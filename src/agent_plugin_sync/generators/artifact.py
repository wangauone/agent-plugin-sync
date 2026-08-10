"""The output type shared by all generators."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class GeneratedFile:
    """A single generated file, path relative to the plugin root."""

    path: str
    contents: str
