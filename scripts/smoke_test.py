"""Offline subtitle/video smoke test using the bundled FFmpeg (no model download)."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from threading import Event

from video2srt.subtitles import ass, srt
from video2srt.transcription.segmentation import Cue
from video2srt.video.ffmpeg_service import build_command, encode
from video2srt.video.probe import probe_video


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ffmpeg, ffprobe = root / "bin/ffmpeg.exe", root / "bin/ffprobe.exe"
    if not ffmpeg.exists() or not ffprobe.exists():
        raise SystemExit("Сначала добавьте FFmpeg в bin")
    with tempfile.TemporaryDirectory(prefix="video2srt-smoke-") as directory:
        work = Path(directory)
        source = work / "portrait.mp4"
        subprocess.run(
            [
                str(ffmpeg),
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=360x640:r=25",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=48000",
                "-t",
                "2",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                str(source),
            ],
            check=True,
            capture_output=True,
        )
        info = probe_video(source, ffprobe)
        cues = [Cue(0.2, 1.8, "Проверка\nсубтитров")]
        srt_path, ass_path, result = work / "test.srt", work / "test.ass", work / "result.mp4"
        srt.write(cues, srt_path)
        ass.write(srt.read(srt_path), ass_path, info.width, info.height)
        command = build_command(
            ffmpeg, source, ass_path, result, "libx264", "original", info.width, info.height
        )
        encode(command, info.duration, lambda _: None, Event())
        final = probe_video(result, ffprobe)
        assert final.width == 360 and final.height == 640 and result.stat().st_size > 1000
        print("SMOKE PASS", result.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
