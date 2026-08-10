"""Readable assertions/lookups shared across tests."""

from __future__ import annotations

import json

from agent_plugin_sync.emit.base import EmittedFile


def generated_json(files: list[EmittedFile], path: str) -> dict:
    """Parse the single emitted file at ``path`` (fails clearly if missing/duplicated)."""
    matches = [f for f in files if f.path == path]
    assert len(matches) == 1, (
        f"expected exactly one '{path}', got {sorted(f.path for f in files)}"
    )
    return json.loads(matches[0].contents)


def emitted_paths(files: list[EmittedFile]) -> set[str]:
    """The set of relative paths an emitter produced."""
    return {f.path for f in files}
