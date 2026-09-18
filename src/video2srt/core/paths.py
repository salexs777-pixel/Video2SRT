from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path

    @property
    def bin(self) -> Path:
        return self.root / "bin"

    @property
    def models(self) -> Path:
        return self.root / "models"

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def output(self) -> Path:
        return self.root / "output"

    def ensure(self) -> None:
        for path in (self.bin, self.models, self.config, self.logs, self.output):
            path.mkdir(parents=True, exist_ok=True)

    def executable(self, name: str) -> Path:
        bundled = self.bin / f"{name}.exe"
        return bundled if bundled.exists() else Path(f"{name}.exe")


def discover_paths() -> AppPaths:
    override = os.environ.get("VIDEO2SRT_ROOT")
    if override:
        root = Path(override).expanduser().resolve()
    elif getattr(sys, "frozen", False):
        root = Path(sys.executable).resolve().parent
    else:
        root = Path(__file__).resolve().parents[3]
    paths = AppPaths(root)
    paths.ensure()
    return paths
