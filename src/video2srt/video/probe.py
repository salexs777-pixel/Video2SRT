from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoInfo:
    path: Path
    width: int
    height: int
    duration: float
    fps: float
    size_bytes: int

    @property
    def orientation(self) -> str:
        return "Вертикальное видео" if self.height > self.width else "Горизонтальное видео"


def _ratio(value: str) -> float:
    try:
        numerator, denominator = value.split("/", 1)
        return float(numerator) / float(denominator) if float(denominator) else 0.0
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe_video(path: Path, ffprobe: Path) -> VideoInfo:
    command = [
        str(ffprobe),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate:format=duration,size",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
    )
    if result.returncode:
        raise ValueError("Не удалось прочитать видео. Проверьте формат и целостность файла.")
    data = json.loads(result.stdout)
    if not data.get("streams"):
        raise ValueError("В файле не найден видеопоток.")
    stream, fmt = data["streams"][0], data.get("format", {})
    return VideoInfo(
        path,
        int(stream["width"]),
        int(stream["height"]),
        float(fmt.get("duration", 0)),
        _ratio(stream.get("avg_frame_rate", "0/1")),
        int(fmt.get("size", path.stat().st_size)),
    )
