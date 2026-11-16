"""
Tests para el adaptador opencode-switch.

Valida el contrato headless JSON (cuentas/cuota/ocupacion/preflight/seleccionar)
leyendo una base de datos SQLite aislada (vía OPENCODE_DB) y un ejecutable
'opencode' simulado, sin tocar la instalación real de OpenCode.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import pytest

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
OPENCODE_CLI = BIN_DIR / "opencode-switch"
SWITCH_CLI = BIN_DIR / "switch"


def _make_fake_db(db_path: Path):
    """Crea una base opencode.db mínima con tablas credential y session_v2."""
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.execute("""CREATE TABLE credential (
        id TEXT PRIMARY KEY,
        integration_id TEXT,
        label TEXT,
        value TEXT,
        connector_id TEXT,
        method_id TEXT,
        active INTEGER,
        time_created INTEGER,
        time_updated INTEGER
    )""")
    cur.execute("""CREATE TABLE session_v2 (
        id TEXT PRIMARY KEY,
        model TEXT,
        cost REAL DEFAULT 0,
        tokens_input INTEGER DEFAULT 0,
        tokens_output INTEGER DEFAULT 0,
        tokens_reasoning INTEGER DEFAULT 0,
        tokens_cache_read INTEGER DEFAULT 0,
        tokens_cache_write INTEGER DEFAULT 0,
        time_created INTEGER DEFAULT 0
    )""")
    cur.execute("INSERT INTO credential VALUES (?,?,?,?,?,?,?,?,?)", (
        "cred_activa", "opencode", "Cuenta Principal", '{"type":"api","key":"sk-activa"}',
        None, "key", 1, 1000, 1000,
    ))
    cur.execute("INSERT INTO credential VALUES (?,?,?,?,?,?,?,?,?)", (
        "cred_secundaria", "opencode", "Cuenta Secundaria", '{"type":"api","key":"sk-sec"}',
        None, "key", 0, 2000, 2000,
    ))
    # Consumo asociado al proveedor "opencode"
    cur.execute("INSERT INTO session_v2 VALUES (?,?,?,?,?,?,?,?,?)", (
        "ses_1", '{"id":"modelo-a","providerID":"opencode"}',
        0.5, 1000, 200, 50, 3000, 0, 100,
    ))
    cur.execute("INSERT INTO session_v2 VALUES (?,?,?,?,?,?,?,?,?)", (
        "ses_2", '{"id":"modelo-b","providerID":"opencode"}',
        0.25, 500, 100, 0, 1000, 0, 200,
    ))
    con.commit()
    con.close()


@pytest.fixture
def isolated_env(tmp_path: Path):
    data_dir = tmp_path / "opencode"
    data_dir.mkdir(parents=True)
    db_path = data_dir / "opencode.db"
    _make_fake_db(db_path)

    mock_bin = tmp_path / "mock_bin"
    mock_bin.mkdir()
    fake_opencode = mock_bin / "opencode"
    fake_opencode.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'opencode v9.9.9-test'; exit 0; fi\n"
        "if [ \"$1\" = \"auth\" ] && [ \"$2\" = \"switch\" ]; then exit 0; fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_opencode.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    env["OPENCODE_DB"] = str(db_path)
    env["PATH"] = f"{mock_bin}:{BIN_DIR}:{env.get('PATH', '')}"
    return {"env": env, "data_dir": data_dir, "db_path": db_path}


def test_opencode_cuentas_json(isolated_env):
    res = subprocess.run(
        [sys.executable, str(OPENCODE_CLI), "cuentas", "--json"],
        env=isolated_env["env"], capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["disponible"] is True
    assert data["perfil_activo"] == "Cuenta Principal"
    aliases = [c["alias"] for c in data["cuentas"]]
    assert "Cuenta Principal" in aliases
    assert "Cuenta Secundaria" in aliases
    activas = [c for c in data["cuentas"] if c["es_activa"]]
    assert len(activas) == 1
    assert activas[0]["alias"] == "Cuenta Principal"


def test_opencode_cuota_json_telemetry(isolated_env):
    res = subprocess.run(
        [sys.executable, str(OPENCODE_CLI), "cuota", "--json"],
        env=isolated_env["env"], capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["proveedor"] == "opencode"
    assert data["cuotas"], "Debe haber al menos una cuenta"

    # El consumo debe reflejar los tokens/coste de la BD aislada.
    tokens = data["cuotas"][0]["tokens"]
    assert "opencode" in tokens
    prov = tokens["opencode"]
    assert prov["input"] == 1500
    assert prov["output"] == 300
    assert prov["reasoning"] == 50
    assert abs(prov["cost"] - 0.75) < 1e-9
    assert set(prov["models"]) == {"modelo-a", "modelo-b"}
    # OpenCode no expone saldo/cuota externa: nunca se inventa.
    assert data["cuotas"][0]["saldo"] is None
    assert data["cuotas"][0]["rate_limit"] is None


class _GoPlusMockHandler(BaseHTTPRequestHandler):
    """Mock de https://opencode.ai/zen/go/v1/usage con la respuesta real observada."""

    def do_GET(self):  # noqa: N802
        assert self.path == "/zen/go/v1/usage"
        assert self.headers.get("Authorization", "").startswith("Bearer oc_sk_")
        body = json.dumps({
            "usage": {
                "rolling": {"status": "ok", "percent": 8, "resetsAt": "2030-01-01T00:00:00.000Z"},
                "weekly": {"status": "ok", "percent": 3, "resetsAt": "2030-01-07T00:00:00.000Z"},
                "monthly": {"status": "ok", "percent": 1, "resetsAt": "2030-02-01T00:00:00.000Z"},
            }
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def test_opencode_go_plus_usage_cuota(isolated_env, tmp_path):
    """La cuota Go Plus (5h/weekly/monthly) debe consultarse a la API de uso y
    reportarse en rate_limit.ventanas, tanto si la key vive en opencode.db como
    si está configurada en el auth.json de Pi."""
    server = HTTPServer(("127.0.0.1", 0), _GoPlusMockHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        env = isolated_env["env"].copy()
        env["OPENCODE_USAGE_URL"] = f"http://127.0.0.1:{port}/zen/go/v1/usage"
        env["HOME"] = str(tmp_path / "no-pi-home")

        # 1. Key en la credencial de opencode.db (fixture usa sk-activa; la
        #    reescribimos con una clave con prefijo oc_sk_ para el caso Go).
        con = sqlite3.connect(str(isolated_env["db_path"]))
        con.execute("UPDATE credential SET value = ? WHERE active = 1",
                    (json.dumps({"type": "api", "key": "oc_sk_test_key_active"}),))
        con.commit()
        con.close()

        res = subprocess.run(
            [sys.executable, str(OPENCODE_CLI), "cuota", "--json"],
            env=env, capture_output=True, text=True,
        )
        assert res.returncode == 0, res.stderr
        data = json.loads(res.stdout)
        q = next(c for c in data["cuotas"] if c["es_activa"])
        ventanas = (q["rate_limit"] or {}).get("ventanas")
        assert ventanas, "rate_limit.ventanas debe contener la cuota Go Plus"
        assert ventanas["5h"]["used_percent"] == 8
        assert ventanas["5h"]["remaining_percent"] == 92
        assert ventanas["weekly"]["used_percent"] == 3
        assert ventanas["monthly"]["used_percent"] == 1
        assert ventanas["5h"]["reset_after_seconds"] > 0

        # 2. Fallback: sin key en opencode.db pero configurada en Pi auth.json.
        pi_dir = tmp_path / "pihome" / ".pi" / "agent"
        pi_dir.mkdir(parents=True)
        (pi_dir / "auth.json").write_text(json.dumps(
            {"opencode-go": {"type": "api_key", "key": "oc_sk_pi_fallback"}}
        ), encoding="utf-8")
        env2 = env.copy()
        env2["PI_CODING_AGENT_DIR"] = str(pi_dir)
        con = sqlite3.connect(str(isolated_env["db_path"]))
        con.execute("UPDATE credential SET value = ?", (json.dumps({"type": "oauth", "access": "x"}),))
        con.commit()
        con.close()
        res2 = subprocess.run(
            [sys.executable, str(OPENCODE_CLI), "cuota", "--json"],
            env=env2, capture_output=True, text=True,
        )
        data2 = json.loads(res2.stdout)
        q2 = next(c for c in data2["cuotas"] if c["es_activa"])
        assert (q2["rate_limit"] or {}).get("ventanas", {}).get("weekly", {}).get("used_percent") == 3
    finally:
        server.shutdown()
        con = sqlite3.connect(str(isolated_env["db_path"]))
        con.execute("UPDATE credential SET value = ? WHERE id = 'cred_activa'",
                    (json.dumps({"type": "api", "key": "sk-activa"}),))
        con.execute("UPDATE credential SET value = ? WHERE id = 'cred_secundaria'",
                    (json.dumps({"type": "api", "key": "sk-sec"}),))
        con.commit()
        con.close()


def test_opencode_sin_cuentas_no_disponible(tmp_path: Path):
    """Sin ninguna cuenta configurada en la BD, el proveedor no debe reportarse disponible."""
    data_dir = tmp_path / "opencode"
    data_dir.mkdir()
    db_path = data_dir / "opencode.db"
    con = sqlite3.connect(str(db_path))
    con.execute("CREATE TABLE credential (id TEXT PRIMARY KEY, integration_id TEXT, label TEXT, value TEXT, connector_id TEXT, method_id TEXT, active INTEGER, time_created INTEGER, time_updated INTEGER)")
    con.execute("CREATE TABLE session_v2 (id TEXT PRIMARY KEY, model TEXT, cost REAL, tokens_input INTEGER, tokens_output INTEGER, tokens_reasoning INTEGER, tokens_cache_read INTEGER, tokens_cache_write INTEGER, time_created INTEGER)")
    con.commit()
    con.close()

    env = os.environ.copy()
    env["HOME"] = str(tmp_path / "home")
    env["OPENCODE_DB"] = str(db_path)
    env["PATH"] = f"{BIN_DIR}:{env.get('PATH', '')}"

    res = subprocess.run(
        [sys.executable, str(OPENCODE_CLI), "cuentas", "--json"],
        env=env, capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["disponible"] is False
    assert data["cuentas"] == []

    # En la suite unificada tampoco debe aparecer como disponible.
    res = subprocess.run(
        [sys.executable, str(SWITCH_CLI), "cuentas", "opencode", "--json"],
        env=env, capture_output=True, text=True,
    )
    data = json.loads(res.stdout)
    assert data["proveedores"]["opencode"]["disponible"] is False


def test_opencode_preflight_json(isolated_env):
    res = subprocess.run(
        [sys.executable, str(OPENCODE_CLI), "preflight", "--json"],
        env=isolated_env["env"], capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["proveedor"] == "opencode"
    assert data["capabilities"]["active_session_detection"] is True
    assert data["capabilities"]["local_token_telemetry"] is True
    # OpenCode no implementa ejecución paralela aislada en esta iteración.
    assert data["capabilities"]["parallel"] is False


def test_opencode_seleccionar_cuenta_inexistente(isolated_env):
    res = subprocess.run(
        [sys.executable, str(OPENCODE_CLI), "seleccionar", "no_existe", "--json"],
        env=isolated_env["env"], capture_output=True, text=True,
    )
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["permitido"] is False
    assert data["codigo"] == "invalid_auth"


def test_opencode_seleccionar_dry_run(isolated_env):
    res = subprocess.run(
        [sys.executable, str(OPENCODE_CLI), "seleccionar", "Cuenta Principal", "--json", "--dry-run"],
        env=isolated_env["env"], capture_output=True, text=True,
    )
    data = json.loads(res.stdout)
    # El dry-run debe ser permitido o, si el entorno tiene procesos 'opencode'
    # reales, rechazado por 'active_session'; nunca debe ser 'invalid_auth'.
    assert data["codigo"] in ("ok", "active_session")


def test_switch_cuentas_opencode_json(isolated_env):
    res = subprocess.run(
        [sys.executable, str(SWITCH_CLI), "cuentas", "opencode", "--json"],
        env=isolated_env["env"], capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert "opencode" in data["proveedores"]
    oc = data["proveedores"]["opencode"]
    assert oc["disponible"] is True
    aliases = [c["alias"] for c in oc["cuentas"]]
    assert "Cuenta Principal" in aliases


def test_switch_preflight_opencode_soportado(isolated_env):
    res = subprocess.run(
        [sys.executable, str(SWITCH_CLI), "preflight", "--json"],
        env=isolated_env["env"], capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["proveedores"]["opencode"]["soportado"] is True
