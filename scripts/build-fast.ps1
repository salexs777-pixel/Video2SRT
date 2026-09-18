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
& ".venv\Scripts\python.exe" -m pytest

$Arguments = @("-m", "PyInstaller", "--noconfirm")
if ($Clean) { $Arguments += "--clean" }
$Arguments += "Video2SRT.dev.spec"
& ".venv\Scripts\python.exe" @Arguments

$PortableRoot = "dist\Video2SRT-Debug"
New-Item -ItemType Directory -Force "$PortableRoot\bin", "$PortableRoot\config", "$PortableRoot\models", "$PortableRoot\logs", "$PortableRoot\output" | Out-Null
Copy-Item -LiteralPath "bin\ffmpeg.exe", "bin\ffprobe.exe" -Destination "$PortableRoot\bin" -Force
Copy-Item -LiteralPath "config\glossary.txt" -Destination "$PortableRoot\config\glossary.txt" -Force
Copy-Item -LiteralPath "README.md", "THIRD_PARTY_LICENSES" -Destination $PortableRoot -Force

$Archive = "dist\Video2SRT-Debug-0.1.0.zip"
if (Test-Path $Archive) { Remove-Item -LiteralPath $Archive }
Compress-Archive -LiteralPath $PortableRoot -DestinationPath $Archive -CompressionLevel Fastest
Write-Host "Debug archive: $Archive"
