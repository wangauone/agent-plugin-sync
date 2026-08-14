"""Generate gemini-extension.json from the model.

Note the reverse rewrite of the MCP command: the spec mcp.json uses a
``./``-relative command anchored by ``cwd: ${PLUGIN_ROOT}``, while Gemini expects
its own ``${extensionPath}${/}...`` placeholder and no cwd/type fields.

Generated gemini-extension.json::

    {
      "name": "postgres",
      "version": "0.2.2",
      "description": "...",
      "mcpServers": {
        "postgresql": {"command": "npx", "args": ["-y", "some-mcp-server", "--stdio"]}
      },
      "contextFileName": "POSTGRESQL.md",
      "settings": [
        {"name": "Host", "description": "...", "envVar": "POSTGRES_HOST"}
      ]
    }
"""

from __future__ import annotations

from typing import Any

from agent_plugin_sync import io, loader, models
from agent_plugin_sync.generators import artifact


def generate_gemini(plugin_model: loader.Model) -> list[artifact.GeneratedFile]:
    """Build the Gemini CLI extension manifest (gemini-extension.json)."""
    plugin = plugin_model.plugin
    ext = models.plugin_extension(plugin)
    gemini = ext.gemini

    out: dict[str, Any] = {"name": plugin.name}
    out.update(plugin.model_dump(include={"version", "description"}, exclude_none=True, by_alias=True))

    # mcpServers, with the command rewrite. Honor an explicit gemini.mcpServerName
    # only when there is exactly one server to rename.
    servers = plugin_model.mcp.mcp_servers if plugin_model.mcp else {}
    if servers:
        rename = None
        if gemini and gemini.mcp_server_name and len(servers) == 1:
            rename = gemini.mcp_server_name
        out["mcpServers"] = {
            (rename or name): _to_gemini_server(server) for name, server in servers.items()
        }

    if gemini and gemini.context_file_name:
        out["contextFileName"] = gemini.context_file_name

    settings = [
        {"name": c.title, "description": c.description, "envVar": c.key} for c in ext.config
    ]
    if settings:
        out["settings"] = settings

    return [artifact.GeneratedFile("gemini-extension.json", io.serialize(out))]


def _to_gemini_server(server: models.McpServer) -> dict[str, Any]:
    out: dict[str, Any] = {"command": _to_gemini_command(server.command)}
    if server.args is not None:
        out["args"] = server.args
    if server.env is not None:
        out["env"] = server.env
    return out


def _to_gemini_command(command: str) -> str:
    """``./toolbox`` -> ``${extensionPath}${/}toolbox``; others pass through."""
    if command.startswith("./"):
        return "${extensionPath}${/}" + command[2:]
    return command
