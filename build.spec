# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all required data files
datas = []
datas += collect_data_files('watchdog')
datas += collect_data_files('google')
datas += collect_data_files('rich')
datas += collect_data_files('tqdm')

# Collect all required hidden imports
hiddenimports = []
hiddenimports += collect_submodules('watchdog')
hiddenimports += collect_submodules('google')
hiddenimports += collect_submodules('rich')
hiddenimports += collect_submodules('tqdm')

# Add platform-specific imports
if sys.platform == 'win32':
    hiddenimports += ['msvcrt']
elif sys.platform == 'darwin':
    hiddenimports += ['termios', 'fcntl']

# Add common imports
hiddenimports += ['select', 'shutil']

# Get version from environment or default
version = os.getenv('VERSION', '1.0.0')

# Determine platform-specific executable name
if sys.platform == 'win32':
    exe_name = f'CursorFocus_{version}_windows'
    icon_ext = '.ico'
elif sys.platform == 'darwin':
    exe_name = f'CursorFocus_{version}_mac'
    icon_ext = '.icns'
else:  # Linux
    exe_name = f'CursorFocus_{version}_linux'
    icon_ext = '.ico'

# Add icon if it exists
icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'icon{icon_ext}')
icon_param = [icon_path] if os.path.exists(icon_path) else None

a = Analysis(
    ['cli.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
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
    icon=icon_param[0] if icon_param else None,
) 