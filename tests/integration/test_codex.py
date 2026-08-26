"""Codex end-to-end via folder install: the plugin installs, its MCP server starts,
and a user env var resolves into it.

Checks:
    1. Marketplace install accepts the generated files.
    2. A session starts the MCP server.
    3. A user env var reaches it, i.e. Codex applied the `.codex-plugin/`
       `env_vars` overlay to the spec server. **Needs Codex 0.150.0+**; older
       versions read the spec mcp.json only and drop the variable.

Codex-legacy can't resolve a `./` command, so we point it at the committed probe
by absolute path. Needs a session (auth), so it's marked `integration`.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from tests.integration import cli

pytestmark = pytest.mark.integration

_SENTINEL = "sentinel-12345"


def test_codex_starts_server_and_resolves_env(generated_plugin, tmp_path):
    # Arrange
    cli.requires("codex")
    home = tmp_path / "codex_home"
    home.mkdir()
    _use_absolute_command(generated_plugin)
    _install(generated_plugin, home)

    # Act
    cli.run_session_until(
        ["codex", "exec", "--skip-git-repo-check", "reply ok"],
        cli.PROBE_DUMP,
        {"CODEX_HOME": str(home), "DEMO_HOST": _SENTINEL},
    )

    # Assert
    assert cli.PROBE_DUMP.exists(), "MCP server was not started"
    assert f"DEMO_HOST={_SENTINEL}" in cli.PROBE_DUMP.read_text()


def _use_absolute_command(plugin: pathlib.Path) -> None:
    mcp = plugin / ".codex-plugin" / ".mcp.json"
    data = json.loads(mcp.read_text())
    data["mcpServers"]["demo"].update(command=str(plugin / "probe.sh"), args=[])
    mcp.write_text(json.dumps(data, indent=2))


def _install(plugin: pathlib.Path, home: pathlib.Path) -> None:
    codex_home = {"CODEX_HOME": str(home)}
    market = json.loads((plugin / ".claude-plugin" / "marketplace.json").read_text())["name"]
    cli.run(["codex", "plugin", "marketplace", "add", str(plugin)], codex_home)
    cli.run(["codex", "plugin", "add", f"demo@{market}"], codex_home)
