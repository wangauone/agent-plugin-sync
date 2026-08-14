"""Generate the Antigravity MCP config: mcp_config.json

`agy plugin install` reads the root `plugin.json` leniently but takes MCP only
from its own `mcp_config.json`, never the spec's `mcp.json`. `mcp_config.json` is
a subset of `mcp.json`: the same `mcpServers`, without `$schema` or the per-server
`type`. See docs/harness-plugin-layouts.md.

Generated mcp_config.json::

    {
      "mcpServers": {
        "postgresql": {"command": "npx", "args": ["-y", "some-mcp-server", "--stdio"]}
      }
    }
"""

from __future__ import annotations

from typing import Any

from agent_plugin_sync import io, loader, models
from agent_plugin_sync.generators import artifact


def generate_antigravity(plugin_model: loader.Model) -> list[artifact.GeneratedFile]:
    """Build the Antigravity MCP config (mcp_config.json). No MCP -> no file."""
    servers = plugin_model.mcp.mcp_servers if plugin_model.mcp else {}
    if not servers:
        return []

    out = {"mcpServers": {name: _to_antigravity_server(s) for name, s in servers.items()}}
    return [artifact.GeneratedFile("mcp_config.json", io.serialize(out))]


def _to_antigravity_server(server: models.McpServer) -> dict[str, Any]:
    """Spec McpServer -> AGY server: drop the spec-only `type`, keep the rest."""
    out: dict[str, Any] = {"command": server.command}
    if server.args is not None:
        out["args"] = server.args
    if server.env is not None:
        out["env"] = server.env
    if server.cwd is not None:
        out["cwd"] = server.cwd
    return out
