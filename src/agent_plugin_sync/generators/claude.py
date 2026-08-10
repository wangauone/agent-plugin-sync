"""Generate the Claude Code manifest: .claude-plugin/plugin.json

Claude is not an Agent Plugin spec client, so its MCP config is carried **inline**
in the manifest's `mcpServers` field (not a root `.mcp.json`). That keeps the only
root-level MCP file the spec's `mcp.json` — see docs/harness-plugin-layouts.md.

Config vars become ``userConfig``, keyed by the lowercased env var name.
Marketplace generation is intentionally out of scope.
"""

from __future__ import annotations

from typing import Any

from agent_plugin_sync import io, model, util
from agent_plugin_sync.generators import artifact

# Claude exposes the plugin's install dir as ${CLAUDE_PLUGIN_ROOT}; the spec uses
# ${PLUGIN_ROOT}. Translate the latter to the former in path-bearing fields.
_SPEC_ROOT = "${PLUGIN_ROOT}"
_CLAUDE_ROOT = "${CLAUDE_PLUGIN_ROOT}"


def generate_claude(plugin_model: model.Model) -> list[artifact.GeneratedFile]:
    plugin = plugin_model.plugin
    google = plugin_model.google

    out: dict[str, Any] = {"name": plugin["name"]}
    util.copy_present(
        out,
        plugin,
        ["version", "description", "author", "homepage", "license", "repository"],
    )
    if plugin_model.has_skills:
        out["skills"] = "./skills/"

    config = google.get("config", [])
    if config:
        out["userConfig"] = _to_user_config(config)

    servers = (plugin_model.mcp or {}).get("mcpServers") or {}
    if servers:
        out["mcpServers"] = {name: _to_claude_server(s) for name, s in servers.items()}

    return [artifact.GeneratedFile(".claude-plugin/plugin.json", io.serialize(out))]


def _to_user_config(config: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for c in config:
        out[c["key"].lower()] = {
            "title": c["title"],
            "description": c["description"],
            "type": "string",
            "sensitive": bool(c.get("sensitive", False)),
        }
    return out


def _to_claude_server(server: dict[str, Any]) -> dict[str, Any]:
    """Spec mcp.json server -> Claude inline server.

    Drops spec-only keys (`type`, `$schema`) and retargets the plugin-root
    placeholder in path-bearing fields.
    """
    out: dict[str, Any] = {"command": server["command"]}
    if server.get("args"):
        out["args"] = [_retarget(a) if isinstance(a, str) else a for a in server["args"]]
    if server.get("env"):
        out["env"] = {k: _retarget(v) if isinstance(v, str) else v for k, v in server["env"].items()}
    if server.get("cwd"):
        out["cwd"] = _retarget(server["cwd"])
    return out


def _retarget(value: str) -> str:
    return value.replace(_SPEC_ROOT, _CLAUDE_ROOT)
