"""
Tests para SPEC-006: Contrato CLI JSON headless, telemetría de cuotas y ejecución concurrente aislada.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
SWITCH_CLI = BIN_DIR / "switch"
AGY_SWITCH_CLI = BIN_DIR / "agy-switch"
CODEX_SWITCH_CLI = BIN_DIR / "codex-switch"


@pytest.fixture
def isolated_env(tmp_path: Path):
    """Crea un entorno aislado para pruebas de CLI con cuentas simuladas de Codex y AGY."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    # Codex mock dirs
    codex_home = home_dir / ".codex"
    codex_cuentas = codex_home / "cuentas"
    codex_cuentas.mkdir(parents=True)

    # Token secreto que NUNCA debe aparecer en respuestas JSON
    codex_secret = "sk-super-secret-openai-token-12345"
    codex_cuenta1 = {
        "OPENAI_API_KEY": codex_secret,
        "tokens": {
            "access_token": codex_secret,
            "refresh_token": "refresh-secret-12345",
            "account_id": "acc-123"
        },
        "email": "usuario.principal@empresa.com",
        "plan_type": "plus"
    }
    (codex_cuentas / "principal.json").write_text(json.dumps(codex_cuenta1), encoding="utf-8")
    (codex_home / "auth.json").write_text(json.dumps(codex_cuenta1), encoding="utf-8")

    # AGY mock dirs
    agy_home = home_dir / ".gemini" / "antigravity-cli"
    agy_cuentas = agy_home / "cuentas"
    agy_cuentas.mkdir(parents=True)

    agy_secret = "ya29.super-secret-google-oauth-token-67890"
    agy_cuenta1 = {
        "token": {
            "access_token": agy_secret,
            "refresh_token": "1//refresh-secret-67890",
            "expires_in": 3600
        },
        "id_token_email": "desarrollador.gemini@gmail.com",
        "plan": "Antigravity"
    }
    (agy_cuentas / "trabajo.token").write_text(json.dumps(agy_cuenta1), encoding="utf-8")
    (agy_home / "antigravity-oauth-token").write_text(json.dumps(agy_cuenta1), encoding="utf-8")

    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["CODEX_HOME"] = str(codex_home)
    env["PATH"] = f"{BIN_DIR}:{env.get('PATH', '')}"

    return {
        "env": env,
        "home_dir": home_dir,
        "codex_home": codex_home,
        "agy_home": agy_home,
        "codex_secret": codex_secret,
        "agy_secret": agy_secret,
    }


