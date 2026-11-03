# CLI Account Switch

Gestores de perfiles locales para **Codex CLI** (`codex-switch`) y **Antigravity CLI** (`agy-switch`), acompañados de un **Widget de Barra de Tareas / Bandeja del Sistema ultraligero** (`switch-tray`) y un **Desktop Dashboard flotante** (`switch-widget`). Guarda una autenticación con un alias, cambia de perfil en 1 clic, monitorea cuotas en tiempo real con mínimo consumo y reanuda tus conversaciones desde la terminal o desde tu entorno de escritorio.

Proyecto independiente, sin afiliación con los proveedores de las herramientas.

## Instalación

### Método 1: Instalación rápida con un solo comando (Recomendado)

Instala directamente sin necesidad de clonar el repositorio:

```bash
# Instalación estándar (requiere Python 3.9+):
curl -fsSL https://raw.githubusercontent.com/Jyzus/cli-account-switch/main/install.sh | bash

# O instalación con binarios precompilados independientes (sin necesidad de Python):
curl -fsSL https://raw.githubusercontent.com/Jyzus/cli-account-switch/main/install.sh | bash -s -- --compiled
```

### Método 2: Clonando el repositorio

```bash
git clone https://github.com/Jyzus/cli-account-switch.git
cd cli-account-switch
./install.sh
```

El destino predeterminado en sistemas Unix es `~/.local/bin`. Si no está en tu `PATH`, añade a `~/.bashrc` o `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

En **Windows**, puedes ejecutar `switch-widget.bat` directamente o añadir la carpeta `bin\` a tu variable de entorno `PATH`.

Puedes elegir otro destino en Unix: `INSTALL_DIR=/ruta/bin ./install.sh`.

## Desktop Widget Multiplataforma (`switch-widget`)

Un widget visual flotante con diseño moderno (Glassmorphism oscuro) que monitorea todas tus cuentas en segundo plano:

```bash
# Lanzar el widget completo (Codex y AGY):
switch-widget

# O lanzarlo directamente desde cualquiera de las CLIs:
codex-switch widget
agy-switch widget
```

### Características del Widget:
- **Multiplataforma**: Funciona de forma nativa en **Linux**, **macOS** y **Windows**. Se abre automáticamente en modo aplicación dedicado (ventana independiente sin pestañas ni barra de URL mediante Chromium, Google Chrome, Brave o Microsoft Edge).
- **Actualización automática periódica**: Configurable desde la barra superior (1 min, 3 min, 5 min por defecto, 10 min, 15 min o Pausar) con temporizador regresivo en vivo (`⏱ 04:32`).
- **Botón de actualización manual**: Botón `↺ Actualizar` con retroalimentación inmediata y animación de carga para forzar la consulta en vivo de todas las cuentas al instante.
- **Relojes de reinicio en tiempo real**: Contadores regresivos que descuentan segundo a segundo (`⏳ Resetea en: 2h 45m 12s` o `4d 18h 22m`), alertando en verde cuando la cuota se resetea.
- **Consumo Semanal (7 días) y Límite Corto (5 horas)**:
  - Visualización gráfica detallada con barras de progreso de degradado dinámico (verde para cuota alta, ámbar para media, rojo para agotada).
  - Porcentaje consumido y porcentaje restante de la cuota semanal.
  - Para OpenAI Codex: Límite primario (5h), Consumo semanal (7d) y créditos de reinicio disponibles.
  - Para Antigravity: Límites independientes para modelos Gemini (Flash/Pro) y modelos de terceros (Claude 3P / Opus / Sonnet).
- **Cambio de cuenta en 1 clic**: Cambia la cuenta activa directamente desde la tarjeta con el botón `⚡ Usar Esta Cuenta`.
- **Protección contra rotura de sesiones**: Si tienes terminales activas con la cuenta actual, el widget despliega un aviso modal con los PIDs y terminales en ejecución para evitar desconexiones accidentales, permitiéndote cancelar o forzar el cambio (`--force`).
- **Búsqueda y filtros**: Filtra al instante por proveedor (`Todos`, `OpenAI Codex`, `Google AGY`) o busca por alias o correo electrónico.

### Opciones de la línea de comandos de `switch-widget`:
```bash
switch-widget --port 4920           # Personalizar el puerto local
switch-widget --host 0.0.0.0        # Permitir acceso desde otros equipos o móvil en la misma red
switch-widget --filter codex        # Filtrar inicialmente solo Codex (o agy)
switch-widget --no-browser          # Modo servidor sin abrir ventana automáticamente
switch-widget --browser-tab         # Abrir en pestaña estándar de navegador
```

## Taskbar / System Tray Widget (`switch-tray`)

Diseñado específicamente para **mantenerse siempre activo con el mínimo consumo de recursos** (0% CPU en reposo y ~15MB RAM). Muestra el estado de tokens y cuotas directamente en la barra de tareas o bandeja del sistema y se inicializa automáticamente al arrancar tu computadora:

```bash
# Iniciar el widget en la barra de tareas:
switch-tray

