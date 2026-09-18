from pathlib import Path

from video2srt.core.config import AppConfig, HardwareConfig, load_config, save_config


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
