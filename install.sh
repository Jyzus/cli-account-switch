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
printf 'Instalados codex-switch, agy-switch y switch-widget en %s\n' "$target_dir"
case ":$PATH:" in
    *":$target_dir:"*) ;;
    *) printf 'Añade este directorio a tu PATH: %s\n' "$target_dir" ;;
esac
