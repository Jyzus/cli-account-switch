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
# Consultar cuota, tokens restantes y tiempo de reseteo en vivo:
codex-switch status              # o: codex-switch tokens
codex-switch status personal     # consulta una cuenta específica

# Gestión de cuentas:
codex-switch guardar personal
codex-switch nueva trabajo
codex-switch listar              # listado rápido en disco (offline)
codex-switch usar personal
codex-switch continuar

# Lo mismo para Antigravity CLI:
agy-switch status                # o: agy-switch tokens
agy-switch status personal
agy-switch guardar personal
agy-switch nueva trabajo
agy-switch listar
agy-switch usar personal
agy-switch continuar
```

También se aceptan `save`, `new`, `list`, `use`, `resume`, `cuota`, `quota` y `usage`. Ejecutar el comando sin argumentos (`codex-switch` o `agy-switch`) consulta el estado en vivo de todas las cuentas. `id` muestra el identificador de la última conversación detectada; `continuar <id>` permite elegir una explícitamente.

Los alias admiten de 1 a 64 caracteres: letras ASCII, números, puntos, guiones y guiones bajos; deben comenzar por letra o número.

## Consulta de Tokens y Cuotas en Vivo (`status` / `tokens`)

El comando `status` (o `tokens`, `cuota`, `usage`) consulta en tiempo real y en paralelo las APIs oficiales de OpenAI / Google para cada cuenta guardada:
- **Codex CLI**: Muestra ventana de 5 horas (o semanal), porcentaje usado/restante con barras visuales, tiempo exacto hasta el próximo reseteo, créditos de reset disponibles y si la cuenta está lista o agotada.
- **Antigravity CLI**: Muestra la cuota restante de modelos Gemini y de terceros (Claude / GPT), tiempo de refresco y plan/tier activo.
- **Auto-refresco inteligente**: Si un token de acceso OAuth expiró pero posee un refresh token válido, se refresca y actualiza automáticamente en disco sin requerir re-login manual.
- **Detección de cuentas listas**: Resalta qué perfiles tienen tokens disponibles para que sepas a cuál cambiar al instante.

## Datos y comportamiento

- Codex: usa `$CODEX_HOME` o `~/.codex`. Los perfiles se guardan en `cuentas/*.json`.
- Antigravity: usa `~/.gemini/antigravity-cli`. Los perfiles se guardan en `cuentas/*.token`.
- Los perfiles contienen credenciales en texto claro y se escriben con permisos `600`, dentro de un directorio con permisos `700`. No los subas a Git ni los compartas.
- Cada equipo mantiene sus propias cuentas y conversaciones. El instalador distribuye únicamente los scripts; no sincroniza datos.
- Cambiar de perfil conserva los archivos de historial, pero la posibilidad de reanudar depende de la CLI y de los permisos de la cuenta.
- **Protección contra desconexiones accidentales**: Antes de cambiar de cuenta (`usar`) o iniciar sesión (`nueva`), el sistema analiza automáticamente los procesos en ejecución. Si detecta terminales, chats o sesiones activas de Codex o Antigravity, **cancela el cambio de forma segura** e indica en qué terminales y PIDs está corriendo la cuenta para evitar que pierdas tareas o se invaliden tus credenciales. Si estás seguro de forzar el cambio, puedes usar la opción `--force` (o `-f`).
- `codex-switch usar` intenta detener y reiniciar el daemon persistente si lo detecta. Las aplicaciones conectadas deben reconectarse. Las CLI independientes abiertas deben cerrarse y reanudarse.
- `nueva` inicia el flujo de autenticación de la CLI. En Codex también admite `codex-switch nueva trabajo --device-auth`. Usa `usar` después de autenticar si hay procesos persistentes abiertos.
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
