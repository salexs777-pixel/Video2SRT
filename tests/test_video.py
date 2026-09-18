import io
from collections.abc import Callable
from pathlib import Path
from threading import Event
from unittest.mock import patch

from video2srt.video.ffmpeg_service import build_command, encode, escape_filter_path
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


class FakeProcess:
    def __init__(self, stdout: str, returncode: int = 0, complete_on_eof: bool = True):
        self.stdout = io.StringIO(stdout)
        self.stderr = io.StringIO("")
        self.returncode: int | None = None
        self._final_returncode = returncode
        self.complete_on_eof = complete_on_eof
        self.terminated = False

    def poll(self) -> int | None:
        if self.complete_on_eof and self.stdout.tell() == len(self.stdout.getvalue()):
            self.returncode = self._final_returncode
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self.returncode = self._final_returncode
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = -1

    def kill(self) -> None:
        self.returncode = -9


def run_fake_encode(fake: FakeProcess, progress: Callable[[float], None]) -> None:
    with patch("video2srt.video.ffmpeg_service.subprocess.Popen", return_value=fake):
        encode(["ffmpeg"], 2.0, progress, Event())


def test_encode_ignores_na_progress_and_waits_for_ffmpeg():
    fake = FakeProcess("out_time_us=N/A\nout_time_us=1000000\nprogress=end\n")
    updates: list[float] = []

    run_fake_encode(fake, updates.append)

    assert fake.returncode == 0
    assert updates == [0.5, 1.0]


def test_encode_stops_ffmpeg_when_progress_callback_fails():
    fake = FakeProcess("out_time_us=1000000\n", complete_on_eof=False)

    def fail(_value: float) -> None:
        raise RuntimeError("callback deleted")

    try:
        run_fake_encode(fake, fail)
    except RuntimeError as exc:
        assert str(exc) == "callback deleted"
    else:
        raise AssertionError("Callback error was not propagated")

    assert fake.terminated
