from PyInstaller.utils.hooks import collect_submodules

hidden_imports = (
    collect_submodules("twitchAPI")
    + collect_submodules("core")
    + collect_submodules("adapter")
    + collect_submodules("ui")
    + collect_submodules("services")
)

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("config", "config"),
        ("tools", "tools"),
    ],
    hiddenimports=hidden_imports,
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
    [],
    name="OOTCC",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    onefile=True,
)