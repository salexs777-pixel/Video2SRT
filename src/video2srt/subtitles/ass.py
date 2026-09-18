from __future__ import annotations

from pathlib import Path

from video2srt.transcription.segmentation import Cue


def escape_text(text: str) -> str:
    return (
        text.replace("\\", r"\e")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("\r\n", r"\N")
        .replace("\n", r"\N")
    )


def ass_timestamp(seconds: float) -> str:
    centiseconds = max(0, round(seconds * 100))
    hours, centiseconds = divmod(centiseconds, 360_000)
    minutes, centiseconds = divmod(centiseconds, 6_000)
    secs, centiseconds = divmod(centiseconds, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def font_size(width: int, height: int) -> int:
    return max(24, min(64, round(min(width, height) * 0.04)))


def margin_v(width: int, height: int) -> int:
    return max(24, min(100, round(min(width, height) * 0.055)))


def dumps(cues: list[Cue], width: int, height: int) -> str:
    size, margin = font_size(width, height), margin_v(width, height)
    style_format = ", ".join(
        (
            "Name",
            "Fontname",
            "Fontsize",
            "PrimaryColour",
            "SecondaryColour",
            "OutlineColour",
            "BackColour",
            "Bold",
            "Italic",
            "Underline",
            "StrikeOut",
            "ScaleX",
            "ScaleY",
            "Spacing",
            "Angle",
            "BorderStyle",
            "Outline",
            "Shadow",
            "Alignment",
            "MarginL",
            "MarginR",
            "MarginV",
            "Encoding",
        )
    )
    style = ",".join(
        (
            "Default",
            "Arial",
            str(size),
            "&H00000000",
            "&H00000000",
            "&H00FFFFFF",
            "&H00FFFFFF",
            "0",
            "0",
            "0",
            "0",
            "100",
            "100",
            "0",
            "0",
            "3",
            "8",
            "0",
            "2",
            "30",
            "30",
            str(margin),
            "1",
        )
    )
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: {style_format}
Style: {style}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = "".join(
        f"Dialogue: 0,{ass_timestamp(c.start)},{ass_timestamp(c.end)},"
        f"Default,,0,0,0,,{escape_text(c.text)}\n"
        for c in cues
    )
    return header + events


def write(cues: list[Cue], path: Path, width: int, height: int) -> None:
    path.write_text(dumps(cues, width, height), encoding="utf-8-sig")