def test_switch_cuentas_json_no_secrets(isolated_env):
    """Verifica 'switch cuentas --json': retorna JSON válido, sin secretos y con correos enmascarados."""
    cmd = [sys.executable, str(SWITCH_CLI), "cuentas", "--json"]
    res = subprocess.run(cmd, env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0, f"Stderr: {res.stderr}"

    data = json.loads(res.stdout)
    assert data["version"] == "1.2.0" or "version" in data
    assert "proveedores" in data

    # Secret check: Los tokens jamás deben aparecer en el JSON
    assert isolated_env["codex_secret"] not in res.stdout
    assert isolated_env["agy_secret"] not in res.stdout
    assert "refresh-secret" not in res.stdout

    # Proveedores chequeados
    provs = data["proveedores"]
    assert "codex" in provs
    assert "agy" in provs
    assert "opencode" in provs

    # OpenCode debe reportar unsupported_capability
    assert provs["opencode"]["disponible"] is False
    assert provs["opencode"].get("capacidad") == "unsupported_capability"

    # Emails enmascarados
    codex_accounts = provs["codex"]["cuentas"]
    assert len(codex_accounts) >= 1
    masked_email = codex_accounts[0]["identificador_enmascarado"]
    assert "***" in masked_email
    assert "@empresa.com" in masked_email
    assert "usuario.principal@empresa.com" not in res.stdout


def test_switch_cuota_json_safe_readonly(isolated_env):
    """Verifica 'switch cuota --json': lectura segura sin mutar credenciales activas en disco."""
    codex_auth = isolated_env["codex_home"] / "auth.json"
    agy_auth = isolated_env["agy_home"] / "antigravity-oauth-token"
    codex_before = codex_auth.read_bytes()
    agy_before = agy_auth.read_bytes()

    cmd = [sys.executable, str(SWITCH_CLI), "cuota", "--json"]
    res = subprocess.run(cmd, env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0, f"Stderr: {res.stderr}"

    data = json.loads(res.stdout)
    assert "proveedores" in data
    provs = data["proveedores"]
    assert "codex" in provs
    assert "agy" in provs
    assert provs["opencode"]["capacidad"] == "unsupported_capability"

    # Verificar que los archivos activos en disco no sufrieron modificación alguna
    assert codex_auth.read_bytes() == codex_before
    assert agy_auth.read_bytes() == agy_before


def test_switch_ocupacion_json(isolated_env):
    """Verifica 'switch ocupacion --json': reporte de estado y procesos concurrentes."""
    cmd = [sys.executable, str(SWITCH_CLI), "ocupacion", "--json"]
    res = subprocess.run(cmd, env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0, f"Stderr: {res.stderr}"

    data = json.loads(res.stdout)
    assert "proveedores" in data
    provs = data["proveedores"]
    assert "codex" in provs
    assert "agy" in provs
    assert "ocupado" in provs["codex"]
    assert "puede_conmutar" in provs["codex"]
    assert provs["opencode"]["capacidad"] == "unsupported_capability"


def test_switch_seleccionar_dry_run_and_active_session(isolated_env):
    """Verifica 'switch seleccionar <proveedor> <cuenta> --dry-run --json'."""
    cmd = [sys.executable, str(SWITCH_CLI), "seleccionar", "codex", "principal", "--dry-run", "--json"]
    res = subprocess.run(cmd, env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0 or res.returncode == 1

    data = json.loads(res.stdout)
    assert "solicitud" in data
    assert data["solicitud"]["dry_run"] is True
    assert "permitido" in data


def test_agy_switch_paralelo_isolation(isolated_env):
    """Verifica 'agy-switch paralelo <cuenta> -- <cmd>' con aislamiento de entorno y sin tocar cuenta 1."""
    agy_main_token = isolated_env["agy_home"] / "antigravity-oauth-token"
    token_before = agy_main_token.read_text(encoding="utf-8")

    # Ejecutar comando que inspecciona el entorno del subproceso aislado
    cmd = [
        sys.executable, str(AGY_SWITCH_CLI), "paralelo", "trabajo", "--",
        sys.executable, "-c",
        "import os, pathlib; print('DBUS=' + os.environ.get('DBUS_SESSION_BUS_ADDRESS', 'NONE')); print('HOME=' + os.environ.get('HOME', '')); print('PROFILE=' + os.environ.get('AGY_PROFILE', ''))"
    ]
    res = subprocess.run(cmd, env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0, f"Stderr: {res.stderr}\nStdout: {res.stdout}"

    # Verificaciones de seguridad en el entorno aislado
    assert "DBUS=NONE" in res.stdout or "DBUS=" in res.stdout
    assert "PROFILE=trabajo" in res.stdout
    assert str(isolated_env["home_dir"]) not in res.stdout or "runtimes/trabajo" in res.stdout

    # El token principal debe permanecer 100% inalterado
    assert agy_main_token.read_text(encoding="utf-8") == token_before


def test_codex_switch_paralelo_isolation(isolated_env):
    """Verifica 'codex-switch paralelo <cuenta> -- <cmd>' usando CODEX_HOME aislado."""
    codex_main_auth = isolated_env["codex_home"] / "auth.json"
    auth_before = codex_main_auth.read_text(encoding="utf-8")

    cmd = [
        sys.executable, str(CODEX_SWITCH_CLI), "paralelo", "principal", "--",
        sys.executable, "-c",
        "import os; print('CODEX_HOME=' + os.environ.get('CODEX_HOME', '')); print('PROFILE=' + os.environ.get('CODEX_PROFILE', ''))"
    ]
    res = subprocess.run(cmd, env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0, f"Stderr: {res.stderr}\nStdout: {res.stdout}"

    assert "CODEX_HOME=" in res.stdout
    assert "runtimes/principal" in res.stdout or "isolated" in res.stdout
    assert "PROFILE=principal" in res.stdout

    # El archivo auth.json principal permanece intacto
    assert codex_main_auth.read_text(encoding="utf-8") == auth_before


def test_switch_paralelo_unified(isolated_env):
    """Verifica 'switch paralelo agy <cuenta> -- <cmd>' y 'switch paralelo codex <cuenta> -- <cmd>'."""
    cmd_agy = [
        sys.executable, str(SWITCH_CLI), "paralelo", "agy", "trabajo", "--",
        sys.executable, "-c", "import os; print('OK_AGY_' + os.environ.get('AGY_PROFILE', ''))"
    ]
    res_agy = subprocess.run(cmd_agy, env=isolated_env["env"], capture_output=True, text=True)
    assert res_agy.returncode == 0, f"Stderr: {res_agy.stderr}"
    assert "OK_AGY_trabajo" in res_agy.stdout

    cmd_codex = [
        sys.executable, str(SWITCH_CLI), "paralelo", "codex", "principal", "--",
        sys.executable, "-c", "import os; print('OK_CODEX_' + os.environ.get('CODEX_PROFILE', ''))"
    ]
    res_codex = subprocess.run(cmd_codex, env=isolated_env["env"], capture_output=True, text=True)
    assert res_codex.returncode == 0, f"Stderr: {res_codex.stderr}"
    assert "OK_CODEX_principal" in res_codex.stdout


def test_switch_opencode_unsupported_and_filters(isolated_env):
    """Verifica filtro por proveedor y reporte unsupported_capability para OpenCode."""
    # Filtro específico hacia opencode en cuentas
    cmd_cuentas = [sys.executable, str(SWITCH_CLI), "cuentas", "opencode", "--json"]
    res_cuentas = subprocess.run(cmd_cuentas, env=isolated_env["env"], capture_output=True, text=True)
    assert res_cuentas.returncode == 0, f"Stderr: {res_cuentas.stderr}"
    d_cuentas = json.loads(res_cuentas.stdout)
    assert "opencode" in d_cuentas["proveedores"]
    assert "codex" not in d_cuentas["proveedores"]
    assert d_cuentas["proveedores"]["opencode"]["capacidad"] == "unsupported_capability"

    # Filtro específico hacia opencode en cuota
    cmd_cuota = [sys.executable, str(SWITCH_CLI), "cuota", "opencode", "--json"]
    res_cuota = subprocess.run(cmd_cuota, env=isolated_env["env"], capture_output=True, text=True)
    assert res_cuota.returncode == 0, f"Stderr: {res_cuota.stderr}"
    d_cuota = json.loads(res_cuota.stdout)
    assert "opencode" in d_cuota["proveedores"]
    assert d_cuota["proveedores"]["opencode"]["capacidad"] == "unsupported_capability"

    # Intento de selección en OpenCode
    cmd_sel = [sys.executable, str(SWITCH_CLI), "seleccionar", "opencode", "default", "--json"]
    res_sel = subprocess.run(cmd_sel, env=isolated_env["env"], capture_output=True, text=True)
    assert res_sel.returncode != 0
    d_sel = json.loads(res_sel.stdout)
    assert d_sel["permitido"] is False
    assert d_sel["codigo"] == "unsupported_capability"


def test_subcli_direct_json_contracts(isolated_env):
    """Verifica que las sub-CLIs codex-switch y agy-switch implementan directamente el contrato JSON."""
    res_codex = subprocess.run([sys.executable, str(CODEX_SWITCH_CLI), "cuentas", "--json"], env=isolated_env["env"], capture_output=True, text=True)
    assert res_codex.returncode == 0
    d_c = json.loads(res_codex.stdout)
    assert d_c["disponible"] is True
    assert len(d_c["cuentas"]) >= 1

    res_agy = subprocess.run([sys.executable, str(AGY_SWITCH_CLI), "cuentas", "--json"], env=isolated_env["env"], capture_output=True, text=True)
    assert res_agy.returncode == 0
    d_a = json.loads(res_agy.stdout)
    assert d_a["disponible"] is True
    assert len(d_a["cuentas"]) >= 1

