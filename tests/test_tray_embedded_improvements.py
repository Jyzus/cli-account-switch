import os
import subprocess
import sys
from pathlib import Path
from importlib.machinery import SourceFileLoader
import pytest

# Cargar switch-tray como módulo
TRAY_PATH = Path(__file__).resolve().parent.parent / "bin" / "switch-tray"
tray_mod = SourceFileLoader("switch_tray", str(TRAY_PATH)).load_module()


def test_preview_image_generation(tmp_path):
    """Verifica que el comando --preview-image genera un archivo PNG válido."""
    out_png = tmp_path / "test_preview.png"
    res = subprocess.run(
        ["xvfb-run", "-a", sys.executable, str(TRAY_PATH), "--preview-image", str(out_png)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert out_png.is_file()
    assert out_png.stat().st_size > 1000


def test_menu_structure_and_no_title_or_exit():
    """Verifica que el menú no incluya el título truncable, ni 'Iniciar con el sistema', ni 'Salir'."""
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
    except Exception:
        pytest.skip("GTK 3 no disponible en este entorno")

    success, _ = Gtk.init_check(None)
    if not success:
        # En entorno sin X11/Wayland activo fuera de xvfb, probar en subproceso
        cmd = [
            "xvfb-run", "-a", sys.executable, "-c",
            f"""
import sys
from importlib.machinery import SourceFileLoader
mod = SourceFileLoader('switch_tray', '{str(TRAY_PATH)}').load_module()
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

tray = mod.LinuxAppIndicatorTray()
tray.current_status = {{
    'codex': {{'accounts': [{{'name': f'c{{i}}', 'is_active': (i==0), 'available_pct': 80, 'weekly_pct': 60, 'reset_str': '2h'}} for i in range(5)], 'all_accounts': [f'c{{i}}' for i in range(5)]}},
    'agy': {{'accounts': [{{'name': f'a{{i}}', 'is_active': (i==0), 'gemini_pct': 90, 'claude_pct': 85, 'reset_str': '3h'}} for i in range(5)], 'all_accounts': [f'a{{i}}' for i in range(5)]}}
}}
tray._rebuild_menu()
children = tray.menu.get_children()

# 1. Verificar que NO hay título 'CLI Account Switch'
labels = []
for c in children:
    if hasattr(c, 'get_label') and c.get_label():
        labels.append(c.get_label())

assert not any('CLI Account Switch' in l for l in labels), f'Título encontrado en: {{labels}}'

# 2. Verificar que NO hay autostart ni salir
assert not any('Iniciar con el sistema' in l for l in labels), f'Autostart encontrado en: {{labels}}'
assert not any('Salir' in l for l in labels), f'Salir encontrado en: {{labels}}'

# 3. Verificar que el pie contiene los dos botones lado a lado
footer = children[-1]
f_box = footer.get_children()[0]
assert isinstance(f_box, Gtk.Box)
assert f_box.get_orientation() == Gtk.Orientation.HORIZONTAL
buttons = [b for b in f_box.get_children() if isinstance(b, Gtk.Button)]
assert len(buttons) == 2
btn_labels = [b.get_label() for b in buttons]
assert '📊 Abrir Monitor' in btn_labels[0]
assert '↻ Actualizar' in btn_labels[1]
print('OK')
"""
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        assert p.returncode == 0, f"Error en verificación de menú: {p.stderr}\n{p.stdout}"
