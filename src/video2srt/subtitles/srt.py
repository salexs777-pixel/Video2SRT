from __future__ import annotations

import re
from pathlib import Path

from video2srt.transcription.segmentation import Cue

TIMESTAMP = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")


def format_timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def parse_timestamp(value: str) -> float:
    match = TIMESTAMP.match(value.strip())
    if not match:
        raise ValueError(f"Некорректная временная метка: {value}")
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    if minutes > 59 or seconds > 59:
        raise ValueError(f"Некорректная временная метка: {value}")
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def dumps(cues: list[Cue]) -> str:
    return (
        "\n\n".join(
            f"{index}\n{format_timestamp(cue.start)} --> {format_timestamp(cue.end)}\n{cue.text}"
            for index, cue in enumerate(cues, 1)
        )
        + "\n"
    )


def loads(content: str) -> list[Cue]:
    blocks = re.split(r"\r?\n\s*\r?\n", content.strip())
    cues: list[Cue] = []
    for position, block in enumerate(blocks, 1):
        lines = block.splitlines()
        if len(lines) < 3 or not lines[0].strip().isdigit() or "-->" not in lines[1]:
            raise ValueError(f"Ошибка в блоке субтитров №{position}")
        start_raw, end_raw = (item.strip() for item in lines[1].split("-->", 1))
        start, end = parse_timestamp(start_raw), parse_timestamp(end_raw)
        if end <= start:
            raise ValueError(f"Конец раньше начала в блоке №{position}")
        text = "\n".join(line.strip() for line in lines[2:] if line.strip())
        if not text:
            raise ValueError(f"Нет текста в блоке №{position}")
        cues.append(Cue(start, end, text))
    return cues


def write(cues: list[Cue], path: Path) -> None:
    path.write_text(dumps(cues), encoding="utf-8-sig")


def read(path: Path) -> list[Cue]:
    return loads(path.read_text(encoding="utf-8-sig"))
