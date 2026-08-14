"""One-time seeding: read an existing gemini-extension.json and produce the
Agent Plugin spec source files (plugin.json + mcp.json).

This is scaffolding, NOT part of the ongoing pipeline. After migrating,
plugin.json becomes the source of truth and gemini-extension.json is a generated
output. The seeded plugin.json is a starting point — a human should review
fields migrate cannot infer (required, default, homepage, keywords).
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
import subprocess
from typing import Any

import agent_plugin_sync
from agent_plugin_sync import io

SPEC_MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


@dataclasses.dataclass
class MigrateResult:
    """The seeded source files: plugin.json contents, and mcp.json if any."""

    plugin: dict[str, Any]
    mcp: dict[str, Any] | None


def migrate(root: pathlib.Path) -> MigrateResult:
    """Seed Agent Plugin spec source (plugin.json + mcp.json) from an existing
    gemini-extension.json. One-time scaffolding; review inferred fields after."""
    gemini_path = root / "gemini-extension.json"
    if not gemini_path.exists():
        raise FileNotFoundError(
            f"No gemini-extension.json to migrate from at {gemini_path}"
        )
    gem = io.read_json(gemini_path)

    # --- Build the com.google.cloud.data.agent-plugins extension bucket ---
    extension: dict[str, Any] = {}
    settings = gem.get("settings") or []
    if settings:
        extension["config"] = [_to_config_var(s) for s in settings]

    gemini_bits: dict[str, Any] = {}
    if gem.get("contextFileName"):
        gemini_bits["contextFileName"] = gem["contextFileName"]
    servers = gem.get("mcpServers") or {}
    first_server = next(iter(servers), None)
    if first_server:
        gemini_bits["mcpServerName"] = first_server
    if gemini_bits:
        extension["gemini"] = gemini_bits

    # --- plugin.json ---
    # No $schema: with it, Codex reads the spec mcp.json and ignores the generated
    # .codex-plugin/ (see validate.py / docs/harness-plugin-layouts.md).
    plugin: dict[str, Any] = {"name": gem["name"]}
    if gem.get("version"):
        plugin["version"] = gem["version"]
    if gem.get("description"):
        plugin["description"] = gem["description"]
    plugin["author"] = {
        "name": "Google LLC",
        "email": "data-cloud-ai-integrations@google.com",
    }
    repo = _git_repo_url(root)
    if repo:
        plugin["repository"] = repo
    if (root / "LICENSE").exists():
        plugin["license"] = "Apache-2.0"
    plugin["extensions"] = {agent_plugin_sync.PLUGIN_EXTENSION_NS: extension}

    # --- mcp.json (only if the gemini extension declared MCP servers) ---
    mcp: dict[str, Any] | None = None
    if servers:
        mcp_servers: dict[str, Any] = {}
        for name, server in servers.items():
            entry: dict[str, Any] = {
                "type": "stdio",
                "command": _to_spec_command(server["command"]),
            }
            if server.get("args"):
                entry["args"] = server["args"]
            if server.get("env"):
                entry["env"] = server["env"]
            entry["cwd"] = "${PLUGIN_ROOT}"
            mcp_servers[name] = entry
        mcp = {"$schema": SPEC_MCP_SCHEMA, "mcpServers": mcp_servers}

    return MigrateResult(plugin=plugin, mcp=mcp)


def _to_config_var(setting: dict[str, Any]) -> dict[str, Any]:
    key = setting["envVar"]
    var: dict[str, Any] = {
        "key": key,
        "title": setting.get("name", key),
        "description": setting.get("description", ""),
    }
    # Best-effort inference; the human refines these after migrate.
    if re.search(r"password|secret|token", key, re.IGNORECASE):
        var["sensitive"] = True
    return var


def _git_repo_url(root: pathlib.Path) -> str | None:
    try:
        url = subprocess.run(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    # Normalize git@github.com:owner/repo.git -> https URL.
    ssh = re.match(r"^git@([^:]+):(.+?)(?:\.git)?$", url)
    if ssh:
        return f"https://{ssh.group(1)}/{ssh.group(2)}"
    return re.sub(r"\.git$", "", url)


def _to_spec_command(command: str) -> str:
    """``${extensionPath}${/}toolbox`` -> ``./toolbox`` for the spec mcp.json."""
    stripped = re.sub(r"^\$\{extensionPath\}\$\{/\}", "", command)
    return command if stripped == command else f"./{stripped}"
