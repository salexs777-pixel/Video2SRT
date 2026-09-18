from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from time import sleep

MODEL_REPOSITORIES = {
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small",
    "medium": "Systran/faster-whisper-medium",
    "large-v3": "Systran/faster-whisper-large-v3",
}

MODEL_SIZES_GB = {"base": 0.15, "small": 0.5, "medium": 1.5, "large-v3": 3.1}


class ModelManager:
    def __init__(self, models_dir: Path):
        self.models_dir = models_dir

    def directory(self, model: str) -> Path:
        return self.models_dir / model

    def is_ready(self, model: str) -> bool:
        target = self.directory(model)
        return (target / "model.bin").exists() and (target / "config.json").exists()

    def download(self, model: str, progress: Callable[[str], None] | None = None) -> Path:
        if model not in MODEL_REPOSITORIES:
            raise ValueError(f"Неизвестная модель: {model}")
        if self.is_ready(model):
            return self.directory(model)
        from huggingface_hub import snapshot_download

        target = self.directory(model)
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                if progress:
                    suffix = f" (попытка {attempt}/3)" if attempt > 1 else ""
                    progress("Загрузка модели распознавания…" + suffix)
                snapshot_download(
                    MODEL_REPOSITORIES[model],
                    local_dir=target,
                    allow_patterns=["*.json", "*.bin", "*.txt", "tokenizer*", "vocabulary.*"],
                )
                if not self.is_ready(model):
                    raise RuntimeError("Загрузка завершилась, но файлы модели неполны.")
                return target
            except Exception as exc:
                last_error = exc
                if attempt < 3:
                    sleep(attempt)
        raise RuntimeError(
            "Не удалось безопасно загрузить модель. Проверьте интернет, VPN/прокси и "
            "доверенные сертификаты Windows. Проверка SSL не отключалась."
        ) from last_error
