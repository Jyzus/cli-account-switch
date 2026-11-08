"""
Tests para SPEC-008: Auto-sincronización y persistencia de reautenticación en Switch.
Valida que al re-iniciar sesión tras expiración de tokens, las nuevas credenciales
se registren y guarden automáticamente en el perfil correspondiente sin perderse.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
SWITCH_CLI = BIN_DIR / "switch"
AGY_SWITCH_CLI = BIN_DIR / "agy-switch"
CODEX_SWITCH_CLI = BIN_DIR / "codex-switch"


@pytest.fixture
def isolated_env(tmp_path: Path):
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    # Codex dirs
    codex_home = home_dir / ".codex"
    codex_cuentas = codex_home / "cuentas"
    codex_cuentas.mkdir(parents=True)

    # Cuenta 1: Expired
    codex_expired = {
        "OPENAI_API_KEY": "sk-old-expired-token",
        "tokens": {
            "access_token": "at-expired-111",
            "refresh_token": "rt-expired-111",
            "account_id": "acc-111"
        },
        "email": "usuario.vencido@empresa.com",
        "plan_type": "plus"
    }
    (codex_cuentas / "cuenta1.json").write_text(json.dumps(codex_expired), encoding="utf-8")

    # Cuenta 2: Healthy
    codex_healthy = {
        "OPENAI_API_KEY": "sk-healthy-token",
        "tokens": {
            "access_token": "at-healthy-222",
            "refresh_token": "rt-healthy-222",
            "account_id": "acc-222"
        },
        "email": "usuario.saludable@empresa.com",
        "plan_type": "team"
    }
    (codex_cuentas / "cuenta2.json").write_text(json.dumps(codex_healthy), encoding="utf-8")

    # Auth activo inicial = cuenta1
    (codex_home / "auth.json").write_text(json.dumps(codex_expired), encoding="utf-8")

    # AGY dirs
    agy_home = home_dir / ".gemini" / "antigravity-cli"
    agy_cuentas = agy_home / "cuentas"
    agy_cuentas.mkdir(parents=True)

    agy_expired = {
        "token": {
            "access_token": "ya29.expired-token",
            "refresh_token": "1//refresh-expired",
            "expires_in": 3600
        },
        "id_token_email": "vencido.gemini@gmail.com",
        "plan": "Antigravity"
    }
    (agy_cuentas / "cuenta1.token").write_text(json.dumps(agy_expired), encoding="utf-8")
    (agy_home / "antigravity-oauth-token").write_text(json.dumps(agy_expired), encoding="utf-8")

    agy_healthy = {
        "token": {
            "access_token": "ya29.healthy-token",
            "refresh_token": "1//refresh-healthy",
            "expires_in": 3600
        },
        "id_token_email": "saludable.gemini@gmail.com",
        "plan": "Antigravity"
    }
    (agy_cuentas / "cuenta2.token").write_text(json.dumps(agy_healthy), encoding="utf-8")

    env = os.environ.copy()
    env["HOME"] = str(home_dir)
    env["CODEX_HOME"] = str(codex_home)
    env["PATH"] = f"{BIN_DIR}:{env.get('PATH', '')}"

    return {
        "env": env,
        "home_dir": home_dir,
        "codex_home": codex_home,
        "agy_home": agy_home,
        "codex_cuentas": codex_cuentas,
        "agy_cuentas": agy_cuentas,
    }


def test_codex_auto_sync_after_relogin(isolated_env):
    """Verifica que tras conmutar a cuenta1 y hacer login nuevo en Codex, Switch sincronice y guarde las nuevas credenciales."""
    # 1. Seleccionar cuenta1
    res = subprocess.run([sys.executable, str(CODEX_SWITCH_CLI), "usar", "cuenta1", "--force"],
                         env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0

    # 2. Simular que Codex pide login y el usuario inicia sesión (auth.json recibe tokens nuevos)
    fresh_codex = {
        "OPENAI_API_KEY": "sk-FRESH-VALID-TOKEN-999",
        "tokens": {
            "access_token": "at-fresh-999",
            "refresh_token": "rt-fresh-999",
            "account_id": "acc-111"
        },
        "email": "usuario.vencido@empresa.com",
        "plan_type": "plus"
    }
    (isolated_env["codex_home"] / "auth.json").write_text(json.dumps(fresh_codex), encoding="utf-8")

    # 3. Invocar cualquier comando de switch (ej. cuentas --json o listar o status)
    res_list = subprocess.run([sys.executable, str(CODEX_SWITCH_CLI), "cuentas", "--json"],
                              env=isolated_env["env"], capture_output=True, text=True)
    assert res_list.returncode == 0

    # 4. El archivo guardado cuenta1.json DEBE haberse actualizado automáticamente con el token fresco
    saved_cuenta1 = json.loads((isolated_env["codex_cuentas"] / "cuenta1.json").read_text(encoding="utf-8"))
    assert saved_cuenta1["tokens"]["access_token"] == "at-fresh-999", "Las credenciales frescas no se guardaron en cuenta1.json"
    assert saved_cuenta1["OPENAI_API_KEY"] == "sk-FRESH-VALID-TOKEN-999"

    # 5. Si ahora cambiamos a cuenta2 y regresamos a cuenta1, cuenta1 NO debe volver a estar expirada
    subprocess.run([sys.executable, str(CODEX_SWITCH_CLI), "usar", "cuenta2", "--force"],
                   env=isolated_env["env"], capture_output=True, text=True)
    subprocess.run([sys.executable, str(CODEX_SWITCH_CLI), "usar", "cuenta1", "--force"],
                   env=isolated_env["env"], capture_output=True, text=True)

    active_auth = json.loads((isolated_env["codex_home"] / "auth.json").read_text(encoding="utf-8"))
    assert active_auth["tokens"]["access_token"] == "at-fresh-999", "Se restauró el token expirado en lugar del nuevo"


def test_codex_sync_before_switching_away(isolated_env):
    """Verifica que al conmutar a otra cuenta, los tokens actualizados de la cuenta previa se guarden antes de cambiar."""
    # Activar cuenta1
    subprocess.run([sys.executable, str(CODEX_SWITCH_CLI), "usar", "cuenta1", "--force"],
                   env=isolated_env["env"], capture_output=True, text=True)

    # Simular refresco de tokens en auth.json mientras se usaba cuenta1
    refreshed_auth = {
        "OPENAI_API_KEY": "sk-REFRESHED-IN-FLIGHT",
        "tokens": {
            "access_token": "at-refreshed-flight",
            "refresh_token": "rt-refreshed-flight",
            "account_id": "acc-111"
        },
        "email": "usuario.vencido@empresa.com",
        "plan_type": "plus"
    }
    (isolated_env["codex_home"] / "auth.json").write_text(json.dumps(refreshed_auth), encoding="utf-8")

    # Cambiar a cuenta2
    res = subprocess.run([sys.executable, str(CODEX_SWITCH_CLI), "usar", "cuenta2", "--force"],
                         env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0

    # cuenta1.json en disco debe haber recibido el token refrescado ANTES de que auth.json fuera sobreescrito con cuenta2
    cuenta1_saved = json.loads((isolated_env["codex_cuentas"] / "cuenta1.json").read_text(encoding="utf-8"))
    assert cuenta1_saved["tokens"]["access_token"] == "at-refreshed-flight"


def test_agy_auto_sync_after_relogin(isolated_env):
    """Verifica que en AGY, tras reautenticación, el token se guarde automáticamente en el perfil."""
    # 1. Seleccionar cuenta1 en agy
    res = subprocess.run([sys.executable, str(AGY_SWITCH_CLI), "usar", "cuenta1", "--force"],
                         env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0

    # 2. Simular login nuevo en agy que actualiza antigravity-oauth-token
    fresh_agy = {
        "token": {
            "access_token": "ya29.FRESH-AGY-TOKEN-888",
            "refresh_token": "1//refresh-fresh-888",
            "expires_in": 3600
        },
        "id_token_email": "vencido.gemini@gmail.com",
        "plan": "Antigravity"
    }
    (isolated_env["agy_home"] / "antigravity-oauth-token").write_text(json.dumps(fresh_agy), encoding="utf-8")

    # 3. Invocar comando de agy-switch
    subprocess.run([sys.executable, str(AGY_SWITCH_CLI), "cuentas", "--json"],
                   env=isolated_env["env"], capture_output=True, text=True)

    # 4. El archivo cuenta1.token debe haberse actualizado
    saved_token = json.loads((isolated_env["agy_cuentas"] / "cuenta1.token").read_text(encoding="utf-8"))
    assert saved_token["token"]["access_token"] == "ya29.FRESH-AGY-TOKEN-888"

    # 5. Conmutar a cuenta2 y regresar a cuenta1
    subprocess.run([sys.executable, str(AGY_SWITCH_CLI), "usar", "cuenta2", "--force"],
                   env=isolated_env["env"], capture_output=True, text=True)
    subprocess.run([sys.executable, str(AGY_SWITCH_CLI), "usar", "cuenta1", "--force"],
                   env=isolated_env["env"], capture_output=True, text=True)

    active_token = json.loads((isolated_env["agy_home"] / "antigravity-oauth-token").read_text(encoding="utf-8"))
    assert active_token["token"]["access_token"] == "ya29.FRESH-AGY-TOKEN-888"


def test_switch_reautenticar_subcommand_with_mock_login(isolated_env, tmp_path):
    """Verifica que el comando 'switch reautenticar' y 'codex-switch login <alias_existente>' guarden automáticamente el nuevo token."""
    mock_bin = tmp_path / "mock_bin"
    mock_bin.mkdir()

    # Mock codex binary
    mock_codex = mock_bin / "codex"
    mock_codex.write_text(f"""#!/bin/sh
