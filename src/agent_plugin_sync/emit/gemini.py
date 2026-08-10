"""Emit gemini-extension.json from the model.

Note the reverse rewrite of the MCP command: the spec mcp.json uses a
``./``-relative command anchored by ``cwd: ${PLUGIN_ROOT}``, while Gemini expects
its own ``${extensionPath}${/}...`` placeholder and no cwd/type fields.
"""

from __future__ import annotations

from typing import Any

from agent_plugin_sync import io, model, util
from agent_plugin_sync.emit import base


def _to_gemini_command(command: str) -> str:
    """``./toolbox`` -> ``${extensionPath}${/}toolbox``; others pass through."""
    if command.startswith("./"):
        return "${extensionPath}${/}" + command[2:]
    return command


def _to_gemini_server(server: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"command": _to_gemini_command(server["command"])}
    if "args" in server:
        out["args"] = server["args"]
    if "env" in server:
        out["env"] = server["env"]
    return out


def emit_gemini(plugin_model: model.Model) -> list[base.EmittedFile]:
    plugin = plugin_model.plugin
    mcp = plugin_model.mcp or {}
    google = plugin_model.google
    gemini_bits = google.get("gemini") or {}

    out: dict[str, Any] = {"name": plugin["name"]}
    util.copy_present(out, plugin, ["version", "description"])

    # mcpServers, with the command rewrite. Honor an explicit gemini.mcpServerName
    # only when there is exactly one server to rename.
    servers_in = mcp.get("mcpServers") or {}
    if servers_in:
        rename = None
        if gemini_bits.get("mcpServerName") and len(servers_in) == 1:
            rename = gemini_bits["mcpServerName"]
        servers_out: dict[str, Any] = {}
        for name, server in servers_in.items():
            servers_out[rename or name] = _to_gemini_server(server)
        out["mcpServers"] = servers_out

    if gemini_bits.get("contextFileName"):
        out["contextFileName"] = gemini_bits["contextFileName"]

    settings = [
        {"name": c["title"], "description": c["description"], "envVar": c["key"]}
        for c in google.get("config", [])
    ]
    if settings:
        out["settings"] = settings

    return [base.EmittedFile("gemini-extension.json", io.serialize(out))]
