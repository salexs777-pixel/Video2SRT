from pathlib import Path

from video2srt.core.config import (
    AppConfig,
    HardwareConfig,
    WhisperConfig,
    apply_cpu_only_debug_profile,
    apply_cpu_release_constraints,
    load_config,
    save_config,
)
from video2srt.ui.settings_window import CPU_LARGE_WARNING, MODEL_GUIDANCE, MODEL_OPTIONS


def test_config_round_trip(tmp_path: Path):
    config = AppConfig(first_run_complete=True, hardware=HardwareConfig(cpu="Test", ram_gb=8))
    path = tmp_path / "config" / "config.json"
    save_config(config, path)
    loaded = load_config(path)
    assert loaded.first_run_complete
    assert loaded.hardware.cpu == "Test"
    assert loaded.hardware.ram_gb == 8


def test_bad_config_returns_defaults(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text("not json", encoding="utf-8")
    assert load_config(path) == AppConfig()


def test_cpu_debug_profile_overrides_saved_gpu_profile():
    config = AppConfig(
        first_run_complete=False,
        hardware=HardwareConfig(cuda_available=True, nvenc_available=True),
        whisper=WhisperConfig(model="large-v3", device="cuda", compute_type="int8_float16"),
    )

    apply_cpu_only_debug_profile(config, 6)

    assert config.first_run_complete
    assert not config.hardware.cuda_available
    assert not config.hardware.nvenc_available
    assert config.whisper == WhisperConfig(
        mode="auto", model="small", device="cpu", compute_type="int8", cpu_threads=6
    )
    assert config.video.encoder == "libx264"


def test_all_whisper_models_are_available_for_manual_selection():
    values = [value for _label, value in MODEL_OPTIONS]

    assert values == ["base", "small", "medium", "large-v3"]
    assert "максимальное качество" in CPU_LARGE_WARNING
    assert "баланс качества и скорости" in MODEL_GUIDANCE["medium"]


def test_cpu_release_keeps_manual_model_and_hardware_video_encoder():
    config = AppConfig(
        first_run_complete=True,
        hardware=HardwareConfig(cuda_available=True, qsv_available=True),
        whisper=WhisperConfig(
            model="large-v3", device="cuda", compute_type="int8_float16", cpu_threads=2
        ),
    )
    config.video.encoder = "h264_qsv"

    apply_cpu_release_constraints(config, 6)

    assert config.whisper.model == "large-v3"
    assert config.whisper.device == "cpu"
    assert config.whisper.compute_type == "int8"
    assert config.whisper.cpu_threads == 6
    assert config.video.encoder == "h264_qsv"
    assert not config.hardware.cuda_available
