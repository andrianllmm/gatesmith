from __future__ import annotations

from pathlib import Path


def read_input(source: str) -> str:
    path = Path(source)
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8")
    return source
