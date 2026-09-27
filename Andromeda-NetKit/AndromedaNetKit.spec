from pathlib import Path
import sys


project_dir = Path(SPECPATH)

a = Analysis(
    [str(project_dir / "main.py")],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        (str(project_dir / "assets" / "network_diagnostics.png"), "assets"),
        (str(project_dir / "assets" / "network_background.png"), "assets"),
    ],
    hiddenimports=["PIL._tkinter_finder"],
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
    name="AndromedaNetKit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=sys.platform.startswith("linux"),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_dir / "assets" / "network_diagnostics.ico"),
)
