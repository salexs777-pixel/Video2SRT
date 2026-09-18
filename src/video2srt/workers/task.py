from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    progress = Signal(int, str, str)
    finished = Signal(object)
    failed = Signal(str)


class TaskWorker(QRunnable):
    def __init__(self, function: Callable, *args):
        super().__init__()
        self.function, self.args = function, args
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.function(*self.args, self.signals.progress.emit)
            self.signals.finished.emit(result)
        except InterruptedError:
            self.signals.failed.emit("Обработка отменена.")
        except Exception as exc:
            logging.getLogger("video2srt").exception("Background task failed")
            self.signals.failed.emit(str(exc) or "Неизвестная ошибка")
