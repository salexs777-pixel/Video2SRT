from __future__ import annotations

from pathlib import Path


def load_glossary(path: Path) -> str | None:
    if not path.exists():
        return None
    terms = [
        line.strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return "Термины и имена: " + ", ".join(terms) if terms else None
