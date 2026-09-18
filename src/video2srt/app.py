from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from video2srt import __version__
from video2srt.core.config import load_config
from video2srt.core.logging import setup_logging
from video2srt.core.paths import discover_paths
from video2srt.core.pipeline import Pipeline
from video2srt.core.runtime import configure_nvidia_dll_search
from video2srt.ui.main_window import MainWindow


def main() -> int:
    configure_nvidia_dll_search()
    paths = discover_paths()
    logger = setup_logging(paths.logs / "video2srt.log")
    logger.info("Starting Video2SRT %s", __version__)
    app = QApplication(sys.argv)
    app.setApplicationName("Video2SRT")
    try:
        config = load_config(paths.config / "config.json")
        window = MainWindow(paths, config, Pipeline(paths, config, logger))
        window.show()
        return app.exec()
    except Exception:
        logger.exception("Fatal startup error")
        QMessageBox.critical(
            None, "Video2SRT", "Приложение не удалось запустить. Подробности записаны в журнал."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
