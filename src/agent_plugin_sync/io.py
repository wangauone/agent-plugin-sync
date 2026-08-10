"""Small filesystem + JSON helpers with stable, deterministic formatting."""

from __future__ import annotations

import json
import pathlib
from typing import Any


def read_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_if_exists(path: pathlib.Path) -> Any | None:
    return read_json(path) if path.exists() else None


def serialize(value: Any) -> str:
    """Serialize with 2-space indent and a trailing newline (matches the repos)."""
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def write_file(path: pathlib.Path, contents: str) -> None:
    """Write a file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def write_json(path: pathlib.Path, value: Any) -> None:
    write_file(path, serialize(value))
