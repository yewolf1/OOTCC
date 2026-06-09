from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules


def _unique(items):
    return list(dict.fromkeys(items))


hidden_imports = _unique(
    [
        "winrt.windows.foundation",
        "winrt.windows.foundation.collections",
    ]
    + collect_submodules("twitchAPI")
    + collect_submodules("twitch")
    + collect_submodules("ble_hr")
    + collect_submodules("core")
    + collect_submodules("adapter")
    + collect_submodules("ui")
    + collect_submodules("services")
    + collect_submodules("bleak")
    + collect_submodules("bleak.backends.winrt")
    + collect_submodules("winrt")
    + collect_submodules("winrt.windows")
    + collect_submodules("winrt.windows.devices")
    + collect_submodules("winrt.windows.devices.bluetooth")
    + collect_submodules("winrt.windows.devices.bluetooth.advertisement")
    + collect_submodules("winrt.windows.devices.enumeration")
    + collect_submodules("winrt.windows.foundation")
    + collect_submodules("winrt.windows.foundation.collections")
    + collect_submodules("winrt.runtime")
)

winrt_binaries = collect_dynamic_libs("winrt")

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=winrt_binaries,
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
    upx=False,
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
