# -*- mode: python ; coding: utf-8 -*-

import os
import platform
from dotenv import load_dotenv

# Load environment variables to get version
load_dotenv()
version = os.getenv('VERSION', '1.0.0')

# Set output name based on system type
system = platform.system().lower()
if system == "windows":
    os_type = "windows"
    executable_extension = '.exe'
    icon_extension = '.ico'
elif system == "linux":
    os_type = "linux"
    executable_extension = ''
    icon_extension = '.ico'
else:  # Darwin (macOS)
    os_type = "mac"
    executable_extension = ''
    icon_extension = '.icns'

output_name = f"CursorFocus_{version}_{os_type}{executable_extension}"

# Get current directory
current_dir = os.getcwd()

# Collect data files
datas = [
    ('config.json', '.'),
    ('.env', '.'),
    ('examples', 'examples'),
]

# Add icon if it exists
icon_path = os.path.join(current_dir, f'icon{icon_extension}')
icon_param = []
if os.path.exists(icon_path):
    icon_param = [('icon', icon_path, 'ICON')]

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

# Get target architecture from environment variable
target_arch = os.environ.get('TARGET_ARCH', None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    *icon_param,
    name=output_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,  # No effect on non-Mac platforms
    target_arch=target_arch,  # Only specified when needed via environment variable
    codesign_identity=None,
    entitlements_file=None,
) 