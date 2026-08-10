"""Readable assertions/lookups shared across tests."""

from __future__ import annotations

import json

from agent_plugin_sync.generators.artifact import GeneratedFile


def generated_json(files: list[GeneratedFile], path: str) -> dict:
    """Parse the single generated file at ``path`` (fails clearly if missing/duplicated)."""
    matches = [f for f in files if f.path == path]
    assert len(matches) == 1, (
        f"expected exactly one '{path}', got {sorted(f.path for f in files)}"
    )
    return json.loads(matches[0].contents)


def generated_paths(files: list[GeneratedFile]) -> set[str]:
    """The set of relative paths a generator produced."""
    return {f.path for f in files}
