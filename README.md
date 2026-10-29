# CLI Account Switch

Gestores de perfiles locales para **Codex CLI** (`codex-switch`) y **Antigravity CLI** (`agy-switch`). Guarda una autenticación con un alias, cambia de perfil y reanuda tus conversaciones desde la terminal.

Proyecto independiente, sin afiliación con los proveedores de las herramientas.

## Instalación

Requisitos: Python 3.9 o posterior, Bash y la CLI correspondiente instalada y autenticada. Pensado para Linux, macOS y WSL; las comprobaciones automatizadas se ejecutan en Linux. No instala Codex ni Antigravity.

```bash
git clone https://github.com/Jyzus/cli-account-switch.git
cd cli-account-switch
./install.sh
```

El destino predeterminado es `~/.local/bin`. Si no está en tu `PATH`, añade a `~/.bashrc` o `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Puedes elegir otro destino: `INSTALL_DIR=/ruta/bin ./install.sh`.

## Uso

```bash
codex-switch guardar personal
codex-switch nueva trabajo
codex-switch listar
codex-switch usar personal
codex-switch continuar

agy-switch guardar personal
agy-switch nueva trabajo
agy-switch usar personal
agy-switch continuar
```

También se aceptan `save`, `new`, `list`, `use` y `resume`. Ejecuta cualquiera sin argumentos para consultar el estado. `id` muestra el identificador de la última conversación detectada; `continuar <id>` permite elegir una explícitamente.

Los alias admiten de 1 a 64 caracteres: letras ASCII, números, puntos, guiones y guiones bajos; deben comenzar por letra o número.

## Datos y comportamiento

- Codex: usa `$CODEX_HOME` o `~/.codex`. Los perfiles se guardan en `cuentas/*.json`.
- Antigravity: usa `~/.gemini/antigravity-cli`. Los perfiles se guardan en `cuentas/*.token`.
- Los perfiles contienen credenciales en texto claro y se escriben con permisos `600`, dentro de un directorio con permisos `700`. No los subas a Git ni los compartas.
- Cada equipo mantiene sus propias cuentas y conversaciones. El instalador distribuye únicamente los scripts; no sincroniza datos.
- Cambiar de perfil conserva los archivos de historial, pero la posibilidad de reanudar depende de la CLI y de los permisos de la cuenta.
- `codex-switch usar` intenta detener y reiniciar el daemon persistente si lo detecta. Las aplicaciones conectadas deben reconectarse. Las CLI independientes abiertas deben cerrarse y reanudarse.
- `nueva` inicia el flujo de autenticación de la CLI. En Codex también admite `codex-switch nueva trabajo --device-auth`. Usa `usar` después de autenticar si hay procesos persistentes abiertos.
- En Antigravity, cierra los procesos abiertos antes de cambiar de cuenta. El script no reinicia procesos de Antigravity.
- La detección de cuenta activa compara archivos; un refresco de tokens puede hacer que un perfil aparezca como temporal. Vuelve a guardarlo para actualizar la copia.

Estos scripts dependen de rutas y formatos internos de las CLI, que pueden cambiar. Evita ejecutar cambios de cuenta simultáneamente en el mismo directorio de configuración.

## Actualización y desinstalación

```bash
git pull --ff-only
./install.sh
```

Para desinstalar, elimina `codex-switch` y `agy-switch` del directorio de instalación. Tus perfiles e historiales permanecen en sus directorios de configuración.

## Contribuciones

Las mejoras y correcciones son bienvenidas mediante issues y pull requests. No adjuntes tokens, credenciales ni archivos de autenticación a los reportes.

Licencia MIT. Consulta [LICENSE](LICENSE).
