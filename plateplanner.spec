# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['plateplanner/runner.py'],
    pathex=[],
    binaries=[],
    datas=[
        ("plateplanner/plates","plateplanner/plates"),
        ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='Plate Planner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="plateplanner/resources/icons/icon.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Plate Planner',
)
app = BUNDLE(
    coll,
    name='Plate Planner.app',
    icon="plateplanner/resources/icons/plateplanner.icns",
    bundle_identifier=None,
)
