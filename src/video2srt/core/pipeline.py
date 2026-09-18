from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Event

from video2srt.core.config import AppConfig, save_config
from video2srt.core.paths import AppPaths
from video2srt.hardware.profiles import select_profile
from video2srt.subtitles import ass, srt
from video2srt.transcription.glossary import load_glossary
from video2srt.transcription.model_manager import ModelManager
from video2srt.transcription.whisper_service import WhisperService
from video2srt.video.ffmpeg_service import build_command, encode
from video2srt.video.probe import VideoInfo, probe_video

ProgressCallback = Callable[[int, str, str], None]


@dataclass(frozen=True)
class Job:
    source: Path
    directory: Path
    srt_path: Path
    ass_path: Path
    video_path: Path
    info: VideoInfo


class Pipeline:
    def __init__(self, paths: AppPaths, config: AppConfig, logger: logging.Logger):
        self.paths, self.config, self.logger = paths, config, logger
        self.cancel_event = Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def new_job(self, source: Path) -> Job:
        if source.suffix.lower() not in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
            raise ValueError("Выберите видео MP4, MOV, MKV, AVI или WEBM.")
        info = probe_video(source, self.paths.executable("ffprobe"))
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        directory = self.paths.output / f"{source.stem}_{stamp}"
        suffix = 1
        while directory.exists():
            directory = self.paths.output / f"{source.stem}_{stamp}_{suffix}"
            suffix += 1
        directory.mkdir(parents=True)
        stem = source.stem
        return Job(
            source,
            directory,
            directory / f"{stem}.srt",
            directory / f"{stem}.ass",
            directory / f"{stem}_subtitled.mp4",
            info,
        )

    def transcribe(self, job: Job, callback: ProgressCallback) -> Job:
        self.cancel_event.clear()
        callback(10, "Загрузка модели", "Проверка локальной модели")
        manager = ModelManager(self.paths.models)
        model_path = manager.download(
            self.config.whisper.model, lambda text: callback(12, "Загрузка модели", text)
        )
        service = WhisperService(self.config.whisper, model_path)
        glossary = load_glossary(self.paths.config / "glossary.txt")
        callback(15, "Распознавание речи", "Подготовка модели")
        try:
            cues = service.transcribe(
                job.source,
                job.info.duration,
                glossary,
                lambda value: callback(
                    15 + round(value * 48),
                    "Распознавание речи",
                    f"Обработано {value * job.info.duration:.0f} из {job.info.duration:.0f} сек.",
                ),
                self.cancel_event,
            )
        except RuntimeError as exc:
            if str(exc) != "GPU_BACKEND_FAILED":
                raise
            self.logger.warning(
                "CUDA backend failed during model load; falling back to CPU", exc_info=True
            )
            self.config.hardware.cuda_available = False
            profile = select_profile(self.config.hardware)
            self.config.whisper = profile.whisper
            self.config.video.encoder = profile.encoder
            save_config(self.config, self.paths.config / "config.json")
            callback(15, "Распознавание речи", "GPU недоступен — продолжаем на процессоре")
            cues = WhisperService(
                self.config.whisper, manager.download(self.config.whisper.model)
            ).transcribe(
                job.source,
                job.info.duration,
                glossary,
                lambda value: callback(
                    15 + round(value * 48),
                    "Распознавание речи",
                    f"Обработано {value * job.info.duration:.0f} сек.",
                ),
                self.cancel_event,
            )
        callback(65, "Создание SRT", "Сохранение субтитров")
        srt.write(cues, job.srt_path)
        return job

    def burn(self, job: Job, quality: str, callback: ProgressCallback) -> Job:
        self.cancel_event.clear()
        callback(72, "Проверка субтитров", "Проверка сохранённого SRT")
        cues = srt.read(job.srt_path)
        callback(75, "Подготовка видео", "Создание оформленных субтитров")
        ass.write(cues, job.ass_path, job.info.width, job.info.height)
        command = build_command(
            self.paths.executable("ffmpeg"),
            job.source,
            job.ass_path,
            job.video_path,
            self.config.video.encoder,
            quality,
            job.info.width,
            job.info.height,
        )
        self.logger.info("FFmpeg command: %s", " ".join(map(str, command)))
        try:
            encode(
                command,
                job.info.duration,
                lambda value: callback(
                    75 + round(value * 24), "Кодирование видео", f"Готово {value:.0%}"
                ),
                self.cancel_event,
            )
        except Exception:
            if job.video_path.exists():
                job.video_path.unlink()
            if self.config.video.encoder != "libx264" and not self.cancel_event.is_set():
                self.logger.warning("Hardware encoder failed; retrying with libx264", exc_info=True)
                self.config.video.encoder = "libx264"
                save_config(self.config, self.paths.config / "config.json")
                command = build_command(
                    self.paths.executable("ffmpeg"),
                    job.source,
                    job.ass_path,
                    job.video_path,
                    "libx264",
                    quality,
                    job.info.width,
                    job.info.height,
                )
                encode(
                    command,
                    job.info.duration,
                    lambda value: callback(
                        75 + round(value * 24), "Кодирование видео", f"Готово {value:.0%}"
                    ),
                    self.cancel_event,
                )
            else:
                raise
        callback(100, "Готово", str(job.video_path))
        return job