cat << 'EOF' > "{isolated_env['codex_home']}/auth.json"
{{"tokens": {{"access_token": "at-reauth-direct-555", "refresh_token": "rt-555", "account_id": "acc-111"}}, "OPENAI_API_KEY": "sk-direct-555", "email": "mock@test.com"}}
EOF
exit 0
""", encoding="utf-8")
    mock_codex.chmod(0o755)

    env = isolated_env["env"].copy()
    env["PATH"] = f"{mock_bin}:{env['PATH']}"

    # Ejecutar 'switch reautenticar codex cuenta1'
    res = subprocess.run([sys.executable, str(SWITCH_CLI), "reautenticar", "codex", "cuenta1"],
                         env=env, capture_output=True, text=True)
    assert res.returncode == 0, f"Error en switch reautenticar: {res.stderr}"

    # Verificar que cuenta1.json se actualizó con el nuevo token
    saved = json.loads((isolated_env["codex_cuentas"] / "cuenta1.json").read_text(encoding="utf-8"))
    assert saved["tokens"]["access_token"] == "at-reauth-direct-555"

    # Probar que 'codex-switch login cuenta1' redirige a reautenticar si cuenta1 ya existe
    mock_codex.write_text(f"""#!/bin/sh
cat << 'EOF' > "{isolated_env['codex_home']}/auth.json"
{{"tokens": {{"access_token": "at-login-redirect-333", "refresh_token": "rt-333", "account_id": "acc-111"}}, "OPENAI_API_KEY": "sk-redirect-333", "email": "mock@test.com"}}
EOF
exit 0
""", encoding="utf-8")
    mock_codex.chmod(0o755)

    res_login = subprocess.run([sys.executable, str(CODEX_SWITCH_CLI), "login", "cuenta1"],
                               env=env, capture_output=True, text=True)
    assert res_login.returncode == 0

    saved2 = json.loads((isolated_env["codex_cuentas"] / "cuenta1.json").read_text(encoding="utf-8"))
    assert saved2["tokens"]["access_token"] == "at-login-redirect-333"

