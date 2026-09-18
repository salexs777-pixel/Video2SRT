from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from video2srt.core.config import AppConfig
from video2srt.core.paths import AppPaths
from video2srt.core.pipeline import Job, Pipeline
from video2srt.transcription.model_manager import MODEL_SIZES_GB, ModelManager
from video2srt.ui.dialogs import FirstRunDialog, show_error
from video2srt.ui.settings_window import SettingsDialog
from video2srt.video.probe import VideoInfo, probe_video
from video2srt.workers.task import TaskWorker


class MainWindow(QMainWindow):
    def __init__(self, paths: AppPaths, config: AppConfig, pipeline: Pipeline):
        super().__init__()
        self.paths, self.config, self.pipeline = paths, config, pipeline
        self.source: Path | None = None
        self.job: Job | None = None
        self.setWindowTitle("Video2SRT")
        self.setMinimumSize(680, 500)
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("<h1>Video2SRT</h1><p>Русские субтитры для вашего видео</p>"))
        row = QHBoxLayout()
        self.file_label = QLabel("Видео не выбрано")
        self.file_label.setWordWrap(True)
        choose = QPushButton("Выбрать видео")
        choose.clicked.connect(self.choose_video)
        row.addWidget(self.file_label, 1)
        row.addWidget(choose)
        layout.addLayout(row)
        self.info_label = QLabel("")
        layout.addWidget(self.info_label)
        layout.addWidget(QLabel("<b>Качество выходного видео</b>"))
        self.original = QRadioButton("Оригинальное качество")
        self.original.setChecked(True)
        self.internet = QRadioButton("Для публикации в интернете")
        layout.addWidget(self.original)
        layout.addWidget(self.internet)
        self.mode_label = QLabel(self._mode_text())
        self.mode_label.setStyleSheet("color:#555;padding:8px")
        layout.addWidget(self.mode_label)
        self.start_button = QPushButton("НАЧАТЬ")
        self.start_button.setEnabled(False)
        self.start_button.setMinimumHeight(48)
        self.start_button.clicked.connect(self.start)
        layout.addWidget(self.start_button)
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.stage = QLabel("Текущий этап: ожидание")
        layout.addWidget(self.stage)
        self.status = QLabel("")
        layout.addWidget(self.status)
        controls = QHBoxLayout()
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.pipeline.cancel)
        self.open_video = QPushButton("Открыть видео")
        self.open_video.setVisible(False)
        self.open_video.clicked.connect(
            lambda: os.startfile(self.job.video_path) if self.job else None
        )
        self.open_folder = QPushButton("Открыть папку результата")
        self.open_folder.setVisible(False)
        self.open_folder.clicked.connect(
            lambda: os.startfile(self.job.directory) if self.job else None
        )
        controls.addWidget(self.cancel_button)
        controls.addStretch()
        controls.addWidget(self.open_video)
        controls.addWidget(self.open_folder)
        layout.addLayout(controls)
        layout.addStretch()
        self.setCentralWidget(central)
        settings = QAction("Настройки", self)
        settings.triggered.connect(self.settings)
        self.menuBar().addAction(settings)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self.config.first_run_complete:
            FirstRunDialog(self.paths, self.config, self).exec()
            self.mode_label.setText(self._mode_text())

    def _mode_text(self) -> str:
        model = {
            "base": "Быстрая",
            "small": "Оптимизированная",
            "medium": "Точная",
            "large-v3": "Высокая точность",
        }.get(self.config.whisper.model, "Авто")
        device = "GPU" if self.config.whisper.device == "cuda" else "CPU"
        extra = " Обработка может занять больше времени." if device == "CPU" else ""
        return f"Режим обработки: {device} · {model}.{extra}"

    def choose_video(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self, "Выберите видео", "", "Видео (*.mp4 *.mov *.mkv *.avi *.webm)"
        )
        if not selected:
            return
        self.source = Path(selected)
        self.file_label.setText(self.source.name)
        self.info_label.setText("Чтение параметров видео…")
        self.start_button.setEnabled(False)
        worker = TaskWorker(
            self._probe_video, self.source, self.paths.executable("ffprobe")
        )
        worker.signals.finished.connect(self._video_probed)
        worker.signals.failed.connect(self._probe_failed)
        QThreadPool.globalInstance().start(worker)

    @staticmethod
    def _probe_video(path: Path, ffprobe: Path, _progress_callback) -> VideoInfo:
        """Adapt the two-argument probe service to TaskWorker's progress contract."""
        return probe_video(path, ffprobe)

    @staticmethod
    def _video_summary(info: VideoInfo) -> str:
        total_seconds = max(0, round(info.duration))
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        duration = (
            f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            if hours
            else f"{minutes:02d}:{seconds:02d}"
        )
        return (
            f"{info.width} × {info.height} · {info.orientation} · {duration} · "
            f"{info.fps:.2f} FPS · {info.size_bytes / 1024**2:.1f} MB"
        )

    def _video_probed(self, info: VideoInfo) -> None:
        if self.source != info.path:
            return
        self.info_label.setText(self._video_summary(info))
        self.start_button.setEnabled(True)

    def _probe_failed(self, message: str) -> None:
        self.source = None
        self.start_button.setEnabled(False)
        self.info_label.setText("")
        show_error(self, message)

    def start(self) -> None:
        if not self.source:
            return
        manager = ModelManager(self.paths.models)
        model = self.config.whisper.model
        if not manager.is_ready(model):
            size = MODEL_SIZES_GB.get(model, 1.0)
            answer = QMessageBox.question(
                self,
                "Загрузка модели",
                f"Для распознавания нужно загрузить модель (примерно {size:g} ГБ). Продолжить?",
            )
            if answer != QMessageBox.Yes:
                return
        self._busy(True)
        worker = TaskWorker(self._create_and_transcribe)
        worker.signals.progress.connect(self._progress)
        worker.signals.finished.connect(self._srt_ready)
        worker.signals.failed.connect(self._failed)
        QThreadPool.globalInstance().start(worker)

    def _create_and_transcribe(self, callback):
        callback(5, "Проверка видео", "Чтение параметров файла")
        job = self.pipeline.new_job(self.source)
        return self.pipeline.transcribe(job, callback)

    def _srt_ready(self, job: Job) -> None:
        self.job = job
        info = job.info
        self.info_label.setText(self._video_summary(info))
        box = QMessageBox(self)
        box.setWindowTitle("Субтитры созданы")
        box.setText("Субтитры созданы. Хотите проверить и исправить текст?")
        edit = box.addButton("Редактировать", QMessageBox.AcceptRole)
        box.addButton("Продолжить без редактирования", QMessageBox.DestructiveRole)
        box.exec()
        if box.clickedButton() == edit:
            os.startfile(job.srt_path)
            QMessageBox.information(
                self,
                "Редактирование субтитров",
                "Внесите изменения в файл, сохраните его и нажмите ОК.\n"
                "Распознавание повторно запускаться не будет.",
            )
        self._start_burn()

    def _start_burn(self) -> None:
        quality = "original" if self.original.isChecked() else "internet"
        worker = TaskWorker(self.pipeline.burn, self.job, quality)
        worker.signals.progress.connect(self._progress)
        worker.signals.finished.connect(self._complete)
        worker.signals.failed.connect(self._failed)
        QThreadPool.globalInstance().start(worker)

    def _progress(self, value: int, stage: str, status: str) -> None:
        self.progress.setValue(value)
        self.stage.setText(f"Текущий этап: {stage}")
        self.status.setText(status)

    def _complete(self, job: Job) -> None:
        self.job = job
        self._busy(False)
        self.progress.setValue(100)
        self.open_video.setVisible(True)
        self.open_folder.setVisible(True)
        QMessageBox.information(self, "Video2SRT", f"Готово.\n\nВыходной файл:\n{job.video_path}")

    def _failed(self, message: str) -> None:
        self._busy(False)
        show_error(self, message)

    def _busy(self, busy: bool) -> None:
        self.start_button.setEnabled(not busy and self.source is not None)
        self.cancel_button.setEnabled(busy)

    def settings(self) -> None:
        def redetect():
            FirstRunDialog(self.paths, self.config, self).exec()
            self.mode_label.setText(self._mode_text())

        SettingsDialog(self.paths, self.config, redetect, self).exec()
        self.mode_label.setText(self._mode_text())
