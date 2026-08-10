"""Small shared helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def copy_present(dst: dict[str, Any], src: dict[str, Any], keys: Iterable[str]) -> None:
    """Copy each key from ``src`` into ``dst`` when present and non-empty.

    Preserves the order of ``keys``, so callers control the output field order.
    """
    for key in keys:
        value = src.get(key)
        if value:
            dst[key] = value
