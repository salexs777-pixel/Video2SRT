# -*- mode: python ; coding: utf-8 -*-
"""Fast CPU-oriented portable build used for UI and pipeline debugging."""

from PyInstaller.utils.hooks import collect_all


datas, binaries, hiddenimports = [], [], []
for package in (
    "faster_whisper",
    "ctranslate2",
    "huggingface_hub",
    "tokenizers",
    "av",
    "psutil",
    "truststore",
):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    ["src/video2srt/app.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=[
        "nvidia",
        "pytest",
        "IPython",
        "jupyter",
        "matplotlib",
        "torch",
        "tensorflow",
        "transformers",
        "PySide6.QtPdf",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtVirtualKeyboard",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Video2SRT-Debug",
    console=False,
    contents_directory="runtime",
)
coll = COLLECT(exe, a.binaries, a.datas, name="Video2SRT-Debug")