# O lanzarlo directamente desde cualquiera de las CLIs:
codex-switch tray
agy-switch tray
```

### Características del Widget de Barra de Tareas:
- **Consumo Mínimo de Recursos**: Integrado de forma nativa con **AyatanaAppIndicator3 / Gtk 3** en Linux (GNOME, KDE Plasma, Ubuntu, XFCE) y `pystray` en Windows/macOS. Sin dependencias pesadas de navegadores ni frameworks web.
- **Etiqueta en vivo en el panel**: Visualiza tus tokens de un vistazo directo sin abrir menús:  
  `Codex: 100% | AGY: 91%` (o alertas visuales de estado ⚠️).
- **Iconos dinámicos SVG**: Indicador visual inteligente en el panel (Verde para cuota óptima >40%, Ámbar para cuota media ≤40%, Rojo para cuota crítica ≤15% o Agotada, y Carmesí para errores).
- **Menú contextual interactivo (clic derecho / clic)**:
  - **Detalle de cada cuenta activa**: Muestra el nombre de perfil, porcentaje de disponibilidad y tiempo restante de reinicio (`Codex [cuenta1]: 100% disp · resetea en 5h 0m`).
  - **Cambio de cuenta rápido en submenús**: `Cambiar cuenta Codex ▸` y `Cambiar cuenta AGY ▸` para alternar entre cualquiera de tus cuentas guardadas con un solo clic.
  - **Protección contra rotura de sesión**: Verifica automáticamente si hay sesiones o chats activos en terminales antes de efectuar la conmutación.
  - **Actualización manual**: Botón `↻ Actualizar ahora` para forzar la consulta en vivo de todas las cuotas inmediatamente.
  - **Acceso directo al dashboard completo**: Botón `📊 Abrir Monitor Completo (Widget)` para abrir la ventana visual detallada cuando requieras ver gráficos semanales.
  - **Control de auto-arranque**: Activa o desactiva con un clic la opción `⚙️ Iniciar con el sistema [✓ Activado]`.
- **Auto-inicio con el sistema (Autostart)**:
  - En **Linux**: Archivo estándar XDG Autostart en `~/.config/autostart/switch-tray.desktop` (creado automáticamente al instalar o mediante el menú).
  - En **Windows**: Acceso directo en la carpeta de Inicio de Windows (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\switch-tray.bat`).
  - En **macOS**: Agente de inicio en `~/Library/LaunchAgents/com.user.switch-tray.plist`.

### Comandos de control de `switch-tray`:
```bash
switch-tray --status                 # Consulta rápida del estado en la terminal
switch-tray --autostart enable       # Activar inicio automático con la computadora
switch-tray --autostart disable      # Desactivar inicio automático
switch-tray --autostart status       # Comprobar si el auto-inicio está activo
switch-tray -i 600                   # Cambiar intervalo de sondeo a 10 minutos (por defecto: 300s = 5m)
```

## Uso por Terminal (CLI)

