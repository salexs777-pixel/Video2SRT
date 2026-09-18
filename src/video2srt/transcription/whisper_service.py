from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import Event

from video2srt.core.config import WhisperConfig
from video2srt.transcription.segmentation import Cue, Word, segment_words


class WhisperService:
    def __init__(self, config: WhisperConfig, model_path: Path):
        self.config = config
        self.model_path = model_path

    def transcribe(
        self,
        media: Path,
        duration: float,
        glossary: str | None,
        progress: Callable[[float], None],
        cancel: Event,
    ) -> list[Cue]:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("Компонент распознавания не установлен.") from exc

        try:
            model = WhisperModel(
                str(self.model_path),
                device=self.config.device,
                compute_type=self.config.compute_type,
                cpu_threads=self.config.cpu_threads,
                local_files_only=True,
            )
            segments, _ = model.transcribe(
                str(media),
                language="ru",
                vad_filter=True,
                word_timestamps=True,
                initial_prompt=glossary,
                beam_size=5,
            )
            words: list[Word] = []
            for segment in segments:
                if cancel.is_set():
                    raise InterruptedError("Обработка отменена")
                if segment.words:
                    words.extend(
                        Word(word.word.strip(), float(word.start), float(word.end))
                        for word in segment.words
                        if word.word.strip()
                    )
                progress(min(1.0, float(segment.end) / duration) if duration else 0.0)
            return segment_words(words)
        except InterruptedError:
            raise
        except Exception as exc:
            if self.config.device == "cuda":
                raise RuntimeError("GPU_BACKEND_FAILED") from exc
            raise RuntimeError("Не удалось загрузить локальную модель распознавания.") from exc
