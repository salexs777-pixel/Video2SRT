# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []
for package in ("faster_whisper", "ctranslate2", "huggingface_hub", "tokenizers", "av", "psutil", "nvidia"):
    d, b, h = collect_all(package)
    datas += d; binaries += b; hiddenimports += h

datas += [("THIRD_PARTY_LICENSES", ".")]

a = Analysis(["src/video2srt/app.py"], pathex=["src"], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports, noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Video2SRT", console=False,
          contents_directory="runtime")
coll = COLLECT(exe, a.binaries, a.datas, name="Video2SRT")
