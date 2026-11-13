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


def test_format_account_label():
    """Verifica la lógica de formateo para Codex y AGY con prefijos de activación."""
    # Codex activo
    c_act = {"name": "principal", "is_active": True, "available_pct": 85, "weekly_pct": 72}
    assert tray_mod.format_account_label("codex", c_act) == "✓ principal · 85% | 72% sem"

    # Codex inactivo
    c_inact = {"name": "backup", "is_active": False, "available_pct": 40, "weekly_pct": 30}
    assert tray_mod.format_account_label("codex", c_inact) == "  backup · 40% | 30% sem"

    # AGY activo
    a_act = {"name": "trabajo", "is_active": True, "gemini_pct": 90, "claude_pct": 80}
    assert tray_mod.format_account_label("agy", a_act) == "✓ trabajo · 90% | 80% sem"

    # AGY con error
    a_err = {"name": "dev", "is_active": False, "error": "Token vencido"}
    assert tray_mod.format_account_label("agy", a_err) == "  dev · ⚠️ Token vencido"


def test_menu_structure_and_no_title_or_exit():
    """Verifica la estructura limpia del menú nativo: encabezados centrados, 3 cuentas max y único botón."""
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
    'codex': {{
        'accounts': [
            {{'name': f'c{{i}}', 'is_active': (i==0), 'available_pct': 80 - i*10, 'weekly_pct': 60, 'reset_str': '2h'}}
            for i in range(5)
        ],
        'all_accounts': [f'c{{i}}' for i in range(5)]
    }},
    'agy': {{
        'accounts': [
            {{'name': f'a{{i}}', 'is_active': (i==0), 'gemini_pct': 90 - i*10, 'claude_pct': 85, 'reset_str': '3h'}}
            for i in range(5)
        ],
        'all_accounts': [f'a{{i}}' for i in range(5)]
    }}
}}
tray._rebuild_menu()
children = tray.menu.get_children()

labels = [c.get_label() for c in children if hasattr(c, 'get_label') and c.get_label()]

# 1. Sin títulos truncables ni opciones de autostart/salir
assert not any('CLI Account Switch' in l for l in labels), f'Título encontrado en: {{labels}}'
assert not any('Iniciar con el sistema' in l for l in labels), f'Autostart encontrado en: {{labels}}'
assert not any('Salir' in l for l in labels), f'Salir encontrado en: {{labels}}'
assert not any('Actualizar' in l for l in labels), f'Actualizar encontrado en: {{labels}}'

# 2. Encabezados centrados presentes
assert '--------- Codex ---------' in labels
assert '---------- AGY ----------' in labels

# 3. Solo 3 cuentas por proveedor (total 6 ítems de cuenta)
codex_items = [l for l in labels if l.startswith('✓ c') or l.startswith('  c')]
agy_items = [l for l in labels if l.startswith('✓ a') or l.startswith('  a')]
assert len(codex_items) == 3, f'Esperadas 3 cuentas codex, obtenidas: {{codex_items}}'
assert len(agy_items) == 3, f'Esperadas 3 cuentas agy, obtenidas: {{agy_items}}'

# 4. Chequeo de activo/inactivo
assert codex_items[0].startswith('✓ c0 · ')
assert codex_items[1].startswith('  c1 · ')

# 5. Único botón extra en el pie
last_item = [c for c in children if hasattr(c, 'get_label') and c.get_label()][-1]
assert last_item.get_label() == '📊 Abrir Monitor'
print('OK_MENU')
"""
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 0, f"Error en verificación de menú: {p.stderr}\n{p.stdout}"
    assert "OK_MENU" in p.stdout


def test_tray_daemon_lifecycle():
    """Verifica comandos de gestión de ciclo de vida en segundo plano (start/stop/status)."""
    p_stop = subprocess.run([sys.executable, str(TRAY_PATH), "stop"], capture_output=True, text=True)
    assert p_stop.returncode == 0
    assert "no estaba en ejecución" in p_stop.stdout

    p_help = subprocess.run([sys.executable, str(TRAY_PATH), "--help"], capture_output=True, text=True)
    assert p_help.returncode == 0
    assert "start" in p_help.stdout
    assert "stop" in p_help.stdout
    assert "restart" in p_help.stdout
    assert "--preview-image" in p_help.stdout
    assert "--foreground" in p_help.stdout or "-f" in p_help.stdout
