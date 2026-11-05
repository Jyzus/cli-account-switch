"""
Tests para SPEC-007: Endurecimiento de concurrencia, exclusión por identidad,
detección de sesiones activas, aislamiento de config.toml y preflight capabilities.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
import pytest

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
SWITCH_CLI = BIN_DIR / "switch"
AGY_SWITCH_CLI = BIN_DIR / "agy-switch"
CODEX_SWITCH_CLI = BIN_DIR / "codex-switch"


@pytest.fixture
def isolated_env(tmp_path: Path):
    """Crea un entorno de prueba con cuentas duplicadas y configuraciones para validar leases y herencia."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    # Codex mock dirs
    codex_home = home_dir / ".codex"
    codex_cuentas = codex_home / "cuentas"
    codex_cuentas.mkdir(parents=True)

    # Configuración original de Codex
    codex_config = codex_home / "config.toml"
    codex_config.write_text('[model]\ndefault = "gpt-5-orig"\n', encoding="utf-8")

    # Skills mock
    codex_skills = codex_home / "skills"
    codex_skills.mkdir(parents=True)
    (codex_skills / "test-skill.md").write_text("# Test Skill", encoding="utf-8")

    # Cuenta principal Codex (Alice)
    alice_email = "alice@example.com"
    codex_cuenta_alice = {
        "OPENAI_API_KEY": "sk-secret-alice-12345",
        "tokens": {
            "access_token": "at-alice-12345",
            "refresh_token": "rt-alice-12345",
            "account_id": "acc-alice"
        },
        "email": alice_email,
        "plan_type": "plus"
    }
    (codex_cuentas / "cuenta1.json").write_text(json.dumps(codex_cuenta_alice), encoding="utf-8")
    (codex_home / "auth.json").write_text(json.dumps(codex_cuenta_alice), encoding="utf-8")

    # Alias duplicado de Codex apuntando a Alice (mismo email)
    (codex_cuentas / "alias_duplicado.json").write_text(json.dumps(codex_cuenta_alice), encoding="utf-8")

    # Cuenta secundaria Codex (Bob - distinta identidad)
    bob_email = "bob@example.com"
    codex_cuenta_bob = {
        "OPENAI_API_KEY": "sk-secret-bob-67890",
        "tokens": {
            "access_token": "at-bob-67890",
            "refresh_token": "rt-bob-67890",
            "account_id": "acc-bob"
        },
        "email": bob_email,
        "plan_type": "team"
    }
    (codex_cuentas / "cuenta2.json").write_text(json.dumps(codex_cuenta_bob), encoding="utf-8")

    # AGY mock dirs
    agy_home = home_dir / ".gemini" / "antigravity-cli"
    agy_cuentas = agy_home / "cuentas"
    agy_cuentas.mkdir(parents=True)

    agy_alice = {
        "token": {
            "access_token": "ya29.alice-token",
            "refresh_token": "1//refresh-alice",
            "expires_in": 3600
        },
        "id_token_email": "alice.agy@gmail.com",
        "plan": "Antigravity"
    }
    (agy_cuentas / "cuenta1.token").write_text(json.dumps(agy_alice), encoding="utf-8")
    (agy_cuentas / "alias_duplicado.token").write_text(json.dumps(agy_alice), encoding="utf-8")
    (agy_home / "antigravity-oauth-token").write_text(json.dumps(agy_alice), encoding="utf-8")

    agy_bob = {
        "token": {
            "access_token": "ya29.bob-token",
            "refresh_token": "1//refresh-bob",
            "expires_in": 3600
        },
        "id_token_email": "bob.agy@gmail.com",
        "plan": "Antigravity"
    }
    (agy_cuentas / "cuenta2.token").write_text(json.dumps(agy_bob), encoding="utf-8")

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


