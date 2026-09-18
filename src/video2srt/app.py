from __future__ import annotations

import sys
import tempfile
import traceback
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from video2srt import __version__
from video2srt.core.config import load_config
from video2srt.core.logging import setup_logging
from video2srt.core.paths import discover_paths
from video2srt.core.pipeline import Pipeline
from video2srt.core.runtime import (
    configure_headless_network_clients,
    configure_nvidia_dll_search,
    configure_system_certificates,
)
from video2srt.ui.main_window import MainWindow


def main() -> int:
    configure_headless_network_clients()
    configure_system_certificates()
    if "--network-self-test" in sys.argv:
        report = Path(sys.executable).resolve().parent / "network-self-test.log"
        try:
            from huggingface_hub import hf_hub_download

            with tempfile.TemporaryDirectory(prefix="video2srt-network-test-") as directory:
                hf_hub_download(
                    "Systran/faster-whisper-small",
                    "config.json",
                    local_dir=Path(directory),
                )
            report.write_text("OK\n", encoding="utf-8")
            return 0
        except Exception:
            report.write_text(traceback.format_exc(), encoding="utf-8")
            return 1
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
