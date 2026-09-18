param([switch]$Clean)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Сначала создайте .venv и установите зависимости проекта."
}
if (-not (Test-Path "bin\ffmpeg.exe") -or -not (Test-Path "bin\ffprobe.exe")) {
    throw "FFmpeg не найден. Запустите scripts\fetch_ffmpeg.ps1."
}

$env:PYTHONPATH = "src"
& ".venv\Scripts\python.exe" -m ruff check src tests
if ($LASTEXITCODE -ne 0) { throw "Ruff завершился с кодом $LASTEXITCODE" }
& ".venv\Scripts\python.exe" -m pytest
if ($LASTEXITCODE -ne 0) { throw "Pytest завершился с кодом $LASTEXITCODE" }
& ".venv\Scripts\python.exe" scripts\smoke_test.py
if ($LASTEXITCODE -ne 0) { throw "FFmpeg smoke-test завершился с кодом $LASTEXITCODE" }

$Arguments = @("-m", "PyInstaller", "--noconfirm")
if ($Clean) { $Arguments += "--clean" }
$Arguments += "Video2SRT.cpu.spec"
& ".venv\Scripts\python.exe" @Arguments
if ($LASTEXITCODE -ne 0) { throw "PyInstaller завершился с кодом $LASTEXITCODE" }

$PortableRoot = "dist\Video2SRT-CPU"
New-Item -ItemType Directory -Force "$PortableRoot\bin", "$PortableRoot\config", "$PortableRoot\models", "$PortableRoot\logs", "$PortableRoot\output" | Out-Null
Copy-Item -LiteralPath "bin\ffmpeg.exe", "bin\ffprobe.exe" -Destination "$PortableRoot\bin" -Force
Copy-Item -LiteralPath "config\glossary.txt" -Destination "$PortableRoot\config\glossary.txt" -Force
Copy-Item -LiteralPath "config\CPU_ONLY.marker" -Destination "$PortableRoot\CPU_ONLY" -Force
Copy-Item -LiteralPath "README.md", "THIRD_PARTY_LICENSES" -Destination $PortableRoot -Force

$Iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 7\ISCC.exe",
    "C:\Program Files\Inno Setup 7\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) { throw "Inno Setup 6/7 не найден" }
& $Iscc "installer\Video2SRT-CPU.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup завершился с кодом $LASTEXITCODE" }

Write-Host "CPU installer: installer\output\Video2SRT-CPU-Setup-0.1.0.exe"
