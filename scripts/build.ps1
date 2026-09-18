param([switch]$SkipDownload)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) { python -m venv .venv }
& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -e ".[dev]"

if (-not $SkipDownload -and -not (Test-Path "bin\ffmpeg.exe")) {
    & "$PSScriptRoot\fetch_ffmpeg.ps1"
}

$env:PYTHONPATH = "src"
& ".venv\Scripts\python.exe" -m ruff check src tests
& ".venv\Scripts\python.exe" -m pytest
& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean Video2SRT.spec

$Iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 7\ISCC.exe",
    "C:\Program Files\Inno Setup 7\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) { throw "Inno Setup 6/7 не найден" }
& $Iscc "installer\Video2SRT.iss"
