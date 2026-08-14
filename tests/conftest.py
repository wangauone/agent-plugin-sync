"""Shared test fixtures."""

from __future__ import annotations

import json
import pathlib

import pytest

_PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
_MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


def _write_json(path: pathlib.Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def make_plugin():
    """Factory that writes a spec plugin (plugin.json + optional mcp.json/skills).

    Returns the plugin root path. `mcp` is the `mcpServers` map (server configs).
    """

    def _make(
        root: pathlib.Path,
        *,
        name: str = "demo",
        config: list[dict] | None = None,
        gemini: dict | None = None,
        mcp: dict | None = None,
        skills: bool = False,
        schema: bool = False,
    ) -> pathlib.Path:
        root = pathlib.Path(root)
        ns: dict = {}
        if config is not None:
            ns["config"] = config
        if gemini is not None:
            ns["gemini"] = gemini

        # $schema is omitted by default: with it, Codex ignores the generated
        # .codex-plugin/. `schema=True` opts in to exercise that validation error.
        plugin: dict = {
            "name": name,
            "version": "0.1.0",
            "description": "Demo plugin.",
            "author": {"name": "Google LLC"},
            "license": "Apache-2.0",
            "extensions": {"com.google.cloud.data.agent-plugins": ns},
        }
        if schema:
            plugin = {"$schema": _PLUGIN_SCHEMA, **plugin}
        _write_json(root / "plugin.json", plugin)

        if mcp is not None:
            _write_json(root / "mcp.json", {"$schema": _MCP_SCHEMA, "mcpServers": mcp})

        if skills:
            skill_dir = root / "skills" / "demo"
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: demo\ndescription: demo skill\n---\n", encoding="utf-8"
            )

        return root

    return _make
