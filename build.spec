# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import platform

# Determine platform-specific values
system = platform.system().lower()
path_separator = ';' if system == 'windows' else ':'
executable_extension = '.exe' if system == 'windows' else ''
icon_extension = '.ico' if system == 'windows' else '.icns'

# Get the current directory
current_dir = os.getcwd()

# Collect data files
datas = []
config_path = os.path.join(current_dir, 'config.json')
if os.path.exists(config_path):
    datas.append((config_path, "."))

env_path = os.path.join(current_dir, '.env')
if os.path.exists(env_path):
    datas.append((env_path, "."))

# List of hidden imports required by CLI
hiddenimports = [
    "watchdog.observers.polling",
    "watchdog.observers.inotify",
    "watchdog.observers.fsevents",
    "watchdog.observers.kqueue",
    "google.generativeai",
    "google.ai.generativelanguage",
    "python-dotenv",
    "colorama",
    "rich",
    "tqdm",
]

# Add platform-specific hidden imports
if system == 'windows':
    hiddenimports.extend([
        "msvcrt",
    ])
elif system == 'darwin':  # macOS
    hiddenimports.extend([
        "termios",
        "fcntl",
    ])

# Add common hidden imports for both platforms
hiddenimports.extend([
    "select",
    "shutil",
])

# Determine executable name based on version and platform
version = "1.0.0"  # Default version
if os.path.exists(config_path):
    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            version = config.get('version', version)
    except Exception:
        pass

executable_name = f"CursorFocus_{version}_{system}{executable_extension}"

# Add icon if it exists
icon_path = os.path.join(current_dir, f'icon{icon_extension}')
icon_param = []
if os.path.exists(icon_path):
    icon_param = [('icon', icon_path, 'ICON')]

a = Analysis(
    ['cli.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    *icon_param,
    name=executable_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
) 