"""
Tests para SPEC-009: Swap & Restore en agy-switch agregar, flexibilización de procesos activos en usar,
y soporte de banderas -y/--yes/--force en CLI unificada switch.
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

    codex_acc1 = {
        "OPENAI_API_KEY": "sk-codex-1",
        "tokens": {
            "access_token": "at-codex-1",
            "refresh_token": "rt-codex-1",
            "account_id": "acc-1"
        },
        "email": "codex1@empresa.com",
        "plan_type": "plus"
    }
    (codex_cuentas / "cuenta1.json").write_text(json.dumps(codex_acc1), encoding="utf-8")
    (codex_home / "auth.json").write_text(json.dumps(codex_acc1), encoding="utf-8")
    (codex_cuentas / ".active_profile").write_text("cuenta1\n", encoding="utf-8")

    # AGY dirs
    agy_home = home_dir / ".gemini" / "antigravity-cli"
    agy_cuentas = agy_home / "cuentas"
    agy_cuentas.mkdir(parents=True)

    agy_acc1 = {
        "token": {
            "access_token": "ya29.token-cuenta1",
            "refresh_token": "1//refresh-cuenta1",
            "expires_in": 3600
        },
        "id_token_email": "principal@gmail.com",
        "plan": "Antigravity"
    }
    (agy_cuentas / "cuenta1.token").write_text(json.dumps(agy_acc1), encoding="utf-8")
    (agy_home / "antigravity-oauth-token").write_text(json.dumps(agy_acc1), encoding="utf-8")
    (agy_cuentas / ".active_profile").write_text("cuenta1\n", encoding="utf-8")

    agy_acc2 = {
        "token": {
            "access_token": "ya29.token-cuenta2",
            "refresh_token": "1//refresh-cuenta2",
            "expires_in": 3600
        },
        "id_token_email": "secundaria@gmail.com",
        "plan": "Antigravity"
    }
    (agy_cuentas / "cuenta2.token").write_text(json.dumps(agy_acc2), encoding="utf-8")

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
        "acc1_data": agy_acc1,
        "acc2_data": agy_acc2,
    }


def test_agy_agregar_interactive_swap_and_restore(isolated_env, tmp_path):
    """
    Valida que 'agy-switch agregar <nombre>' use el patrón Swap & Restore:
    1. Ejecute el login capturando las nuevas credenciales.
    2. Guarde la nueva cuenta en cuentas/<nombre>.token.
    3. Restaure de inmediato el token activo previo en disco y el perfil activo.
    """
    mock_bin = tmp_path / "mock_bin"
    mock_bin.mkdir()

    # Mock del binario agy: simula un login OAuth exitoso generando un nuevo token
    nueva_cuenta_data = {
        "token": {
            "access_token": "ya29.NUEVO-TOKEN-SWAP",
            "refresh_token": "1//refresh-nuevo-swap",
            "expires_in": 3600
        },
        "id_token_email": "tercera.cuenta@gmail.com",
        "plan": "Antigravity"
    }
    mock_agy = mock_bin / "agy"
    mock_agy.write_text(f"""#!/bin/sh
