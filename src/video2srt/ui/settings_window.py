from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QVBoxLayout,
)

from video2srt.core.config import AppConfig, save_config
from video2srt.core.paths import AppPaths


class SettingsDialog(QDialog):
    def __init__(self, paths: AppPaths, config: AppConfig, redetect, parent=None):
        super().__init__(parent)
        self.paths, self.config = paths, config
        self.setWindowTitle("Настройки")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.mode = QComboBox()
        self.mode.addItems(["Автоматически", "Быстро", "Повышенная точность"])
        self.mode.setCurrentIndex({"auto": 0, "fast": 1, "high": 2}.get(config.whisper.mode, 0))
        form.addRow("Качество распознавания:", self.mode)
        layout.addLayout(form)
        self.advanced_check = QCheckBox("Расширенные настройки")
        layout.addWidget(self.advanced_check)
        self.advanced = QGroupBox()
        advanced_form = QFormLayout(self.advanced)
        self.model = QComboBox()
        self.model.addItems(["Auto", "Base", "Small", "Medium", "Large-v3"])
        self.device = QComboBox()
        self.device.addItems(["Auto", "GPU", "CPU"])
        advanced_form.addRow("Whisper model:", self.model)
        advanced_form.addRow("Processing device:", self.device)
        self.advanced.setVisible(False)
        self.advanced_check.toggled.connect(self.advanced.setVisible)
        layout.addWidget(self.advanced)
        redetect_button = QPushButton("Повторно определить конфигурацию компьютера")
        redetect_button.clicked.connect(redetect)
        layout.addWidget(redetect_button)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self) -> None:
        self.config.whisper.mode = ("auto", "fast", "high")[self.mode.currentIndex()]
        if self.advanced_check.isChecked():
            selected_model = self.model.currentText().lower()
            if selected_model != "auto":
                self.config.whisper.model = selected_model
            selected_device = self.device.currentText().lower()
            if selected_device != "auto":
                self.config.whisper.device = "cuda" if selected_device == "gpu" else "cpu"
                self.config.whisper.compute_type = (
                    "int8_float16" if selected_device == "gpu" else "int8"
                )
        save_config(self.config, self.paths.config / "config.json")
        self.accept()
