from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


def wrap_text(text: str, width: int = 42, max_lines: int = 2) -> str:
    words = text.split()
    if not words:
        return ""
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > width and len(lines) < max_lines - 1:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    return "\n".join(lines)


def segment_words(words: list[Word], max_chars: int = 84, max_duration: float = 6.0) -> list[Cue]:
    cues: list[Cue] = []
    bucket: list[Word] = []
    punctuation = (".", "!", "?", "…")

    def flush() -> None:
        if bucket:
            text = " ".join(word.text.strip() for word in bucket).strip()
            cues.append(
                Cue(bucket[0].start, max(bucket[-1].end, bucket[0].start + 0.8), wrap_text(text))
            )
            bucket.clear()

    for word in words:
        candidate = " ".join([*(item.text.strip() for item in bucket), word.text.strip()]).strip()
        duration = word.end - bucket[0].start if bucket else 0
        if bucket and (len(candidate) > max_chars or duration > max_duration):
            flush()
        bucket.append(word)
        duration_now = word.end - bucket[0].start
        if duration_now >= 1.2 and word.text.rstrip().endswith(punctuation):
            flush()
    flush()
    return cues
