"""Generate the Codex (legacy .codex-plugin) manifest + MCP config.

Codex reads the Agent Plugin spec, but its spec `mcp.json` cannot forward user
environment variables to an MCP server (`env_vars` is rejected, `${VAR}` in `env`
is not expanded, ambient env is cleared). So we target Codex's **legacy**
`.codex-plugin/` format, whose `env_vars` list forwards named vars from the user
environment. For Codex to use these files the root `plugin.json` must omit
`$schema`; see docs/harness-plugin-layouts.md.

Config vars (`com.google.cloud.data.agent-plugins.config`) become `env_vars` on
each server. The manifest references the sibling MCP file with a **root-relative**
path (`./.codex-plugin/.mcp.json`), the way Codex resolves it.

Generated .codex-plugin/plugin.json::

    {
      "name": "postgres",
      "version": "0.2.2",
      "description": "...",
      "author": {"name": "Google LLC"},
      "homepage": "...", "license": "Apache-2.0", "repository": "...",
      "keywords": ["postgres", "database"],
      "skills": "./skills",
      "mcpServers": "./.codex-plugin/.mcp.json"
    }

Generated .codex-plugin/.mcp.json::

    {
      "mcpServers": {
        "postgresql": {
          "command": "npx", "args": ["-y", "some-mcp-server", "--stdio"],
          "env_vars": ["POSTGRES_HOST"]
        }
      }
    }
"""

from __future__ import annotations

from typing import Any

from agent_plugin_sync import io, loader, models
from agent_plugin_sync.generators import artifact

_MANIFEST = ".codex-plugin/plugin.json"
_MCP = ".codex-plugin/.mcp.json"
# Codex resolves the manifest's `mcpServers` path relative to the plugin root, not
# the .codex-plugin/ directory, so the reference includes the directory.
_MCP_REF = "./.codex-plugin/.mcp.json"

_PASSTHROUGH = {"version", "description", "author", "homepage", "license", "repository", "keywords"}


def generate_codex(plugin_model: loader.Model) -> list[artifact.GeneratedFile]:
    """Build the Codex legacy manifest (.codex-plugin/plugin.json) + its MCP file."""
    plugin = plugin_model.plugin
    servers = plugin_model.mcp.mcp_servers if plugin_model.mcp else {}

    manifest: dict[str, Any] = {"name": plugin.name}
    manifest.update(plugin.model_dump(include=_PASSTHROUGH, exclude_none=True, by_alias=True))
    if plugin_model.has_skills:
        manifest["skills"] = "./skills"

    files: list[artifact.GeneratedFile] = []
    if servers:
        manifest["mcpServers"] = _MCP_REF
        env_vars = [c.key for c in models.plugin_extension(plugin).config]
        mcp = {"mcpServers": {name: _to_codex_server(s, env_vars) for name, s in servers.items()}}
        files.append(artifact.GeneratedFile(_MCP, io.serialize(mcp)))

    files.insert(0, artifact.GeneratedFile(_MANIFEST, io.serialize(manifest)))
    return files


def _to_codex_server(server: models.McpServer, env_vars: list[str]) -> dict[str, Any]:
    """Spec McpServer -> Codex legacy server: drop spec-only `type`, add `env_vars`."""
    out: dict[str, Any] = {"command": server.command}
    if server.args is not None:
        out["args"] = server.args
    if server.env is not None:
        out["env"] = server.env
    if server.cwd is not None:
        out["cwd"] = server.cwd
    if env_vars:
        out["env_vars"] = env_vars
    return out
