# Guía de Integración para Nuevos Agentes y Proveedores CLI
<!-- switch:version=1.2.0 -->

> **Mensaje para el Agente / Modelo de IA (DeepSeek, OpenCode, Claude, etc.):**  
> Si estás leyendo este archivo porque el usuario te indicó *"Lee este archivo para integrarte a Switch"*, estás en el lugar correcto.  
> Tu misión es implementar el soporte completo de tu herramienta o CLI (ej: `deepseek`, `opencode`) dentro de la suite Switch, de modo que cuente con gestión multicuenta, telemetría de cuotas en tiempo real, detección de procesos activos, conmutación atómica segura, ejecución paralela concurrente e integración en la interfaz visual y la bandeja del sistema.

---

## 📑 Índice de Contenidos
1. [Arquitectura y Principios de Switch](#1-arquitectura-y-principios-de-switch)
2. [Fase 0: Auto-Descubrimiento de tu Propia Herramienta](#2-fase-0-auto-descubrimiento-de-tu-propia-herramienta)
3. [Fase 1: Creación del Adaptador `bin/<proveedor>-switch`](#3-fase-1-creación-del-adaptador-binproveedor-switch)
4. [Fase 2: Contrato CLI y Headless JSON Obligatorio](#4-fase-2-contrato-cli-y-headless-json-obligatorio)
5. [Fase 3: Integración en la Suite Unificada (`switch`, Tray y Widget)](#5-fase-3-integración-en-la-suite-unificada-switch-tray-y-widget)
6. [Fase 4: Batería de Pruebas Automatizadas (TDD)](#6-fase-4-batería-de-pruebas-automatizadas-tdd)
7. [Checklist de Entrega (Definition of Done)](#7-checklist-de-entrega-definition-of-done)

---

## 1. Arquitectura y Principios de Switch

Switch es una suite autónoma de gestión de perfiles de cuentas y telemetría para asistentes de codificación CLI.

### Reglas Duras de Desarrollo
- **Python 3.9+ usando exclusivamente la Biblioteca Estándar (`stdlib`)**:  
  Está **estrictamente prohibido** agregar dependencias externas pesadas (`pip install requests`, `pydantic`, etc.). Usa `urllib.request`, `json`, `pathlib`, `fcntl`, `hashlib`, `subprocess`, etc.
- **Permisos Seguros en Disco**:  
  Los directorios de cuentas se crean con `0700` (`rwx------`). Los archivos de credenciales se guardan con `0600` (`rw-------`).
- **Cero Pérdida de Credenciales (Persistencia Bidireccional)**:  
  1. El perfil activo siempre se registra en `~/.<proveedor>/.active_profile`.
  2. Antes de cambiar de cuenta con `usar`, se debe respaldar/sincronizar el estado del archivo activo saliente en su respectivo `cuentas/<alias>.json`.
  3. Tras un nuevo login o refresco de token en vuelo, Switch detecta los bytes nuevos y actualiza el perfil guardado (`sync_active_profile`).
- **Seguridad de Sesiones en Ejecución**:  
  Nunca conmutar credenciales globales si hay procesos interactivos o workers activos de la herramienta, salvo que el usuario pase explícitamente `--force`.
- **Cero Commits Incompletos**:  
  Los tests deben pasar al 100% en verde antes de realizar cualquier commit.

---

## 2. Fase 0: Auto-Descubrimiento de tu Propia Herramienta

Antes de programar, debes responder con precisión las siguientes preguntas sobre tu propia CLI o ecosistema en este entorno:

| Pregunta de Auditoría | Qué debes investigar | Comandos útiles |
| :--- | :--- | :--- |
| **1. Ubicación de Credenciales** | ¿Dónde guarda tu CLI los tokens o llaves de API por defecto? (ej: `~/.config/deepseek/`, `~/.deepseek/auth.json`, `~/.opencode/config.json`). | `find ~ -maxdepth 3 -name "*<tu_tool>*" 2>/dev/null` |
| **2. Formato de Autenticación** | ¿Es un token OAuth (access + refresh + expiry), una API Key estática, o un archivo SQLite/YAML? | Inspecciona la estructura JSON/texto del archivo de autenticación. |
| **3. Telemetría y Cuotas** | ¿Existe un endpoint HTTP oficial de tu API para consultar saldo o límites de consumo? (Ej: DeepSeek cuenta con `https://api.deepseek.com/user/balance`). | Revisa la documentación de tu API de usuario/facturación. Si no existe, define `unsupported_capability`. |
| **4. Detección de Procesos** | ¿Cuáles son los nombres exactos de tus ejecutables cuando corres en la terminal? (ej: `deepseek`, `opencode`, `opencode-server`). | `pgrep -a "<tu_tool>"` o revisar `/proc/[0-9]*/cmdline`. |
| **5. Aislamiento Concurrente** | ¿Qué variable de entorno o flag permite a tu CLI usar un directorio temporal privado sin tocar `~/.<tu_tool>`? (ej: `DEEPSEEK_HOME`, `OPENCODE_CONFIG_DIR`, `--config-dir`). | Revisa cómo tu CLI lee su ruta base de configuración. |

---

## 3. Fase 1: Creación del Adaptador `bin/<proveedor>-switch`

El repositorio incluye una plantilla lista para usar en [`templates/provider_switch_template.py`](file:///home/kaymer/Kaymer/cli-account-switch/templates/provider_switch_template.py).

### Paso 1: Copiar la plantilla
```bash
cp templates/provider_switch_template.py bin/<proveedor>-switch
chmod +x bin/<proveedor>-switch
```

### Paso 2: Implementar los bloques específicos (`TODO`)
Edita `bin/<proveedor>-switch` y completa las siguientes funciones:

1. **`PROVIDER_ID` y `PROVIDER_NAME`**:
   ```python
   PROVIDER_ID = "deepseek"       # Nombre corto en minúsculas
   PROVIDER_NAME = "DeepSeek"     # Nombre formal para la UI
   ```

2. **`get_base_dir()` y `get_auth_path()`**:
   Define dónde se ubica la configuración y el archivo activo de autenticación.
   ```python
   def get_base_dir() -> Path:
       env_override = os.environ.get("DEEPSEEK_HOME")
       if env_override:
           return Path(env_override)
       return Path.home() / ".deepseek"

   def get_auth_path(auto_sync: bool = True) -> Path:
       if auto_sync:
           sync_active_profile()
       return get_base_dir() / "config.json"
   ```

3. **`decode_account_from_auth(auth_file: Path) -> str`**:
   Extrae una etiqueta amigable (email, usuario o API key enmascarada) del archivo.

4. **`fetch_provider_quota(auth_file: Path, active_profile: str = "") -> dict`**:
   Consulta el estado de cuota, tokens o saldo.  
   - Si tu API tiene endpoint de balance (ejemplo para DeepSeek):
     ```python
     # Consulta a https://api.deepseek.com/user/balance con Authorization: Bearer <api_key>
     ```
   - Si no expone saldo o cuota:
     Retorna `"rate_limit": None, "saldo": None, "err_msg": None` (o código `"unsupported_capability"` si aplica). **Nunca inventes cuota falsa**.

5. **`get_client_process_names() -> list[str]`**:
   Lista de ejecutables a buscar en `/proc` para proteger sesiones activas.
   ```python
   def get_client_process_names() -> list[str]:
       return ["deepseek", "deepseek-cli"]
   ```

6. **`cmd_nueva(nombre)` y `cmd_reautenticar(nombre)`**:
   Flujo interactivo para pedir API key o invocar el login nativo (`deepseek login`).

---

## 4. Fase 2: Contrato CLI y Headless JSON Obligatorio

Tu script `bin/<proveedor>-switch` DEBE responder a dos modos de ejecución:

### A. Modo Interactivo Humano (Terminal)
- `<proveedor>-switch listar`: Listado visual rápido de cuentas en disco con marcador `★ [ACTIVA]`.
- `<proveedor>-switch status [alias]`: Detalle de cuotas, saldo y modelos.
- `<proveedor>-switch usar <alias> [--force]`: Conmutación atómica del archivo de credenciales.
- `<proveedor>-switch guardar <alias>`: Guarda la sesión activa actual en `cuentas/<alias>.json`.
- `<proveedor>-switch reautenticar [alias]`: Reautentica sesión vencida y guarda en el perfil.
- `<proveedor>-switch login <alias>`: Redirige a `reautenticar` si `<alias>` existe, o `nueva` si no.
- `<proveedor>-switch paralelo <alias> [-- <comando>...]`: Ejecución aislada con lease lock.

### B. Modo Headless JSON (`--json`)
Este contrato es consumido por Planifier, agentes autónomos y la CLI unificada `switch`:

#### 1. `cuentas --json`
```json
{
  "disponible": true,
  "perfil_activo": "cuenta_pro",
  "cuentas": [
    {
      "alias": "cuenta_pro",
      "es_activa": true,
      "identificador_enmascarado": "use***@domain.com",
      "identidad_opaca": "a3f5b8...",
      "plan": "DEEPSEEK-V3",
      "estado": "disponible"
    }
  ]
}
```

#### 2. `cuota [alias] --json`
```json
{
  "proveedor": "deepseek",
  "frescura": "2026-11-08T18:00:00Z",
  "perfil_activo": "cuenta_pro",
  "cuotas": [
    {
      "alias": "cuenta_pro",
      "es_activa": true,
      "identificador_enmascarado": "use***@domain.com",
      "identidad_opaca": "a3f5b8...",
      "plan": "DEEPSEEK-V3",
      "frescura": "2026-11-08T18:00:00Z",
      "error": null,
      "rate_limit": null,
      "saldo": {
        "total": 50.0,
        "consumido": 8.2,
        "disponible": 41.8,
        "moneda": "USD"
      },
      "tokens": null
    }
  ]
}
```

#### 3. `ocupacion --json`
```json
{
  "ocupado": false,
  "puede_conmutar": true,
  "motivo": null,
  "perfil_activo": "cuenta_pro",
  "procesos": [],
  "procesos_paralelos": []
}
```

#### 4. `seleccionar <alias> --json [--dry-run]`
```json
{
  "solicitud": {
    "proveedor": "deepseek",
    "cuenta_destino": "cuenta_pro",
    "dry_run": false
  },
  "permitido": true,
  "codigo": "ok",
  "mensaje": "Cuenta conmutada con éxito a 'cuenta_pro'",
  "bloqueo_adquirido": true,
  "cambio_realizado": true
}
```
*Códigos estándar posibles*: `"ok"`, `"active_session"`, `"invalid_auth"`, `"unsupported_capability"`.

---

## 5. Fase 3: Integración en la Suite Unificada (`switch`, Tray y Widget)

Una vez probado `bin/<proveedor>-switch`, debes registrarlo en el resto de la suite:

### 1. Modificar [`bin/switch`](file:///home/kaymer/Kaymer/cli-account-switch/bin/switch)
1. **`cmd_preflight_json()`**:
   - Activar capability `parallel_<proveedor>: true` (si soporta concurrencia aislada).
   - Añadir `<proveedor>` al diccionario `proveedores` con `soportado: true`.
2. **`cmd_cuota_json()`, `cmd_cuentas_json()`, `cmd_ocupacion_json()`**:
   - Añadir la llamada a `<proveedor>-switch`.
3. **`cmd_seleccionar_json()`**:
   - Agregar condición para despachar a `<proveedor>-switch seleccionar ...`.
4. **`cmd_paralelo()`**:
   - Agregar enrutamiento: `elif prov in ("<proveedor>", ...): exec_subcommand("<proveedor>-switch", ...)`.
5. **`cmd_usar()` y `cmd_reautenticar()`**:
   - Verificar si el alias existe en `~/.<proveedor>/cuentas/<alias>.json` para auto-detectar el proveedor.
6. **Enrutamiento general en `main()`**:
   - Añadir `elif args[0] in ("<proveedor>", ...): exec_subcommand("<proveedor>-switch", args[1:])`.

### 2. Modificar [`bin/switch-tray`](file:///home/kaymer/Kaymer/cli-account-switch/bin/switch-tray)
- En `fetch_tray_status()`: Agregar consulta a `<proveedor>-switch` (vía `ThreadPoolExecutor` para no bloquear el bucle de eventos del tray).
- En el menú contextual y salida de terminal: Mostrar las cuentas y cuota del nuevo proveedor.

### 3. Modificar [`bin/switch-widget`](file:///home/kaymer/Kaymer/cli-account-switch/bin/switch-widget)
- Crear una subclase `<Proveedor>Provider(BaseProvider)` implementando `fetch_status()` y `use_account()`.
- Agregarla a la lista de proveedores del servidor REST.

### 4. Modificar [`install.sh`](file:///home/kaymer/Kaymer/cli-account-switch/install.sh)
- Añadir `<proveedor>-switch` a la lista de binarios que se copian a `$INSTALL_DIR`.

---

## 6. Fase 4: Batería de Pruebas Automatizadas (TDD)

Crea un archivo de tests en `tests/test_<proveedor>_switch.py` usando `pytest`:

```python
"""
Tests para el adaptador <proveedor>-switch.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
PROV_CLI = BIN_DIR / "<proveedor>-switch"

@pytest.fixture
def isolated_env(tmp_path: Path):
    home = tmp_path / "home"
    prov_home = home / ".<proveedor>"
    cuentas = prov_home / "cuentas"
    cuentas.mkdir(parents=True)
    
    # Crear cuenta de prueba
    test_auth = {"email": "test@domain.com", "api_key": "sk-test-1234"}
    (cuentas / "cuenta1.json").write_text(json.dumps(test_auth), encoding="utf-8")
    (prov_home / "auth.json").write_text(json.dumps(test_auth), encoding="utf-8")
    
    env = os.environ.copy()
    env["HOME"] = str(home)
    env[f"<PROVEEDOR>_HOME"] = str(prov_home)
    env["PATH"] = f"{BIN_DIR}:{env.get('PATH', '')}"
    return {"env": env, "prov_home": prov_home, "cuentas": cuentas}

def test_cuentas_json(isolated_env):
    res = subprocess.run([sys.executable, str(PROV_CLI), "cuentas", "--json"],
                         env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["disponible"] is True
    assert len(data["cuentas"]) >= 1
    assert data["cuentas"][0]["alias"] == "cuenta1"

def test_conmutacion_segura(isolated_env):
    # Probar conmutación y verificación de .active_profile
    res = subprocess.run([sys.executable, str(PROV_CLI), "usar", "cuenta1", "--force"],
                         env=isolated_env["env"], capture_output=True, text=True)
    assert res.returncode == 0
    marker = isolated_env["prov_home"] / ".active_profile"
    assert marker.is_file()
    assert marker.read_text(encoding="utf-8").strip() == "cuenta1"
```

---

## 7. Checklist de Entrega (Definition of Done)

Antes de considerar tu integración completa y solicitar commit, verifica:

- [ ] `bin/<proveedor>-switch` tiene permisos de ejecución (`chmod +x`).
- [ ] `python3 -m py_compile bin/<proveedor>-switch` compila sin errores de sintaxis.
- [ ] `bin/<proveedor>-switch cuentas --json` responde en milisegundos con el formato esperado.
- [ ] `bin/<proveedor>-switch cuota --json` responde limpiamente sin romper credenciales.
- [ ] `bin/<proveedor>-switch ocupacion --json` detecta procesos clientes en `/proc`.
- [ ] `bin/<proveedor>-switch seleccionar <cuenta> --json` respeta bloqueos y conmutación atómica.
- [ ] `bin/<proveedor>-switch paralelo <cuenta>` aísla el entorno en runtime temporal sin pisar la cuenta global.
- [ ] `switch preflight --json` reporta `soportado: true` para tu proveedor.
- [ ] `switch status` muestra el bloque de tu proveedor.
- [ ] `./install.sh` instala el nuevo binario en `$INSTALL_DIR`.
- [ ] Todos los tests unitarios (`pytest tests/`) pasan al **100% en verde**.
- [ ] No hay archivos temporales ni credenciales reales en el árbol git (`git status`).