def test_switch_preflight_json(isolated_env):
    """Verifica 'switch preflight --json' con protocol_version: 1 y capabilities inequívocas."""
    cmd = [sys.executable, str(SWITCH_CLI), "preflight", "--json"]
    res = subprocess.run(cmd, env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0, f"Stderr: {res.stderr}"

    data = json.loads(res.stdout)
    assert data["protocol_version"] == 1
    assert "version" in data
    assert "capabilities" in data
    caps = data["capabilities"]

    # Flags inequívocos requeridos por Planifier
    assert caps.get("parallel_codex") is True
    assert caps.get("parallel_agy") is True
    assert caps.get("identity_reservation") is True
    assert caps.get("active_session_detection") is True
    assert caps.get("refresh_persistence_errors") is True

    # Proveedores y OpenCode como no implementado
    provs = data["proveedores"]
    assert provs["codex"]["soportado"] is True
    assert provs["agy"]["soportado"] is True
    assert provs["opencode"]["soportado"] is False
    assert provs["opencode"]["razon"] == "adaptador_no_implementado"


def test_cuentas_identidad_opaca(isolated_env):
    """Verifica que 'switch cuentas --json' devuelva identidad_opaca idéntica para alias duplicados."""
    cmd = [sys.executable, str(SWITCH_CLI), "cuentas", "--json"]
    res = subprocess.run(cmd, env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0, f"Stderr: {res.stderr}"

    data = json.loads(res.stdout)
    codex_cuentas = data["proveedores"]["codex"]["cuentas"]
    
    # Mapear por alias
    by_alias = {c["alias"]: c for c in codex_cuentas}
    assert "cuenta1" in by_alias
    assert "alias_duplicado" in by_alias
    assert "cuenta2" in by_alias

    id_cuenta1 = by_alias["cuenta1"]["identidad_opaca"]
    id_duplicado = by_alias["alias_duplicado"]["identidad_opaca"]
    id_cuenta2 = by_alias["cuenta2"]["identidad_opaca"]

    # Cuentas con misma identidad real deben tener EXACTAMENTE la misma identidad_opaca
    assert id_cuenta1 != ""
    assert id_cuenta1 == id_duplicado
    # Cuenta con diferente identidad debe tener distinta identidad_opaca
    assert id_cuenta1 != id_cuenta2


def test_paralelo_same_alias_lease_lock(isolated_env):
    """Verifica que dos procesos paralelos con el mismo alias se rechacen mediante lease atómico."""
    script_hold = "import time; time.sleep(1.5)"
    cmd1 = [sys.executable, str(SWITCH_CLI), "paralelo", "codex", "cuenta1", "--", sys.executable, "-c", script_hold]
    p1 = subprocess.Popen(cmd1, env=isolated_env["env"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Dar tiempo a p1 para adquirir el lock
    time.sleep(0.3)

    # p2 intenta ejecutar en paralelo con el MISMO alias mientras p1 sigue corriendo
    cmd2 = [sys.executable, str(SWITCH_CLI), "paralelo", "codex", "cuenta1", "--", sys.executable, "-c", "print('should_not_run')"]
    res2 = subprocess.run(cmd2, env=isolated_env["env"], capture_output=True, text=True)

    # Debe fallar inmediatamente
    assert res2.returncode != 0
    assert "alias_lease_busy" in res2.stderr or "alias_lease_busy" in res2.stdout or "lease" in res2.stderr.lower()

    stdout1, stderr1 = p1.communicate(timeout=5)
    assert p1.returncode == 0


def test_paralelo_identity_collision_lock(isolated_env):
    """Verifica que dos procesos con alias distintos pero misma identidad real se bloqueen mutuamente."""
    script_hold = "import time; time.sleep(1.5)"
    # p1 usa cuenta1
    cmd1 = [sys.executable, str(SWITCH_CLI), "paralelo", "codex", "cuenta1", "--", sys.executable, "-c", script_hold]
    p1 = subprocess.Popen(cmd1, env=isolated_env["env"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(0.3)

    # p2 intenta ejecutar en paralelo usando alias_duplicado (misma identidad real que cuenta1)
    cmd2 = [sys.executable, str(SWITCH_CLI), "paralelo", "codex", "alias_duplicado", "--", sys.executable, "-c", "print('collision')"]
    res2 = subprocess.run(cmd2, env=isolated_env["env"], capture_output=True, text=True)

    # Debe fallar por identity_collision
    assert res2.returncode != 0
    assert "identity_collision" in res2.stderr or "identity_collision" in res2.stdout or "identidad" in res2.stderr.lower()

    p1.communicate(timeout=5)
    assert p1.returncode == 0


def test_codex_paralelo_config_toml_defensive_copy(isolated_env):
    """Verifica que el runtime de Codex copie config.toml defensivamente sin modificar el archivo host."""
    host_config = isolated_env["codex_home"] / "config.toml"
    orig_content = host_config.read_text(encoding="utf-8")

    # Script que muta config.toml dentro del entorno aislado
    script_mutate = (
        "import os\n"
        "from pathlib import Path\n"
        "codex_home = Path(os.environ['CODEX_HOME'])\n"
        "cfg = codex_home / 'config.toml'\n"
        "assert cfg.exists(), 'config.toml no fue heredado'\n"
        "with open(cfg, 'a') as f:\n"
        "    f.write('\\nmutated = true\\n')\n"
    )

    cmd = [sys.executable, str(SWITCH_CLI), "paralelo", "codex", "cuenta1", "--", sys.executable, "-c", script_mutate]
    res = subprocess.run(cmd, env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0, f"Stderr: {res.stderr}"

    # El host config.toml NO debe haber cambiado en lo absoluto
    assert host_config.read_text(encoding="utf-8") == orig_content


def test_paralelo_refresh_persistence_error_observable(isolated_env):
    """Verifica que un fallo al persistir el token refrescado no se silencie y genere respaldo de recuperación."""
    # Script que simula un refresco de token exitoso dentro del worker aislado,
    # y corrompe el destino para inducir fallo I/O en sync_back (incluso ejecutándose como root).
    script_refresh = (
        "import os, json, shutil\n"
        "from pathlib import Path\n"
        "codex_home = Path(os.environ['CODEX_HOME'])\n"
        "auth_f = codex_home / 'auth.json'\n"
        "data = json.loads(auth_f.read_text())\n"
        "data['tokens']['refresh_token'] = 'NEW_REFRESHED_TOKEN_999'\n"
        "auth_f.write_text(json.dumps(data))\n"
        "orig = Path(os.environ['HOME']) / '.codex' / 'cuentas' / 'cuenta1.json'\n"
        "orig.unlink()\n"
        "orig.mkdir()\n"
    )

    cmd = [sys.executable, str(SWITCH_CLI), "paralelo", "codex", "cuenta1", "--", sys.executable, "-c", script_refresh]
    res = subprocess.run(cmd, env=isolated_env["env"], capture_output=True, text=True)

    # Debe fallar con código no cero (¡no silenciar con pass!)
    assert res.returncode != 0
    assert "refresh" in res.stderr.lower() or "recovery" in res.stderr.lower() or "error" in res.stderr.lower()

    # Verificar que se creó archivo de recovery en runtimes con el token refrescado
    runtimes_dir = isolated_env["codex_home"] / "runtimes"
    recovery_files = list(runtimes_dir.glob("recovery*"))
    assert len(recovery_files) > 0, f"No se encontró archivo de recuperación. Archivos en runtimes: {list(runtimes_dir.iterdir())}"
    content = recovery_files[0].read_text(encoding="utf-8")
    assert "NEW_REFRESHED_TOKEN_999" in content
