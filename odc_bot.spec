# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/bot-app.py'],
    pathex=[],
    binaries=[],
    datas=[('src/ControlPanel.py', 'src'), ('src/bot.py', 'src'), ('src/.env', 'src')],
    hiddenimports=['discord', 'pandas'],
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
    name='odc_bot',
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