from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from threading import Event

from video2srt.video.profiles import encoder_args, scale_filter


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        process.wait()
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def escape_filter_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def build_command(
    ffmpeg: Path,
    source: Path,
    ass: Path,
    destination: Path,
    encoder: str,
    quality: str,
    width: int,
    height: int,
) -> list[str]:
    filters = [f"ass='{escape_filter_path(ass)}'"]
    scale = scale_filter(width, height, quality)
    if scale:
        filters.append(scale)
    return [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-vf",
        ",".join(filters),
        *encoder_args(encoder, quality),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        "-progress",
        "pipe:1",
        "-nostats",
        str(destination),
    ]


def encode(
    command: list[str], duration: float, progress: Callable[[float], None], cancel: Event
) -> None:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert process.stdout is not None
    try:
        while True:
            if cancel.is_set():
                raise InterruptedError("Обработка отменена")
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            key, _, value = line.strip().partition("=")
            if key in {"out_time_us", "out_time_ms"} and duration > 0:
                try:
                    elapsed = int(value)
                except ValueError:
                    # FFmpeg may emit out_time_us=N/A near the end of a valid encode.
                    continue
                progress(min(1.0, max(0.0, elapsed / 1_000_000 / duration)))
        returncode = process.wait()
        error = process.stderr.read()[-2000:] if process.stderr else ""
        if returncode:
            raise RuntimeError(f"FFmpeg не смог создать видео. {error}")
        progress(1.0)
    except BaseException:
        _stop_process(process)
        raise
    finally:
        process.stdout.close()
        if process.stderr:
            process.stderr.close()
