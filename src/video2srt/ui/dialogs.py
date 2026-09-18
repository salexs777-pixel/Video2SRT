from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QDialog, QLabel, QMessageBox, QProgressBar, QPushButton, QVBoxLayout

from video2srt.core.config import AppConfig, save_config
from video2srt.core.paths import AppPaths
from video2srt.hardware.detector import detect_and_validate
from video2srt.hardware.profiles import select_profile
from video2srt.workers.task import TaskWorker


class FirstRunDialog(QDialog):
    def __init__(self, paths: AppPaths, config: AppConfig, parent=None, cpu_only: bool = False):
        super().__init__(parent)
        self.paths, self.config = paths, config
        self.cpu_only = cpu_only
        self.setWindowTitle("Первоначальная настройка Video2SRT")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Video2SRT настраивается для вашего компьютера</h2>"))
        layout.addWidget(
            QLabel("Видео и аудио обрабатываются локально и не отправляются в облако.")
        )
        self.status = QLabel("Анализ процессора и памяти…")
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)
        self.continue_button = QPushButton("Продолжить")
        self.continue_button.setEnabled(False)
        self.continue_button.clicked.connect(self.accept)
        layout.addWidget(self.continue_button)
        self.worker = TaskWorker(self._detect)
        self.worker.signals.finished.connect(self._complete)
        self.worker.signals.failed.connect(self._failed)
        QThreadPool.globalInstance().start(self.worker)

    def _detect(self, _progress):
        hardware = detect_and_validate(self.paths.executable("ffmpeg"))
        return hardware, select_profile(hardware)

    def _complete(self, result) -> None:
        hardware, profile = result
        if self.cpu_only:
            hardware = replace(hardware, cuda_available=False)
            profile = select_profile(hardware)
        self.config.hardware = hardware
        self.config.whisper = profile.whisper
        self.config.video.encoder = profile.encoder
        self.config.first_run_complete = True
        save_config(self.config, self.paths.config / "config.json")
        encoder = {
            "h264_nvenc": "NVIDIA Hardware Encoder",
            "h264_qsv": "Intel Quick Sync",
            "h264_amf": "AMD Hardware Encoder",
            "libx264": "Процессор",
        }[profile.encoder]
        self.status.setText(
            f"<b>Оптимальная конфигурация</b><br><br>Распознавание: {profile.label}<br>"
            f"Видео: {encoder}"
        )
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.continue_button.setEnabled(True)

    def _failed(self, message: str) -> None:
        self.config.first_run_complete = True
        save_config(self.config, self.paths.config / "config.json")
        self.status.setText(
            "Автоматическая проверка не завершена. Будет использован безопасный режим CPU."
        )
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.continue_button.setEnabled(True)


def show_error(parent, message: str) -> None:
    friendly = message
    if "No such file" in message or "не удается найти" in message:
        friendly = "Не найден FFmpeg. Переустановите Video2SRT или проверьте папку bin."
    QMessageBox.critical(parent, "Video2SRT", friendly)
