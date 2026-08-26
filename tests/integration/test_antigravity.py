"""Antigravity end-to-end via folder install: `agy plugin install <dir>` loads the
skill and MCP server, and an ambient env var reaches the server.

Checks:
    1. `agy plugin install <dir>` accepts the generated files.
    2. It reports exactly one skill and one MCP server.
    3. An ambient env var reaches the MCP server.

AGY forwards the ambient environment. It can't resolve a `./` command, so we point
it at the committed probe by absolute path. Auth lives under HOME (can't isolate),
so we install into the real home; the `_clean_agy` fixture uninstalls before and
after (before too, to recover from a crashed prior run).
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

from tests.integration import cli

pytestmark = pytest.mark.integration

_SENTINEL = "sentinel-12345"


@pytest.fixture
def _clean_agy():
    cli.requires("agy")
    cli.run(["agy", "plugin", "uninstall", "demo"])
    yield
    cli.run(["agy", "plugin", "uninstall", "demo"])


@pytest.mark.usefixtures("_clean_agy")
def test_antigravity_installs_folder_and_forwards_env(generated_plugin):
    # Arrange
    _use_absolute_command(generated_plugin)

    # Assert: folder install loads the skill and the MCP server.
    assert _install(generated_plugin) == (1, 1)

    # Act + Assert: a session starts the server, which sees the ambient value.
    cli.run_session_until(
        ["agy", "-p", "Say hello.", "--dangerously-skip-permissions"], cli.PROBE_DUMP, {"DEMO_HOST": _SENTINEL}
    )
    assert cli.PROBE_DUMP.exists(), "MCP server was not started"
    assert f"DEMO_HOST={_SENTINEL}" in cli.PROBE_DUMP.read_text()


def _use_absolute_command(plugin: pathlib.Path) -> None:
    mcp = plugin / "mcp_config.json"
    data = json.loads(mcp.read_text())
    data["mcpServers"]["demo"] = {"command": str(plugin / "probe.sh")}
    mcp.write_text(json.dumps(data, indent=2))


def _install(plugin: pathlib.Path) -> tuple[int, int]:
    """Install the folder into the real AGY home; return (skills, mcp_servers)."""
    report = cli.run(["agy", "plugin", "install", str(plugin)])
    text = report.stdout + report.stderr
    return _processed(text, "skills"), _processed(text, "mcpServers")


def _processed(report: str, component: str) -> int:
    match = re.search(rf"{component}\s*:\s*(\d+)\s+processed", report)
    return int(match.group(1)) if match else 0
