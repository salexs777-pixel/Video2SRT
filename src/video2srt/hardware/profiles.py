from __future__ import annotations

from dataclasses import dataclass

from video2srt.core.config import HardwareConfig, WhisperConfig


@dataclass(frozen=True)
class ProcessingProfile:
    whisper: WhisperConfig
    encoder: str
    label: str


def cpu_threads(logical_cores: int) -> int:
    if logical_cores <= 2:
        return 1
    return max(2, min(8, logical_cores - 1))


def select_profile(hw: HardwareConfig) -> ProcessingProfile:
    threads = cpu_threads(hw.logical_cores)
    if hw.cuda_available and hw.vram_gb >= 7.5:
        whisper = WhisperConfig("auto", "large-v3", "cuda", "int8_float16", threads)
        label = f"GPU · {hw.gpu_name or 'NVIDIA'} · высокая точность"
    elif hw.cuda_available and hw.vram_gb >= 3.5:
        whisper = WhisperConfig("auto", "medium", "cuda", "int8_float16", threads)
        label = f"GPU · {hw.gpu_name or 'NVIDIA'} · оптимальная модель"
    elif hw.ram_gb >= 15 and hw.physical_cores >= 4 and hw.logical_cores >= 8:
        whisper = WhisperConfig("auto", "medium", "cpu", "int8", threads)
        label = "CPU · повышенная точность"
    elif hw.ram_gb >= 7 and hw.logical_cores >= 4:
        whisper = WhisperConfig("auto", "small", "cpu", "int8", threads)
        label = "CPU · оптимизированная модель"
    else:
        whisper = WhisperConfig("auto", "base", "cpu", "int8", threads)
        label = "CPU · быстрая модель"

    encoder = next(
        (
            name
            for name, ok in (
                ("h264_nvenc", hw.nvenc_available),
                ("h264_qsv", hw.qsv_available),
                ("h264_amf", hw.amf_available),
            )
            if ok
        ),
        "libx264",
    )
    return ProcessingProfile(whisper, encoder, label)
