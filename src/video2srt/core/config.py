from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class HardwareConfig:
    windows: str = ""
    architecture: str = ""
    cpu: str = "Unknown CPU"
    physical_cores: int = 1
    logical_cores: int = 1
    ram_gb: float = 0.0
    gpu_vendor: str = ""
    gpu_name: str = ""
    vram_gb: float = 0.0
    cuda_available: bool = False
    nvenc_available: bool = False
    qsv_available: bool = False
    amf_available: bool = False


@dataclass
class WhisperConfig:
    mode: str = "auto"
    model: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    cpu_threads: int = 2


@dataclass
class VideoConfig:
    encoder: str = "libx264"


@dataclass
class AppConfig:
    version: int = 1
    first_run_complete: bool = False
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    video: VideoConfig = field(default_factory=VideoConfig)

    @classmethod
    def from_dict(cls, data: dict) -> AppConfig:
        return cls(
            version=int(data.get("version", 1)),
            first_run_complete=bool(data.get("first_run_complete", False)),
            hardware=HardwareConfig(**data.get("hardware", {})),
            whisper=WhisperConfig(**data.get("whisper", {})),
            video=VideoConfig(**data.get("video", {})),
        )


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        return AppConfig()
    try:
        return AppConfig.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        return AppConfig()


def save_config(config: AppConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(asdict(config), ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def apply_cpu_only_debug_profile(config: AppConfig, cpu_threads: int) -> None:
    """Force a deterministic profile for builds that intentionally omit CUDA."""
    config.first_run_complete = True
    config.hardware.cuda_available = False
    config.hardware.nvenc_available = False
    config.whisper = WhisperConfig(
        mode="auto",
        model="small",
        device="cpu",
        compute_type="int8",
        cpu_threads=max(1, cpu_threads),
    )
    config.video = VideoConfig(encoder="libx264")


def apply_cpu_release_constraints(config: AppConfig, cpu_threads: int) -> None:
    """Keep the selected model and video encoder, but always run Whisper on the CPU."""
    config.hardware.cuda_available = False
    config.whisper.device = "cpu"
    config.whisper.compute_type = "int8"
    config.whisper.cpu_threads = max(1, cpu_threads)
