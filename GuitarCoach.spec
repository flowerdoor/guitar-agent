# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

import PySide6
from PySide6.QtCore import QLibraryInfo


qt_bin_dir = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.BinariesPath))
qt_runtime_names = [
    "Qt6Core.dll",
    "Qt6Gui.dll",
    "Qt6Network.dll",
    "Qt6Pdf.dll",
    "Qt6Svg.dll",
    "Qt6Widgets.dll",
]
qt_runtime_binaries = [
    (str(qt_bin_dir / name), ".") for name in qt_runtime_names
]
conda_bin_dir = Path(sys.prefix) / "Library" / "bin"
pyside_dir = Path(PySide6.__file__).resolve().parent
qt_dependency_names = [
    "charset.dll",
    "freetype.dll",
    "glib-2.0-0.dll",
    "graphite2.dll",
    "harfbuzz.dll",
    "iconv.dll",
    "intl-8.dll",
    "libpng16.dll",
    "pcre2-16.dll",
    "pcre2-8.dll",
    "zlib.dll",
    "zstd.dll",
]


def find_qt_dependency(name):
    for directory in (qt_bin_dir, conda_bin_dir, pyside_dir):
        candidate = directory / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find the Qt runtime dependency: {name}")


qt_runtime_binaries.extend(
    (str(find_qt_dependency(name)), ".") for name in qt_dependency_names
)

a = Analysis(
    ["app/__main__.py"],
    pathex=["."],
    binaries=qt_runtime_binaries,
    datas=[
        ("data/knowledge", "data/knowledge"),
        ("lessons", "lessons"),
        ("config.example.json", "."),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "PyQt6",
        "pytest",
        "numpy",
        "matplotlib",
        "IPython",
        "sphinx",
        "docutils",
        "black",
        "pygame",
        "tkinter",
        "_tkinter",
        "PIL",
        "zmq",
        "jedi",
        "astroid",
        "pylint",
        "nbformat",
        "notebook",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GuitarCoach",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GuitarCoach",
)
