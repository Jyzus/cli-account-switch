"""
Tests para el adaptador pi-switch (Pi Coding Agent).

Valida el contrato headless JSON (cuentas/cuota/ocupacion/seleccionar/preflight),
la conmutación atómica con marcador .active_profile, la sincronización
bidireccional y el aislamiento de ejecución paralela vía PI_CODING_AGENT_DIR,
todo en un entorno aislado (HOME y PI_CODING_AGENT_DIR temporales) sin tocar
la instalación real de Pi.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
PI_CLI = BIN_DIR / "pi-switch"
SWITCH_CLI = BIN_DIR / "switch"


def _auth_a() -> dict:
    return {
        "anthropic": {"type": "api_key", "key": "sk-ant-AAAA-secret-111111"},
        "opencode-go": {"type": "api_key", "key": "oc_sk_BBBB_secret_222222"},
    }


def _auth_b() -> dict:
    return {
        "openai": {"type": "api_key", "key": "sk-proj-CCCC-secret-333333"},
    }


@pytest.fixture
def isolated_env(tmp_path: Path):
    """Crea un directorio de agente de Pi aislado con dos cuentas guardadas."""
    home = tmp_path / "home"
    pi_dir = home / ".pi" / "agent"
    cuentas = pi_dir / "cuentas"
    cuentas.mkdir(parents=True)

    (cuentas / "personal.json").write_text(json.dumps(_auth_a()), encoding="utf-8")
    (cuentas / "trabajo.json").write_text(json.dumps(_auth_b()), encoding="utf-8")
    (pi_dir / "auth.json").write_text(json.dumps(_auth_a()), encoding="utf-8")
    (pi_dir / ".active_profile").write_text("personal\n", encoding="utf-8")

    # Registro de sesión con consumo simulado (telemetría local).
    sessions = pi_dir / "sessions" / "--proj--"
    sessions.mkdir(parents=True)
    (sessions / "s1.jsonl").write_text(
        json.dumps({"type": "message", "message": {
            "role": "assistant", "provider": "anthropic", "model": "claude-x",
            "usage": {"input": 100, "output": 40, "cacheRead": 10, "cacheWrite": 5,
                      "totalTokens": 155, "cost": {"total": 0.25}},
        }}) + "\n",
        encoding="utf-8",
    )

    # Binario 'pi' simulado para flujo de login/paralelo.
    mock_bin = tmp_path / "mock_bin"
    mock_bin.mkdir()
    fake_pi = mock_bin / "pi"
    fake_pi.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'pi 9.9.9-test'; exit 0; fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_pi.chmod(0o755)

    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PI_CODING_AGENT_DIR"] = str(pi_dir)
    env["PATH"] = f"{mock_bin}:{BIN_DIR}:{env.get('PATH', '')}"
    return {
        "env": env,
        "pi_dir": pi_dir,
        "cuentas": cuentas,
        "mock_bin": mock_bin,
    }


def run_pi(env, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PI_CLI)] + list(args),
        env=env, capture_output=True, text=True,
    )


def test_pi_preflight_json(isolated_env):
    res = run_pi(isolated_env["env"], "preflight", "--json")
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["proveedor"] == "pi"
    assert data["protocol_version"] == 1
    assert data["capabilities"]["parallel"] is True
    assert data["capabilities"]["active_session_detection"] is True
    assert data["capabilities"]["local_token_telemetry"] is True
    # Pi no expone API externa de saldo/cuota.
    assert data["capabilities"]["external_quota_api"] is False


def test_pi_cuentas_json(isolated_env):
    res = run_pi(isolated_env["env"], "cuentas", "--json")
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["disponible"] is True
    assert data["perfil_activo"] == "personal"
    aliases = {c["alias"] for c in data["cuentas"]}
    assert {"personal", "trabajo"} <= aliases
    activas = [c for c in data["cuentas"] if c["es_activa"]]
    assert len(activas) == 1 and activas[0]["alias"] == "personal"
    # Nunca deben filtrarse secretos en claro.
    assert "secret" not in res.stdout
    # Identidad opaca estable y no vacía.
    personal = next(c for c in data["cuentas"] if c["alias"] == "personal")
    assert personal["identidad_opaca"]


def test_pi_cuentas_json_sin_credenciales_no_disponible(tmp_path: Path):
    """Un proveedor sin ninguna cuenta configurada NO debe reportarse disponible."""
    home = tmp_path / "home"
    pi_dir = home / ".pi" / "agent"
    (pi_dir / "cuentas").mkdir(parents=True)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PI_CODING_AGENT_DIR"] = str(pi_dir)
    res = run_pi(env, "cuentas", "--json")
    data = json.loads(res.stdout)
    assert data["disponible"] is False
    assert data["cuentas"] == []


def test_pi_cuota_json_telemetría_local(isolated_env):
    res = run_pi(isolated_env["env"], "cuota", "--json")
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["proveedor"] == "pi"
    assert data["cuotas"], "Debe haber al menos una cuenta"
    q = data["cuotas"][0]
    # El consumo se lee de las sesiones locales.
    tokens = q["tokens"]
    assert "anthropic" in tokens
    assert tokens["anthropic"]["input"] == 100
    assert tokens["anthropic"]["output"] == 40
    assert abs(tokens["anthropic"]["cost"] - 0.25) < 1e-9
    # Nunca se inventa saldo ni rate limit externo.
    assert q["saldo"] is None
    assert q["rate_limit"] is None


def test_pi_seleccionar_y_conmutacion(isolated_env):
    env = isolated_env["env"]
    res = run_pi(env, "seleccionar", "trabajo", "--json", "--force")
    assert res.returncode == 0, res.stdout + res.stderr
    data = json.loads(res.stdout)
    assert data["permitido"] is True
    assert data["codigo"] == "ok"
    assert data["cambio_realizado"] is True

    # El auth.json activo debe ser ahora el de 'trabajo' y el marcador también.
    auth = json.loads((isolated_env["pi_dir"] / "auth.json").read_text(encoding="utf-8"))
    assert "openai" in auth and "anthropic" not in auth
    marker = isolated_env["pi_dir"] / ".active_profile"
    assert marker.read_text(encoding="utf-8").strip() == "trabajo"


def test_pi_seleccionar_cuenta_inexistente(isolated_env):
    res = run_pi(isolated_env["env"], "seleccionar", "no_existe", "--json")
    assert res.returncode == 1
    data = json.loads(res.stdout)
    assert data["permitido"] is False
    assert data["codigo"] == "invalid_auth"


def test_pi_guardar_y_sincronizacion_bidireccional(isolated_env):
    env = isolated_env["env"]
    pi_dir = isolated_env["pi_dir"]

    # Login nativo simulado refresca el token en vuelo del proveedor activo.
    auth_path = pi_dir / "auth.json"
    refreshed = _auth_a()
    refreshed["anthropic"]["key"] = "sk-ant-REFRESCADO-999999"
    auth_path.write_text(json.dumps(refreshed), encoding="utf-8")

    # Cualquier lectura del contrato debe sincronizar el perfil guardado saliente.
    res = run_pi(env, "cuentas", "--json")
    assert res.returncode == 0
    persistido = json.loads((isolated_env["cuentas"] / "personal.json").read_text(encoding="utf-8"))
    assert persistido["anthropic"]["key"] == "sk-ant-REFRESCADO-999999"


def test_pi_paralelo_aislado(isolated_env):
    """'paralelo' debe ejecutar con PI_CODING_AGENT_DIR temporal sin tocar el global."""
    env = isolated_env["env"]
    before = (isolated_env["pi_dir"] / "auth.json").read_bytes()

    probe = (
        "import json,os;"
        "d=os.environ['PI_CODING_AGENT_DIR'];"
        "auth=json.load(open(os.path.join(d,'auth.json')));"
        "print('PAR_OK', os.environ.get('SWITCH_PARALLEL_ALIAS'), sorted(auth.keys()))"
    )
    res = subprocess.run(
        [sys.executable, str(PI_CLI), "paralelo", "trabajo", "--", sys.executable, "-c", probe],
        env=env, capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    assert "PAR_OK trabajo ['openai']" in res.stdout
    # El auth.json global intacto.
    assert (isolated_env["pi_dir"] / "auth.json").read_bytes() == before


def test_pi_switch_preflight_soportado(isolated_env):
    """`switch preflight --json` debe reportar pi como proveedor soportado."""
    res = subprocess.run(
        [sys.executable, str(SWITCH_CLI), "preflight", "--json"],
        env=isolated_env["env"], capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["proveedores"]["pi"]["soportado"] is True
    assert data["capabilities"]["parallel_pi"] is True


def test_pi_switch_cuentas_y_seleccionar_unificado(isolated_env):
    env = isolated_env["env"]
    res = subprocess.run(
        [sys.executable, str(SWITCH_CLI), "cuentas", "pi", "--json"],
        env=env, capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert "pi" in data["proveedores"]
    assert data["proveedores"]["pi"]["disponible"] is True

    res = subprocess.run(
        [sys.executable, str(SWITCH_CLI), "seleccionar", "pi", "trabajo", "--json"],
        env=env, capture_output=True, text=True,
    )
    data = json.loads(res.stdout)
    # Permitido (sin sesiones pi) o bloqueado por sesión activa real; nunca invalid.
    assert data["codigo"] in ("ok", "active_session")


def test_pi_ocultar_proveedor_sin_cuentas_en_switch(tmp_path: Path):
    """`switch cuentas --json` debe marcar disponible=false si no hay cuentas en disco."""
    home = tmp_path / "home"
    pi_dir = home / ".pi" / "agent"
    (pi_dir / "cuentas").mkdir(parents=True)
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PI_CODING_AGENT_DIR"] = str(pi_dir)
    env["PATH"] = f"{BIN_DIR}:{env.get('PATH', '')}"

    res = subprocess.run(
        [sys.executable, str(SWITCH_CLI), "cuentas", "pi", "--json"],
        env=env, capture_output=True, text=True,
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["proveedores"]["pi"]["disponible"] is False
    assert data["proveedores"]["pi"]["cuentas"] == []
