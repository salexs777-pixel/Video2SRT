from __future__ import annotations

import os
import sys
from pathlib import Path

_DLL_HANDLES: list[object] = []


def configure_nvidia_dll_search() -> None:
    """Expose bundled NVIDIA redistributables without editing the user's PATH."""
    if sys.platform != "win32":
        return
    roots = []
    if getattr(sys, "frozen", False):
        roots.append(Path(sys._MEIPASS) / "nvidia")
    roots.append(Path(sys.prefix) / "Lib" / "site-packages" / "nvidia")
    for root in roots:
        if not root.exists():
            continue
        for directory in root.rglob("bin"):
            value = str(directory)
            if value not in os.environ.get("PATH", "").split(os.pathsep):
                os.environ["PATH"] = value + os.pathsep + os.environ.get("PATH", "")
            try:
                _DLL_HANDLES.append(os.add_dll_directory(value))
            except (AttributeError, OSError):
                pass
