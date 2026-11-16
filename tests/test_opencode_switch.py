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
