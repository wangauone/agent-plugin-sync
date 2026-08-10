"""Load the source files from a plugin root and build the canonical model.

This is the one place that reads disk, so the emitters stay pure functions of
the model.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import Any

import agent_plugin_sync
from agent_plugin_sync import io


@dataclasses.dataclass
class Model:
    """What the emitters read. `plugin`, `mcp`, and `google` are parsed JSON."""

    root: pathlib.Path
    plugin: dict[str, Any]
    mcp: dict[str, Any] | None
    google: dict[str, Any] = dataclasses.field(default_factory=dict)
    has_skills: bool = False


def discover_roots(root: pathlib.Path, marker: str = "plugin.json") -> list[pathlib.Path]:
    """Find every plugin root at or under ``root``, identified by ``marker``.

    - Single plugin: ``root`` itself contains ``marker`` -> ``[root]``.
    - Monorepo: no ``marker`` at ``root`` -> every subdirectory that has one.

    Paths under a dot-directory (``.git``, ``.venv``, and crucially the generated
    ``.claude-plugin``/``.codex-plugin`` manifests) are skipped, so only true spec
    plugin roots are returned. Results are sorted for deterministic ordering.
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
    plugin_path = root / "plugin.json"
    if not plugin_path.exists():
        raise FileNotFoundError(f"No plugin.json found at {plugin_path}")

    plugin = io.read_json(plugin_path)
    mcp = io.read_json_if_exists(root / "mcp.json")
    google = plugin.get("extensions", {}).get(agent_plugin_sync.GOOGLE_NS, {})
    has_skills = (root / "skills").is_dir()

    return Model(root=root, plugin=plugin, mcp=mcp, google=google, has_skills=has_skills)
