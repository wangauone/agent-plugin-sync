"""Shared type for emitters."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class EmittedFile:
    """A single generated file, path relative to the plugin root."""

    path: str
    contents: str
