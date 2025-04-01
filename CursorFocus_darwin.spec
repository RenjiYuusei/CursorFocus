# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\minhr\\Downloads\\CursorFocus\\cli.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\minhr\\Downloads\\CursorFocus\\config.json', '.'), ('C:\\Users\\minhr\\Downloads\\CursorFocus\\.env', '.')],
    hiddenimports=['watchdog.observers.polling', 'watchdog.observers.inotify', 'watchdog.observers.fsevents', 'watchdog.observers.kqueue', 'google.generativeai', 'google.ai.generativelanguage', 'python-dotenv', 'colorama', 'rich', 'tqdm', 'termios', 'fcntl', 'select', 'shutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CursorFocus_darwin',
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
