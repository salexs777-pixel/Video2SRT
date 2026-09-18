from pathlib import Path

import pytest

from video2srt.subtitles.srt import dumps, format_timestamp, loads, parse_timestamp, read, write
from video2srt.transcription.segmentation import Cue


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "00:00:00,000"),
        (1.234, "00:00:01,234"),
        (3661.999, "01:01:01,999"),
    ],
)
def test_format_timestamp(seconds, expected):
    assert format_timestamp(seconds) == expected
    assert parse_timestamp(expected) == pytest.approx(seconds, abs=0.001)


def test_srt_round_trip(tmp_path: Path):
    cues = [Cue(0, 1.5, "Привет"), Cue(2, 4, "Две\nстроки")]
    path = tmp_path / "test.srt"
    write(cues, path)
    assert read(path) == cues
    assert dumps(cues).startswith("1\n00:00:00,000 --> 00:00:01,500")


@pytest.mark.parametrize(
    "content",
    [
        "1\nwrong --> 00:00:01,000\nТекст",
        "1\n00:00:02,000 --> 00:00:01,000\nТекст",
        "one\n00:00:00,000 --> 00:00:01,000\nТекст",
        "1\n00:00:00,000 --> 00:00:01,000\n",
    ],
)
def test_invalid_srt(content):
    with pytest.raises(ValueError):
        loads(content)