cat << 'EOF' > "{isolated_env['agy_home']}/antigravity-oauth-token"
{json.dumps(nueva_cuenta_data)}
EOF
exit 0
""", encoding="utf-8")
    mock_agy.chmod(0o755)

    env = isolated_env["env"].copy()
    env["PATH"] = f"{mock_bin}:{env['PATH']}"

    # Ejecutar 'agy-switch agregar cuenta3'
    res = subprocess.run([sys.executable, str(AGY_SWITCH_CLI), "agregar", "cuenta3"],
                         env=env, capture_output=True, text=True)
    assert res.returncode == 0, f"Error en agy-switch agregar: stdout={res.stdout}, stderr={res.stderr}"

    # 1. La nueva cuenta debe existir en cuentas/cuenta3.token con el token nuevo
    saved_nueva = json.loads((isolated_env["agy_cuentas"] / "cuenta3.token").read_text(encoding="utf-8"))
    assert saved_nueva["token"]["access_token"] == "ya29.NUEVO-TOKEN-SWAP"
    assert saved_nueva["id_token_email"] == "tercera.cuenta@gmail.com"

    # 2. El token activo en disco (antigravity-oauth-token) DEBE HABERSE RESTAURADO a cuenta1
    active_token = json.loads((isolated_env["agy_home"] / "antigravity-oauth-token").read_text(encoding="utf-8"))
    assert active_token["token"]["access_token"] == "ya29.token-cuenta1", "El token activo fue sobreescrito y no se restauró"
    assert active_token["id_token_email"] == "principal@gmail.com"

    # 3. El perfil activo debe seguir siendo cuenta1
    active_marker = (isolated_env["agy_cuentas"] / ".active_profile").read_text(encoding="utf-8").strip()
    assert active_marker == "cuenta1"


def test_agy_agregar_desde_archivo_y_json(isolated_env, tmp_path):
    """Valida importación con --desde tanto de archivo como de JSON directo sin abrir agy."""
    # Archivo
    import_file = tmp_path / "token_importado.json"
    imported_data = {
        "token": {
            "access_token": "ya29.TOKEN-IMPORTADO-FILE",
            "refresh_token": "1//refresh-file",
            "expires_in": 3600
        },
        "id_token_email": "importado.file@gmail.com",
        "plan": "Antigravity"
    }
    import_file.write_text(json.dumps(imported_data), encoding="utf-8")

    res = subprocess.run([sys.executable, str(AGY_SWITCH_CLI), "agregar", "importada_file", "--desde", str(import_file)],
                         env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0

    saved_file = json.loads((isolated_env["agy_cuentas"] / "importada_file.token").read_text(encoding="utf-8"))
    assert saved_file["token"]["access_token"] == "ya29.TOKEN-IMPORTADO-FILE"

    # JSON directo vía switch unificado
    json_str = json.dumps({
        "token": {
            "access_token": "ya29.TOKEN-IMPORTADO-JSON",
            "refresh_token": "1//refresh-json",
            "expires_in": 3600
        },
        "id_token_email": "importado.json@gmail.com",
        "plan": "Antigravity"
    })
    res_unified = subprocess.run([sys.executable, str(SWITCH_CLI), "agy", "agregar", "importada_json", "--desde", json_str],
                                 env=isolated_env["env"], capture_output=True, text=True)
    assert res_unified.returncode == 0

    saved_json = json.loads((isolated_env["agy_cuentas"] / "importada_json.token").read_text(encoding="utf-8"))
    assert saved_json["token"]["access_token"] == "ya29.TOKEN-IMPORTADO-JSON"

    # Sesión activa intacta
    active_token = json.loads((isolated_env["agy_home"] / "antigravity-oauth-token").read_text(encoding="utf-8"))
    assert active_token["token"]["access_token"] == "ya29.token-cuenta1"


def test_agy_usar_with_force_and_y_flags(isolated_env):
    """Valida conmutación con flags --force, -f, -y, --yes en agy-switch y switch unificado."""
    # 1. Conmutar a cuenta2 con -y en switch unificado (auto-detecta AGY porque solo existe en AGY)
    res1 = subprocess.run([sys.executable, str(SWITCH_CLI), "usar", "cuenta2", "-y"],
                          env=isolated_env["env"], capture_output=True, text=True)
    assert res1.returncode == 0
    active1 = json.loads((isolated_env["agy_home"] / "antigravity-oauth-token").read_text(encoding="utf-8"))
    assert active1["token"]["access_token"] == "ya29.token-cuenta2"
    assert (isolated_env["agy_cuentas"] / ".active_profile").read_text(encoding="utf-8").strip() == "cuenta2"

    # 2. Conmutar de regreso a cuenta1 con --yes en switch agy
    res2 = subprocess.run([sys.executable, str(SWITCH_CLI), "agy", "usar", "cuenta1", "--yes"],
                          env=isolated_env["env"], capture_output=True, text=True)
    assert res2.returncode == 0
    active2 = json.loads((isolated_env["agy_home"] / "antigravity-oauth-token").read_text(encoding="utf-8"))
    assert active2["token"]["access_token"] == "ya29.token-cuenta1"
    assert (isolated_env["agy_cuentas"] / ".active_profile").read_text(encoding="utf-8").strip() == "cuenta1"

    # 3. Conmutar con agy-switch usar cuenta2 --force
    res3 = subprocess.run([sys.executable, str(AGY_SWITCH_CLI), "usar", "cuenta2", "--force"],
                          env=isolated_env["env"], capture_output=True, text=True)
    assert res3.returncode == 0
    active3 = json.loads((isolated_env["agy_home"] / "antigravity-oauth-token").read_text(encoding="utf-8"))
    assert active3["token"]["access_token"] == "ya29.token-cuenta2"


def test_switch_status_and_listar_with_added_profiles(isolated_env):
    """Valida que 'switch listar' y 'switch status' reconozcan todos los perfiles de forma robusta."""
    res_list = subprocess.run([sys.executable, str(SWITCH_CLI), "listar"],
                              env=isolated_env["env"], capture_output=True, text=True)
    assert res_list.returncode == 0
    assert "cuenta1" in res_list.stdout
    assert "cuenta2" in res_list.stdout

    res_cuentas_json = subprocess.run([sys.executable, str(SWITCH_CLI), "cuentas", "--json"],
                                      env=isolated_env["env"], capture_output=True, text=True)
    assert res_cuentas_json.returncode == 0
    data = json.loads(res_cuentas_json.stdout)
    assert "agy" in data["proveedores"]
    agy_aliases = [c["alias"] for c in data["proveedores"]["agy"]["cuentas"]]
    assert "cuenta1" in agy_aliases
    assert "cuenta2" in agy_aliases
