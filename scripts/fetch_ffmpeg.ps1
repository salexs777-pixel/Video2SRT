$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Archive = Join-Path $env:TEMP "video2srt-ffmpeg-9.0.1.zip"
$Extract = Join-Path $env:TEMP "video2srt-ffmpeg-9.0.1"
$Url = "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.1-essentials_build.zip"
# Published by the build provider alongside this pinned archive.
$ExpectedSha256 = "fec81ae03971d9dd4be3ebe02e263bd2ec1d789483f931bdba5f5715e65da2e9"

Invoke-WebRequest -Uri $Url -OutFile $Archive
$Actual = (Get-FileHash -Algorithm SHA256 $Archive).Hash.ToLowerInvariant()
if ($Actual -ne $ExpectedSha256.ToLowerInvariant()) { throw "FFmpeg SHA-256 mismatch" }
if (Test-Path $Extract) { Remove-Item -LiteralPath $Extract -Recurse -Force }
Expand-Archive -LiteralPath $Archive -DestinationPath $Extract
$SourceBin = Get-ChildItem -Path $Extract -Directory | Select-Object -First 1 | ForEach-Object { Join-Path $_.FullName "bin" }
Copy-Item -LiteralPath (Join-Path $SourceBin "ffmpeg.exe") -Destination (Join-Path $ProjectRoot "bin\ffmpeg.exe")
Copy-Item -LiteralPath (Join-Path $SourceBin "ffprobe.exe") -Destination (Join-Path $ProjectRoot "bin\ffprobe.exe")
