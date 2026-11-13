#!/usr/bin/env bash
set -euo pipefail

REPO="Jyzus/cli-account-switch"
BRANCH="${BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"

# Analizar banderas de ejecución
USE_COMPILED=false
for arg in "$@"; do
    case "$arg" in
        --compiled|--binary) USE_COMPILED=true ;;
    esac
done

# Verificar disponibilidad de Python 3.9+
HAS_PYTHON=false
if command -v python3 >/dev/null 2>&1; then
    if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
        HAS_PYTHON=true
    fi
fi

if [ "$HAS_PYTHON" = "false" ] && [ "$USE_COMPILED" = "false" ]; then
    echo "ℹ️  Python 3.9+ no detectado en el sistema."
    echo "   Seleccionando automáticamente la instalación de binarios precompilados..."
    USE_COMPILED=true
fi

mkdir -p -- "$INSTALL_DIR"

# Determinar si se ejecuta localmente (desde repo clonado) o remotamente (curl | bash)
script_file="${BASH_SOURCE[0]:-}"
if [ -n "$script_file" ] && [ "$script_file" != "bash" ] && [ -f "$script_file" ]; then
    source_dir="$(cd -- "$(dirname -- "$script_file")" && pwd)"
else
    source_dir=""
fi

tmp_dir="$(mktemp -d -t switch-install-XXXXXX)"
trap 'rm -rf -- "$tmp_dir"' EXIT

if [ "$USE_COMPILED" = "true" ]; then
    echo "📦 Descargando binarios precompilados desde GitHub Releases (${REPO})..."
    ARCHIVE_URL="https://github.com/${REPO}/releases/latest/download/cli-account-switch-linux-x86_64.tar.gz"
    if curl -fsSL "$ARCHIVE_URL" -o "$tmp_dir/release.tar.gz" 2>/dev/null; then
        tar -xzf "$tmp_dir/release.tar.gz" -C "$tmp_dir"
        for name in switch codex-switch agy-switch switch-widget switch-tray; do
            if [ -f "$tmp_dir/$name" ]; then
                install -m 755 "$tmp_dir/$name" "$INSTALL_DIR/$name"
            fi
        done
        echo "   Binarios precompilados instalados."
    else
        echo "❌ Error al descargar el paquete precompilado desde GitHub Releases." >&2
        exit 1
    fi
elif [ -n "$source_dir" ] && [ -d "$source_dir/bin" ]; then
    # Modo Local (desde el repositorio clonado)
    for name in switch codex-switch agy-switch switch-widget switch-tray; do
        install -m 755 "$source_dir/bin/$name" "$INSTALL_DIR/$name"
    done
    if [ -f "$source_dir/bin/switch-widget.bat" ]; then
        install -m 755 "$source_dir/bin/switch-widget.bat" "$INSTALL_DIR/switch-widget.bat"
    fi
else
    # Modo Remoto (ejecutado directamente mediante: curl -fsSL ... | bash)
    echo "🚀 Descargando e instalando CLI Account Switch desde GitHub (${REPO})..."
    RAW_BASE="https://raw.githubusercontent.com/${REPO}/${BRANCH}"
    for name in switch codex-switch agy-switch switch-widget switch-widget.bat switch-tray; do
        if curl -fsSL "${RAW_BASE}/bin/${name}" -o "$tmp_dir/${name}" 2>/dev/null; then
            install -m 755 "$tmp_dir/${name}" "$INSTALL_DIR/${name}"
        fi
    done
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
    printf '   Acceso directo de escritorio: %s/switch-widget.desktop\n' "$apps_dir"
fi

# Configurar auto-inicio de la barra de tareas si switch-tray está presente
if [ -x "$INSTALL_DIR/switch-tray" ]; then
    "$INSTALL_DIR/switch-tray" --autostart enable >/dev/null 2>&1 || true
    printf '   Auto-inicio en barra de tareas activado (switch-tray --autostart enable)\n'
fi

printf '✅ Instalados switch, codex-switch, agy-switch, switch-widget y switch-tray (v1.2.6) en %s\n' "$INSTALL_DIR"
case ":$PATH:" in
    *":$INSTALL_DIR:"*) ;;
    *) printf '💡 Añade este directorio a tu PATH: export PATH="%s:\$PATH"\n' "$INSTALL_DIR" ;;
esac
