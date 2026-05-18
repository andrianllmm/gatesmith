from __future__ import annotations

from pathlib import Path


def write_output(destination: str, content: str) -> None:
    path = Path(destination)
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
