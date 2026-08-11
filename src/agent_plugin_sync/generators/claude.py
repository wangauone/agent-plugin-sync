"""Generate the Claude Code manifest: .claude-plugin/plugin.json

Claude is not an Agent Plugin spec client, so its MCP config is carried **inline**
in the manifest's `mcpServers` field (not a root `.mcp.json`). That keeps the only
root-level MCP file the spec's `mcp.json` — see docs/harness-plugin-layouts.md.

Config vars become ``userConfig``, keyed by the lowercased env var name.
Marketplace generation is intentionally out of scope.
"""

from __future__ import annotations

from typing import Any

from agent_plugin_sync import io, loader, models
from agent_plugin_sync.generators import artifact

# Claude exposes the plugin's install dir as ${CLAUDE_PLUGIN_ROOT}; the spec uses
# ${PLUGIN_ROOT}. Translate the latter to the former in path-bearing fields.
_SPEC_ROOT = "${PLUGIN_ROOT}"
_CLAUDE_ROOT = "${CLAUDE_PLUGIN_ROOT}"

_PASSTHROUGH = {"version", "description", "author", "homepage", "license", "repository"}


def generate_claude(plugin_model: loader.Model) -> list[artifact.GeneratedFile]:
    plugin = plugin_model.plugin

    out: dict[str, Any] = {"name": plugin.name}
    out.update(plugin.model_dump(include=_PASSTHROUGH, exclude_none=True, by_alias=True))
    if plugin_model.has_skills:
        out["skills"] = "./skills/"

    config = plugin.google.config
    if config:
        out["userConfig"] = {c.key.lower(): _to_user_config(c) for c in config}

    servers = plugin_model.mcp.mcp_servers if plugin_model.mcp else {}
    if servers:
        out["mcpServers"] = {name: _to_claude_server(s) for name, s in servers.items()}

    return [artifact.GeneratedFile(".claude-plugin/plugin.json", io.serialize(out))]


def _to_user_config(var: models.ConfigVar) -> dict[str, Any]:
    return {
        "title": var.title,
        "description": var.description,
        "type": "string",
        "sensitive": bool(var.sensitive),
    }


def _to_claude_server(server: models.McpServer) -> dict[str, Any]:
    """Spec McpServer -> Claude inline server.

    Drops the spec-only ``type`` and retargets the plugin-root placeholder.
    """
    out: dict[str, Any] = {"command": server.command}
    if server.args is not None:
        out["args"] = [_retarget(a) for a in server.args]
    if server.env is not None:
        out["env"] = {k: _retarget(v) for k, v in server.env.items()}
    if server.cwd is not None:
        out["cwd"] = _retarget(server.cwd)
    return out


def _retarget(value: str) -> str:
    return value.replace(_SPEC_ROOT, _CLAUDE_ROOT)
