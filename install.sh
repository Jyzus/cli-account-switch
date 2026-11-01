#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
target_dir="${INSTALL_DIR:-$HOME/.local/bin}"
command -v python3 >/dev/null || { echo 'Se requiere Python 3.9 o posterior.' >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || { echo 'Se requiere Python 3.9 o posterior.' >&2; exit 1; }
mkdir -p -- "$target_dir"
for name in codex-switch agy-switch switch-widget; do
    install -m 755 "$source_dir/bin/$name" "$target_dir/$name"
done
if [ -f "$source_dir/bin/switch-widget.bat" ]; then
    install -m 755 "$source_dir/bin/switch-widget.bat" "$target_dir/switch-widget.bat"
fi

# Instalar acceso directo en el menú de aplicaciones de Linux
if [ "$(uname -s 2>/dev/null)" = "Linux" ]; then
    apps_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
    mkdir -p "$apps_dir"
    cat <<EOF > "$apps_dir/switch-widget.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=CLI Account Switch
GenericName=AI Account Monitor & Switcher
Comment=Monitor de cuotas, tokens en vivo y cambio de cuentas para Codex y AGY
Exec=sh -c 'PATH="\$HOME/.local/bin:\$PATH" switch-widget'
Icon=utilities-system-monitor
Terminal=false
Categories=Development;Utility;
Keywords=codex;openai;antigravity;gemini;switch;quota;tokens;widget;
StartupNotify=true
EOF
    chmod 644 "$apps_dir/switch-widget.desktop"
    printf 'Acceso directo de escritorio instalado en %s/switch-widget.desktop\n' "$apps_dir"
fi

printf 'Instalados codex-switch, agy-switch y switch-widget en %s\n' "$target_dir"
case ":$PATH:" in
    *":$target_dir:"*) ;;
    *) printf 'Añade este directorio a tu PATH: %s\n' "$target_dir" ;;
esac