```bash
# Consultar cuota, tokens restantes y tiempo de reseteo en vivo:
codex-switch status              # o: codex-switch tokens
codex-switch status personal     # consulta una cuenta específica

# Abrir el widget en la barra de tareas o el widget gráfico de escritorio:
codex-switch tray                # o: switch-tray (bajo consumo)
codex-switch widget              # o: switch-widget (dashboard flotante)

# Gestión de cuentas:
codex-switch agregar trabajo         # agrega una cuenta en entorno aislado SIN cerrar tus chats activos
codex-switch agregar trabajo --desde creds.json # importa credenciales directamente sin abrir navegador
codex-switch guardar personal        # guarda las credenciales activas (evita duplicados automáticos)
codex-switch eliminar antigua        # elimina un perfil guardado (alias: borrar, rm, quitar)
codex-switch renombrar viejo nuevo   # renombra un alias existente (alias: mv, rename)
codex-switch nueva trabajo           # inicia sesión interactiva para otra cuenta
codex-switch listar                  # listado rápido en disco (offline)
codex-switch usar personal           # cambia de cuenta y reinicia daemon
codex-switch continuar               # reanuda última tarea

# Lo mismo para Antigravity CLI:
agy-switch status                # o: agy-switch tokens
agy-switch status personal
agy-switch tray                  # widget de barra de tareas
agy-switch widget                # abre el dashboard gráfico flotante
agy-switch agregar trabajo       # agrega una cuenta en entorno aislado SIN cerrar tus chats activos
agy-switch agregar trabajo --desde token.json # importa token directamente sin abrir navegador
agy-switch guardar personal      # guarda las credenciales activas
agy-switch eliminar antigua      # elimina un perfil guardado (alias: borrar, rm, quitar)
agy-switch renombrar viejo nuevo # renombra un alias existente (alias: mv, rename)
agy-switch nueva trabajo
agy-switch listar
agy-switch usar personal
agy-switch continuar
```

También se aceptan `save`, `rm`, `borrar`, `quitar`, `delete`, `mv`, `rename`, `new`, `list`, `use`, `resume`, `cuota`, `quota` y `usage`. Ejecutar el comando sin argumentos (`codex-switch` o `agy-switch`) consulta el estado en vivo de todas las cuentas. `id` muestra el identificador de la última conversación detectada; `continuar <id>` permite elegir una explícitamente.

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
- **Compatibilidad con GNOME Keyring en Linux**: Antigravity CLI en entornos de escritorio Linux almacena por defecto sus credenciales en el Secret Service del sistema (GNOME Keyring / libsecret). `agy-switch` detecta y sincroniza automáticamente las credenciales entre el Keyring del sistema y el archivo de tokens local (`~/.gemini/antigravity-cli/antigravity-oauth-token`), permitiendo guardar, consultar y alternar perfiles sin discrepancias tanto en entornos gráficos de escritorio como en servidores headless.
- **Agregar cuentas en entorno aislado sin interrumpir sesiones (`agregar`)**: Con `codex-switch agregar <alias>` y `agy-switch agregar <alias>` (alias: `add`), puedes autenticar y registrar cuentas adicionales para que aparezcan en tu panel de monitoreo (`switch-widget`, `switch-tray` y `status`) **sin tener que cerrar tus chats abiertos ni cambiar de cuenta activa**. La autenticación se ejecuta en un sandbox temporal aislado que no toca tu sesión activa ni archivos en uso. Además, soporta `--desde <archivo_o_json>` para importar credenciales directas sin abrir navegador.
- **Protección contra perfiles duplicados y sobrescrituras**: Al ejecutar `guardar <alias>`, el sistema verifica automáticamente si la cuenta activa ya se encuentra guardada bajo otro perfil. Si ya existe, bloquea la duplicación innecesaria y sugiere renombrarlo con `renombrar` o forzarlo con `--force`. Asimismo, si el alias ya pertenece a otra cuenta diferente, previene la sobrescritura accidental a menos que se indique `--force`.
- **Eliminación y renombrado ágil**: Puedes depurar cuentas guardadas con `eliminar <alias>` (o `borrar`, `rm`, `quitar`, así como desde el botón 🗑 del widget de escritorio) y renombrar perfiles con `renombrar <actual> <nuevo>` (o `mv`, `rename`) sin perder configuraciones ni tokens.
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
