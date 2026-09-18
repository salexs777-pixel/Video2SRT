from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from video2srt.core.config import AppConfig, save_config
from video2srt.core.paths import AppPaths

MODEL_OPTIONS = (
    ("Base — минимальные требования", "base"),
    ("Small — быстрее", "small"),
    ("Medium — баланс качества и скорости", "medium"),
    ("Large-v3 — максимальная точность", "large-v3"),
)

MODEL_GUIDANCE = {
    "base": "Минимальное потребление памяти и самая высокая скорость.",
    "small": "Заметно быстрее, но вероятность ошибок выше.",
    "medium": "Хороший баланс качества и скорости.",
    "large-v3": "Максимальная точность, но более медленная обработка.",
}

CPU_LARGE_WARNING = (
    "Large-v3 обеспечивает максимальное качество, но на CPU требует много памяти "
    "и может работать медленно."
)


class SettingsDialog(QDialog):
    def __init__(
        self, paths: AppPaths, config: AppConfig, redetect, parent=None, cpu_only: bool = False
    ):
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
        for label, value in MODEL_OPTIONS:
            self.model.addItem(label, value)
        self.model.setCurrentIndex(max(0, self.model.findData(config.whisper.model)))
        self.device = QComboBox()
        if not cpu_only:
            self.device.addItem("GPU (NVIDIA CUDA)", "cuda")
        self.device.addItem("CPU", "cpu")
        self.device.setCurrentIndex(max(0, self.device.findData(config.whisper.device)))
        self.model_note = QLabel()
        self.model_note.setWordWrap(True)
        self.model.currentIndexChanged.connect(self._update_model_note)
        self.device.currentIndexChanged.connect(self._update_model_note)
        advanced_form.addRow("Модель Whisper:", self.model)
        advanced_form.addRow("Устройство:", self.device)
        advanced_form.addRow("", self.model_note)
        self._update_model_note()
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

    def _selected_model(self) -> str:
        return str(self.model.currentData())

    def _selected_device(self) -> str:
        return str(self.device.currentData())

    def _update_model_note(self) -> None:
        model = self._selected_model()
        text = MODEL_GUIDANCE[model]
        if model == "large-v3" and self._selected_device() == "cpu":
            text = CPU_LARGE_WARNING
        self.model_note.setText(text)

    def _save(self) -> None:
        self.config.whisper.mode = ("auto", "fast", "high")[self.mode.currentIndex()]
        if self.advanced_check.isChecked():
            selected_model = self._selected_model()
            selected_device = self._selected_device()
            self.config.whisper.model = selected_model
            self.config.whisper.device = selected_device
            self.config.whisper.compute_type = (
                "int8_float16" if selected_device == "cuda" else "int8"
            )
            if selected_model == "large-v3" and selected_device == "cpu":
                QMessageBox.warning(self, "Large-v3 на CPU", CPU_LARGE_WARNING)
        save_config(self.config, self.paths.config / "config.json")
        self.accept()
