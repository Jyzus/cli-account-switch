#!/usr/bin/env python3
"""
Plantilla Base para Nuevos Proveedores de Switch (v1.2.0+)
=========================================================
Usa esta plantilla para crear un nuevo adaptador 'bin/<proveedor>-switch'.
Completa las secciones marcadas con [TODO: ESPECÍFICO DEL PROVEEDOR].

Requisitos del proyecto:
- Python 3.9+ usando EXCLUSIVAMENTE la biblioteca estándar (sin dependencias externas).
- Permisos seguros: directorios 0700, archivos de credenciales 0600.
- Soporte dual: comandos humanos y comandos headless con salida JSON (--json).
- Registro persistente del perfil activo en '.active_profile'.
- Auto-sincronización bidireccional tras refresco o reautenticación de tokens.
"""

from __future__ import annotations

import os
import sys
import json
import shutil
import hashlib
import subprocess
import time
import fcntl
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ==============================================================================
# 1. CONFIGURACIÓN DEL PROVEEDOR
# ==============================================================================

# [TODO: ESPECÍFICO DEL PROVEEDOR]
PROVIDER_ID = "nuevo_proveedor"       # Identificador corto en minúsculas (ej: deepseek, opencode)
PROVIDER_NAME = "Nuevo Proveedor"    # Nombre legible (ej: DeepSeek, OpenCode)
VERSION = "1.2.0"

def get_base_dir() -> Path:
    """
    [TODO: ESPECÍFICO DEL PROVEEDOR]
    Retorna el directorio de configuración donde la herramienta original almacena sus datos.
    Ejemplos:
      - DeepSeek: Path(os.environ.get("DEEPSEEK_HOME", Path.home() / ".deepseek"))
      - OpenCode: Path(os.environ.get("OPENCODE_DIR", Path.home() / ".config" / "opencode"))
    """
    env_override = os.environ.get(f"{PROVIDER_ID.upper()}_HOME")
    if env_override:
        return Path(env_override)
    return Path.home() / f".{PROVIDER_ID}"


def get_cuentas_dir() -> Path:
    """Directorio donde Switch almacena los perfiles guardados del proveedor."""
    d = get_base_dir() / "cuentas"
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except Exception:
        pass
    return d


def get_auth_path(auto_sync: bool = True) -> Path:
    """
    [TODO: ESPECÍFICO DEL PROVEEDOR]
    Retorna la ruta al archivo de credenciales/autenticación activo que lee la herramienta original.
    Ejemplos:
      - auth.json
      - config.json
      - credentials.token
    """
    if auto_sync:
        sync_active_profile()
    return get_base_dir() / "auth.json"


def get_active_profile_marker() -> Path:
    """Ruta al archivo que registra qué perfil guardado está activo actualmente."""
    return get_base_dir() / ".active_profile"


def get_locks_dir() -> Path:
    """Directorio para bloqueos (leases) de concurrencia y conmutación atómica."""
    d = get_base_dir() / ".locks"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ==============================================================================
# 2. GESTIÓN DEL PERFIL ACTIVO Y PERSISTENCIA SEGURA
# ==============================================================================

def get_recorded_active_profile() -> str:
    marker = get_active_profile_marker()
    if marker.is_file():
        try:
            val = marker.read_text(encoding="utf-8").strip()
            if val and (get_cuentas_dir() / f"{val}.json").is_file():
                return val
        except Exception:
            pass
    return ""


def set_recorded_active_profile(nombre: str):
    marker = get_active_profile_marker()
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(nombre.strip() + "\n", encoding="utf-8")
        os.chmod(marker, 0o600)
    except Exception:
        pass


def clear_recorded_active_profile():
    marker = get_active_profile_marker()
    if marker.is_file():
        try:
            marker.unlink()
        except Exception:
            pass


