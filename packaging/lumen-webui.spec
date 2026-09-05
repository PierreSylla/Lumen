# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

REPO_ROOT = Path(SPECPATH).resolve().parent  # noqa: F821 - PyInstaller global

a = Analysis(  # noqa: F821 - PyInstaller global
    [str(REPO_ROOT / "packaging" / "hue_webui_entry.py")],
    pathex=[str(REPO_ROOT)],
    datas=[(str(REPO_ROOT / "huectl" / "webui_dist"), "webui_dist")],
    excludes=[
        "PySide6", "shiboken6",
        "PyQt6", "qtpy",
        "numpy", "scipy", "matplotlib", "pandas",
    ],
)

a.datas = [d for d in a.datas if "share/icons" not in d[0] and "share/locale" not in d[0]]

pyz = PYZ(a.pure)  # noqa: F821 - PyInstaller global

exe = EXE(  # noqa: F821 - PyInstaller global
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="hue-webui",
    console=True,
)

COLLECT(  # noqa: F821 - PyInstaller global
    exe,
    a.binaries,
    a.datas,
    name="hue-webui",
)
