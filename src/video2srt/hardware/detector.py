from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

import psutil

from video2srt.core.config import HardwareConfig


def _powershell_json(script: str) -> list[dict]:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode:
            return []
        value = json.loads(result.stdout.strip() or "[]")
        return value if isinstance(value, list) else [value]
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return []


def detect_basic() -> HardwareConfig:
    cpu_rows = _powershell_json(
        "Get-CimInstance Win32_Processor | Select-Object -First 1 Name | ConvertTo-Json -Compress"
    )
    gpu_rows = _powershell_json(
        "Get-CimInstance Win32_VideoController | "
        "Select-Object Name,AdapterRAM | ConvertTo-Json -Compress"
    )
    gpu_names = [str(row.get("Name", "")) for row in gpu_rows]
    chosen = next(
        (row for row in gpu_rows if "NVIDIA" in str(row.get("Name", "")).upper()),
        gpu_rows[0] if gpu_rows else {},
    )
    name = str(chosen.get("Name", ""))
    upper = " ".join(gpu_names).upper()
    vendor = (
        "NVIDIA"
        if "NVIDIA" in upper
        else "Intel"
        if "INTEL" in upper
        else "AMD"
        if any(item in upper for item in ("AMD", "RADEON"))
        else ""
    )
    adapter_ram = chosen.get("AdapterRAM") or 0
    try:
        query = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if query.returncode == 0 and query.stdout.strip():
            nvidia_name, memory_mb = query.stdout.splitlines()[0].rsplit(",", 1)
            name = nvidia_name.strip()
            adapter_ram = float(memory_mb.strip()) * 1024**2
            vendor = "NVIDIA"
    except (OSError, ValueError, subprocess.SubprocessError):
        pass

    cpu_name = platform.processor()
    if platform.system() == "Windows":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            ) as key:
                cpu_name = str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    return HardwareConfig(
        windows=platform.platform(),
        architecture=platform.machine(),
        cpu=str(cpu_rows[0].get("Name", "Unknown CPU")).strip() if cpu_rows else cpu_name,
        physical_cores=psutil.cpu_count(logical=False) or 1,
        logical_cores=psutil.cpu_count(logical=True) or 1,
        ram_gb=round(psutil.virtual_memory().total / 1024**3, 1),
        gpu_vendor=vendor,
        gpu_name=name,
        vram_gb=round(float(adapter_ram) / 1024**3, 1) if adapter_ram else 0.0,
    )


def test_cuda_backend(model_path: Path | None = None) -> bool:
    """Real CTranslate2 allocation; model inference is tested when a local model exists."""
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() < 1:
            return False
        if model_path and model_path.exists():
            ctranslate2.models.Whisper(str(model_path), device="cuda", compute_type="int8_float16")
        return True
    except (ImportError, RuntimeError, OSError):
        return False


def test_encoder(ffmpeg: Path, encoder: str) -> bool:
    command = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=320x240:d=0.15:r=10",
        "-an",
        "-c:v",
        encoder,
        "-frames:v",
        "1",
        "-f",
        "null",
        "-",
    ]
    try:
        return (
            subprocess.run(
                command,
                capture_output=True,
                timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            ).returncode
            == 0
        )
    except (OSError, subprocess.SubprocessError):
        return False


def detect_and_validate(ffmpeg: Path) -> HardwareConfig:
    hw = detect_basic()
    hw.cuda_available = test_cuda_backend()
    if hw.cuda_available and not hw.gpu_vendor:
        hw.gpu_vendor = "NVIDIA"
    hw.nvenc_available = test_encoder(ffmpeg, "h264_nvenc")
    hw.qsv_available = test_encoder(ffmpeg, "h264_qsv")
    hw.amf_available = test_encoder(ffmpeg, "h264_amf")
    return hw