def private_copy(src: Path, dst: Path):
    """Copia atómica preservando permisos restrictivos 0600."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    temp_dst = dst.with_name(f"{dst.name}.tmp.{os.getpid()}")
    shutil.copyfile(src, temp_dst)
    try:
        os.chmod(temp_dst, 0o600)
    except Exception:
        pass
    os.replace(temp_dst, dst)


def sync_active_profile():
    """
    Sincroniza automáticamente las credenciales activas en disco con el perfil
    guardado si el token se ha renovado o el usuario se ha reautenticado.
    """
    marker = get_active_profile_marker()
    if not marker.is_file():
        return
    nombre = ""
    try:
        nombre = marker.read_text(encoding="utf-8").strip()
    except Exception:
        return
    if not nombre:
        return

    cuentas_dir = get_base_dir() / "cuentas"
    target_profile = cuentas_dir / f"{nombre}.json"
    auth_file = get_base_dir() / "auth.json"

    if auth_file.is_file() and target_profile.is_file():
        try:
            auth_bytes = auth_file.read_bytes()
            profile_bytes = target_profile.read_bytes()
            if auth_bytes != profile_bytes and len(auth_bytes) > 10:
                private_copy(auth_file, target_profile)
        except Exception:
            pass


def find_active_profile_name(cuentas_dir: Path, auth_path: Path) -> str:
    """Determina el nombre del perfil activo comprobando el marcador y el contenido."""
    rec = get_recorded_active_profile()
    if rec:
        return rec
    if not auth_path.is_file():
        return ""
    try:
        auth_bytes = auth_path.read_bytes()
        for f in cuentas_dir.glob("*.json"):
            if f.read_bytes() == auth_bytes:
                set_recorded_active_profile(f.stem)
                return f.stem
    except Exception:
        pass
    return "(sin guardar / temporal)"


# ==============================================================================
# 3. IDENTIDAD, DECODIFICACIÓN Y CUOTAS (TODO: Implementar según el proveedor)
# ==============================================================================

def decode_account_from_auth(auth_file: Path) -> str:
    """
    [TODO: ESPECÍFICO DEL PROVEEDOR]
    Extrae un identificador amigable del archivo de credenciales (correo, username o clave enmascarada).
    """
    if not auth_file.is_file():
        return "Sin credencial"
    try:
        data = json.loads(auth_file.read_text(encoding="utf-8"))
        # Extraer email, user, o clave según el formato de la herramienta
        return data.get("email") or data.get("user") or data.get("username") or "Usuario"
    except Exception:
        return "Credencial no parseable"


def mask_identifier(ident: str) -> str:
    """Oculta parcialmente correos o identificadores para respuestas JSON seguras."""
    if not ident:
        return "desconocido"
    if "@" in ident:
        user, domain = ident.split("@", 1)
        visible = user[:3] if len(user) >= 3 else user[:1]
        return f"{visible}***@{domain}"
    if len(ident) > 8:
        return f"{ident[:4]}...{ident[-4:]}"
    return "***"


def compute_opaque_identity(auth_file: Path) -> str:
    """
    Genera un hash SHA-256 no reversible de la identidad real (ej: email o ID de cuenta)
    para deduplicación y reserva de leases concurrentes.
    """
    if not auth_file.is_file():
        return ""
    try:
        data = json.loads(auth_file.read_text(encoding="utf-8"))
        ident = data.get("email") or data.get("user_id") or data.get("api_key") or ""
        if ident:
            return hashlib.sha256(f"{PROVIDER_ID}:{ident}".encode("utf-8")).hexdigest()
    except Exception:
        pass
    return ""


def fetch_provider_quota(auth_file: Path, active_profile: str = "") -> dict:
    """
    [TODO: ESPECÍFICO DEL PROVEEDOR]
    Consulta la cuota, saldo o límites de consumo de la cuenta.
    
    Retorna un diccionario estructurado con:
      - email: str
      - plan_type: str
      - rate_limit: { primary_window: {...}, secondary_window: {...} } o None
      - saldo: { total: float, consumido: float, disponible: float, moneda: str } o None
      - err_msg: str | None (en caso de fallo de red o auth)
    
    Si la herramienta no expone cuotas o saldo vía API, establece:
      err_msg = "unsupported_capability" o None con valores informativos.
    """
    if not auth_file.is_file():
        return {"err_msg": "Archivo de credenciales no encontrado"}

    # Ejemplo de estructura de retorno esperada:
    return {
        "email": decode_account_from_auth(auth_file),
        "plan_type": "PRO",
        "rate_limit": {
            "primary_window": {
                "used_percent": 10,
                "limit_window_seconds": 18000,
                "reset_after_seconds": 12000,
                "reset_at": datetime.now(timezone.utc).isoformat()
            },
            "secondary_window": None
        },
        "saldo": None,
        "err_msg": None
    }


# ==============================================================================
# 4. DETECCIÓN DE PROCESOS Y BLOQUEO DE CONCURRENCIA
# ==============================================================================

def get_client_process_names() -> list[str]:
    """
    [TODO: ESPECÍFICO DEL PROVEEDOR]
    Retorna la lista de nombres de ejecutables de la herramienta en ejecución.
    Ej: ["deepseek", "deepseek-cli"] o ["opencode", "opencode-server"]
    """
    return [PROVIDER_ID, f"{PROVIDER_ID}-cli"]


def find_running_clients() -> list[dict]:
    """Escanea /proc en Linux o procesos del sistema para detectar clientes activos."""
    clients = []
    current_pid = os.getpid()
    proc_names = get_client_process_names()

    if not Path("/proc").is_dir():
        return clients

    for p in Path("/proc").glob("[0-9]*"):
        try:
            pid = int(p.name)
            if pid == current_pid:
                continue
            cmdline_file = p / "cmdline"
            if not cmdline_file.is_file():
                continue
            cmdline = cmdline_file.read_bytes().decode("utf-8", errors="ignore").replace("\x00", " ").strip()
            if not cmdline:
                continue
            
            # Verificar si coincide con alguno de los ejecutables clientes
            first_arg = cmdline.split()[0].lower()
            if any(name in first_arg for name in proc_names):
                clients.append({
                    "pid": pid,
                    "cmd": cmdline[:80]
                })
        except Exception:
            continue
    return clients


def find_active_parallel_leases() -> list[str]:
    """Detecta qué perfiles o identidades tienen un lease de ejecución concurrente activo."""
    locks_dir = get_locks_dir()
    busy = []
    for lk in locks_dir.glob("*.lease"):
        try:
            fd = os.open(str(lk), os.O_RDWR)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fd, fcntl.LOCK_UN)
            except (BlockingIOError, OSError):
                busy.append(lk.stem)
            finally:
                os.close(fd)
        except Exception:
            pass
    return busy


# ==============================================================================
# 5. CONTRATO CLI HEADLESS JSON (--json)
# ==============================================================================

def cmd_cuentas_json() -> dict:
    """Contrato: <proveedor>-switch cuentas --json"""
    sync_active_profile()
    auth_path = get_auth_path()
    cuentas_dir = get_cuentas_dir()
    active_profile = find_active_profile_name(cuentas_dir, auth_path) if auth_path.is_file() else ""
    guardadas = sorted(cuentas_dir.glob("*.json"))

    accounts = []
    for f in guardadas:
        p_name = f.stem
        is_active = (p_name == active_profile)
        email = decode_account_from_auth(f)
        accounts.append({
            "alias": p_name,
            "es_activa": is_active,
            "identificador_enmascarado": mask_identifier(email),
            "identidad_opaca": compute_opaque_identity(f),
            "plan": "STANDARD",
            "estado": "disponible"
        })

    return {
        "disponible": True,
        "perfil_activo": active_profile,
        "cuentas": accounts
    }


def cmd_cuota_json(target: str = "") -> dict:
    """Contrato: <proveedor>-switch cuota [alias] --json"""
    sync_active_profile()
    auth_path = get_auth_path()
    cuentas_dir = get_cuentas_dir()
    active_profile = find_active_profile_name(cuentas_dir, auth_path) if auth_path.is_file() else ""
    guardadas = sorted(cuentas_dir.glob("*.json"))
    if target:
        guardadas = [f for f in guardadas if f.stem == target]

    now_iso = datetime.now(timezone.utc).isoformat()
    accounts = []

    for f in guardadas:
        p_name = f.stem
        is_active = (p_name == active_profile)
        q = fetch_provider_quota(f, active_profile=p_name)
        
        status_item = {
            "alias": p_name,
            "es_activa": is_active,
            "identificador_enmascarado": mask_identifier(q.get("email") or ""),
            "identidad_opaca": compute_opaque_identity(f),
            "plan": (q.get("plan_type") or "DESCONOCIDO").upper(),
            "frescura": now_iso,
            "error": q.get("err_msg"),
            "rate_limit": q.get("rate_limit"),
            "saldo": q.get("saldo"),
            "tokens": None
        }
        accounts.append(status_item)

    return {
        "proveedor": PROVIDER_ID,
        "frescura": now_iso,
        "perfil_activo": active_profile,
        "cuotas": accounts
    }


def cmd_ocupacion_json() -> dict:
    """Contrato: <proveedor>-switch ocupacion --json"""
    sync_active_profile()
    running_clients = find_running_clients()
    parallel_busy = find_active_parallel_leases()
    auth_path = get_auth_path()
    cuentas_dir = get_cuentas_dir()
    active_profile = find_active_profile_name(cuentas_dir, auth_path) if auth_path.is_file() else ""
    is_busy = len(running_clients) > 0 or len(parallel_busy) > 0

    return {
        "ocupado": is_busy,
        "puede_conmutar": not is_busy,
        "motivo": "active_session" if is_busy else None,
        "perfil_activo": active_profile,
        "procesos": running_clients,
        "procesos_paralelos": parallel_busy
    }


def cmd_seleccionar_json(nombre: str, dry_run: bool = False) -> dict:
    """Contrato: <proveedor>-switch seleccionar <alias> --json [--dry-run]"""
    cuentas_dir = get_cuentas_dir()
    src = cuentas_dir / f"{nombre}.json"
    if not src.is_file():
        return {
            "solicitud": {"proveedor": PROVIDER_ID, "cuenta_destino": nombre, "dry_run": dry_run},
            "permitido": False,
            "codigo": "invalid_auth",
            "mensaje": f"La cuenta '{nombre}' no existe en {cuentas_dir}",
            "bloqueo_adquirido": False,
            "cambio_realizado": False
        }

    running = find_running_clients()
    if running:
        return {
            "solicitud": {"proveedor": PROVIDER_ID, "cuenta_destino": nombre, "dry_run": dry_run},
            "permitido": False,
            "codigo": "active_session",
            "mensaje": f"No se puede conmutar: hay {len(running)} procesos activos de {PROVIDER_NAME}.",
            "bloqueo_adquirido": False,
            "cambio_realizado": False,
            "procesos": running
        }

    if dry_run:
        return {
            "solicitud": {"proveedor": PROVIDER_ID, "cuenta_destino": nombre, "dry_run": True},
            "permitido": True,
            "codigo": "ok",
            "mensaje": "Conmutación viable y segura (dry-run verificado)",
            "bloqueo_adquirido": False,
            "cambio_realizado": False
        }

    # Sincronizar cuenta saliente antes de conmutar
    sync_active_profile()
    auth_path = get_base_dir() / "auth.json"
    private_copy(src, auth_path)
    set_recorded_active_profile(nombre)

    return {
        "solicitud": {"proveedor": PROVIDER_ID, "cuenta_destino": nombre, "dry_run": False},
        "permitido": True,
        "codigo": "ok",
        "mensaje": f"Cuenta conmutada con éxito a '{nombre}'",
        "bloqueo_adquirido": True,
        "cambio_realizado": True
    }


# ==============================================================================
# 6. EJECUCIÓN CONCURRENTE AISLADA (PARALELO)
# ==============================================================================

def cmd_paralelo(nombre: str, extra_cmd: list[str]):
    """
    Contrato: <proveedor>-switch paralelo <alias> [-- <comando>...]
    Ejecuta un worker en runtime privado con lease atómico no bloqueante.
    """
    cuentas_dir = get_cuentas_dir()
    src = cuentas_dir / f"{nombre}.json"
    if not src.is_file():
        print(f"❌ Error: La cuenta '{nombre}' no existe en {cuentas_dir}.", file=sys.stderr)
        sys.exit(1)

    opaque_id = compute_opaque_identity(src)
    alias_lease = get_locks_dir() / f"alias_{nombre}.lease"
    ident_lease = get_locks_dir() / f"ident_{opaque_id}.lease" if opaque_id else None

    # Adquirir lease por alias
    fd_alias = os.open(str(alias_lease), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd_alias, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (BlockingIOError, OSError):
        print(f"❌ Error: Ya existe una ejecución concurrente activa para el alias '{nombre}'.", file=sys.stderr)
        sys.exit(3)

    # Adquirir lease por identidad real opaca
    fd_ident = None
    if ident_lease:
        fd_ident = os.open(str(ident_lease), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd_ident, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError):
            print(f"❌ Error: Ya existe una ejecución concurrente activa con la misma identidad de '{nombre}'.", file=sys.stderr)
            sys.exit(3)

    # Crear runtime privado aislado en /tmp
    temp_dir = Path(f"/tmp/{PROVIDER_ID}-paralelo-{nombre}-{os.getpid()}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        isolated_auth = temp_dir / "auth.json"
        private_copy(src, isolated_auth)

        # Variables de entorno para redirigir la herramienta al sandbox privado
        env = os.environ.copy()
        env[f"{PROVIDER_ID.upper()}_HOME"] = str(temp_dir)
        env["SWITCH_PARALLEL_ALIAS"] = nombre

        cmd = extra_cmd if extra_cmd else [PROVIDER_ID]
        res = subprocess.run(cmd, env=env)

        # Sincronizar credenciales actualizadas al perfil original
        if isolated_auth.is_file():
            private_copy(isolated_auth, src)

        sys.exit(res.returncode)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if fd_ident is not None:
            fcntl.flock(fd_ident, fcntl.LOCK_UN)
            os.close(fd_ident)
        fcntl.flock(fd_alias, fcntl.LOCK_UN)
        os.close(fd_alias)


# ==============================================================================
# 7. COMANDOS CLI HUMANOS (listar, usar, guardar, reautenticar...)
# ==============================================================================

def cmd_listar():
    sync_active_profile()
    auth_path = get_auth_path()
    cuentas_dir = get_cuentas_dir()
    active_profile = find_active_profile_name(cuentas_dir, auth_path) if auth_path.is_file() else ""
    guardadas = sorted(cuentas_dir.glob("*.json"))

    print(f"\n╭─────────────────────────────────────────────────────────────╮")
    print(f"│  ✦ Cuentas de {PROVIDER_NAME:<44}│")
    print(f"╰─────────────────────────────────────────────────────────────╯")
    if not guardadas:
        print(f"  (No hay cuentas guardadas. Usa: {PROVIDER_ID}-switch guardar <nombre>)\n")
        return

    for f in guardadas:
        is_active = (f.stem == active_profile)
        prefix = "\033[1;33m★ [ACTIVA]\033[0m" if is_active else "          "
        email = decode_account_from_auth(f)
        print(f"  {prefix} \033[1m{f.stem:<16}\033[0m \033[2m{email}\033[0m")
    print()


def cmd_usar(nombre: str, force: bool = False):
    cuentas_dir = get_cuentas_dir()
    src = cuentas_dir / f"{nombre}.json"
    if not src.is_file():
        print(f"❌ La cuenta '{nombre}' no existe en {cuentas_dir}.")
        sys.exit(1)

    running = find_running_clients()
    if running and not force:
        print(f"⚠️  Se detectaron {len(running)} proceso(s) activos de {PROVIDER_NAME}.")
        print("   Usa --force para ignorar o cierra las sesiones antes de conmutar.")
        sys.exit(2)

    sync_active_profile()
    auth_path = get_base_dir() / "auth.json"
    private_copy(src, auth_path)
    set_recorded_active_profile(nombre)
    print(f"✅ Conmutado exitosamente a '{nombre}'.")


def cmd_guardar(nombre: str):
    auth_path = get_auth_path(auto_sync=False)
    if not auth_path.is_file():
        print(f"❌ No hay credenciales activas en {auth_path}.")
        sys.exit(1)
    target = get_cuentas_dir() / f"{nombre}.json"
    private_copy(auth_path, target)
    set_recorded_active_profile(nombre)
    print(f"✅ Cuenta activa guardada como '{nombre}'.")


# ==============================================================================
# 8. ENRUTADOR PRINCIPAL (MAIN)
# ==============================================================================

def main():
    args = sys.argv[1:]

    # Modo Headless JSON
    if "--json" in args:
        subcmd = args[0] if args else "status"
        if subcmd in ("cuentas", "accounts", "listar", "list"):
            print(json.dumps(cmd_cuentas_json(), indent=2))
            sys.exit(0)
        elif subcmd in ("cuota", "quota", "status"):
            target = [a for a in args[1:] if not a.startswith("-")]
            t = target[0] if target else ""
            print(json.dumps(cmd_cuota_json(t), indent=2))
            sys.exit(0)
        elif subcmd in ("ocupacion", "ocupado", "sesiones"):
            res = cmd_ocupacion_json()
            print(json.dumps(res, indent=2))
            sys.exit(0 if not res.get("ocupado") else 1)
        elif subcmd in ("seleccionar", "select"):
            target = [a for a in args[1:] if not a.startswith("-")]
            if not target:
                sys.exit(1)
            dry_run = "--dry-run" in args
            res = cmd_seleccionar_json(target[0], dry_run=dry_run)
            print(json.dumps(res, indent=2))
            sys.exit(0 if res.get("permitido") else 1)

    # Modo Terminal Humano
    if not args or args[0] in ("listar", "list", "ls"):
        cmd_listar()
    elif args[0] in ("usar", "use", "switch"):
        nombre = args[1] if len(args) > 1 and not args[1].startswith("-") else ""
        force = "--force" in args or "-f" in args
        if not nombre:
            print(f"Uso: {PROVIDER_ID}-switch usar <nombre> [--force]")
            sys.exit(1)
        cmd_usar(nombre, force=force)
    elif args[0] in ("guardar", "save"):
        nombre = args[1] if len(args) > 1 and not args[1].startswith("-") else ""
        if not nombre:
            print(f"Uso: {PROVIDER_ID}-switch guardar <nombre>")
            sys.exit(1)
        cmd_guardar(nombre)
    elif args[0] in ("paralelo", "parallel"):
        if len(args) < 2:
            print(f"Uso: {PROVIDER_ID}-switch paralelo <nombre> [-- <comando>...]")
            sys.exit(1)
        nombre = args[1]
        extra_cmd = []
        if "--" in args:
            extra_cmd = args[args.index("--") + 1:]
        cmd_paralelo(nombre, extra_cmd)
    elif args[0] in ("cuentas", "accounts"):
        print(json.dumps(cmd_cuentas_json(), indent=2))
    elif args[0] in ("cuota", "quota", "status"):
        target = args[1] if len(args) > 1 and not args[1].startswith("-") else ""
        print(json.dumps(cmd_cuota_json(target), indent=2))
    elif args[0] in ("ocupacion", "ocupado"):
        res = cmd_ocupacion_json()
        print(json.dumps(res, indent=2))
        sys.exit(0 if not res.get("ocupado") else 1)
    else:
        print(f"Uso: {PROVIDER_ID}-switch [listar | usar <nombre> | guardar <nombre> | paralelo <nombre> | status]")
        sys.exit(1)


if __name__ == "__main__":
    main()
