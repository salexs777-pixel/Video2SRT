from pathlib import Path

from video2srt.video.ffmpeg_service import build_command, escape_filter_path
from video2srt.video.profiles import encoder_args, scale_filter


def test_original_quality_cpu_command():
    command = build_command(
        Path("ffmpeg.exe"),
        Path("in.mp4"),
        Path("sub.ass"),
        Path("out.mp4"),
        "libx264",
        "original",
        1920,
        1080,
    )
    assert ["-crf", "18"] == command[command.index("-crf") : command.index("-crf") + 2]
    assert "scale=" not in command[command.index("-vf") + 1]
    assert "+faststart" in command


def test_internet_quality_downscales_only_large_video():
    assert scale_filter(3840, 2160, "internet") is not None
    assert scale_filter(1920, 1080, "internet") is None
    assert scale_filter(1080, 1920, "internet") is None


def test_all_encoder_profiles():
    for encoder in ("h264_nvenc", "h264_qsv", "h264_amf", "libx264"):
        args = encoder_args(encoder, "internet")
        assert "23" in args
        assert encoder in args


def test_windows_filter_path_is_escaped():
    escaped = escape_filter_path(Path("C:/A Folder/test.ass"))
    assert r"C\:" in escaped
    assert "A Folder" in escaped
