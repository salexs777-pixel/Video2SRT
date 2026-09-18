from pathlib import Path

from video2srt.ui.main_window import MainWindow
from video2srt.video.probe import VideoInfo


def test_background_probe_accepts_worker_progress_callback(monkeypatch):
    expected = VideoInfo(Path("video.mp4"), 1920, 1080, 10.0, 25.0, 123)
    calls = []

    def fake_probe(path, ffprobe):
        calls.append((path, ffprobe))
        return expected

    monkeypatch.setattr("video2srt.ui.main_window.probe_video", fake_probe)

    result = MainWindow._probe_video(
        Path("video.mp4"), Path("ffprobe.exe"), lambda *_args: None
    )

    assert result == expected
    assert calls == [(Path("video.mp4"), Path("ffprobe.exe"))]
