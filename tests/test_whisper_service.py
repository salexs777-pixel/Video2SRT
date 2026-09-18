import sys
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import pytest

from video2srt.core.config import WhisperConfig
from video2srt.transcription.whisper_service import WhisperService


def test_lazy_cuda_failure_is_converted_to_fallback_signal(monkeypatch):
    class FakeWhisperModel:
        def __init__(self, *_args, **_kwargs):
            pass

        def transcribe(self, *_args, **_kwargs):
            def failing_segments():
                raise RuntimeError("Library cublas64_12.dll is not found")
                yield

            return failing_segments(), None

    monkeypatch.setitem(
        sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=FakeWhisperModel)
    )
    service = WhisperService(
        WhisperConfig(model="small", device="cuda", compute_type="int8_float16"),
        Path("model"),
    )

    with pytest.raises(RuntimeError, match="GPU_BACKEND_FAILED"):
        service.transcribe(Path("video.mp4"), 10.0, None, lambda _value: None, Event())
