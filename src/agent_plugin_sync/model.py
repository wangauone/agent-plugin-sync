"""Discover plugin roots and load their source files into typed models.

This is the one place that reads disk, so the generators stay pure functions of
the model.
"""

from __future__ import annotations

import dataclasses
import pathlib

from agent_plugin_sync import io, models


@dataclasses.dataclass
class Model:
    """What the generators read: the parsed source of one plugin."""

    root: pathlib.Path
    plugin: models.Plugin
    mcp: models.Mcp | None
    has_skills: bool = False


def discover_roots(root: pathlib.Path, marker: str = "plugin.json") -> list[pathlib.Path]:
    """Find every plugin root at or under ``root``, identified by ``marker``.

    - Single plugin: ``root`` itself contains ``marker`` -> ``[root]``.
    - Monorepo: no ``marker`` at ``root`` -> every subdirectory that has one.

    Paths under a dot-directory (``.git``, ``.venv``, and crucially the generated
    ``.claude-plugin`` manifests) are skipped, so only true spec plugin roots are
    returned. Results are sorted for deterministic ordering.
    """
    if (root / marker).is_file():
        return [root]

    roots: list[pathlib.Path] = []
    for found in sorted(root.rglob(marker)):
        rel = found.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        roots.append(found.parent)
    return roots


def load_model(root: pathlib.Path) -> Model:
    """Parse a plugin root's source files. Assumes the source is valid (callers
    validate first); raises pydantic.ValidationError on malformed input."""
    plugin_path = root / "plugin.json"
    if not plugin_path.exists():
        raise FileNotFoundError(f"No plugin.json found at {plugin_path}")

    plugin = models.Plugin.model_validate(io.read_json(plugin_path))
    mcp_raw = io.read_json_if_exists(root / "mcp.json")
    mcp = models.Mcp.model_validate(mcp_raw) if mcp_raw is not None else None
    has_skills = (root / "skills").is_dir()

    return Model(root=root, plugin=plugin, mcp=mcp, has_skills=has_skills)
