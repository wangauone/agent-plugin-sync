"""Claude Code end-to-end via marketplace install: `plugin details` reports the
skill, `--config` sets the userConfig the server resolves
(`${user_config.demo_host}`), and a session starts the server (via the generated
`${CLAUDE_PLUGIN_ROOT}` command). Needs a session (auth), so it's `integration`.
"""

from __future__ import annotations

import json
import re

import pytest

from tests.integration import cli

pytestmark = pytest.mark.integration

_SENTINEL = "sentinel-12345"


def test_claude_installs_skill_and_resolves_config(generated_plugin, tmp_path):
    # Arrange: install from the marketplace with the config value set.
    cli.requires("claude")
    home = tmp_path / "claude_home"
    home.mkdir()
    env = {"CLAUDE_CONFIG_DIR": str(home)}
    market = json.loads((generated_plugin / ".claude-plugin" / "marketplace.json").read_text())["name"]
    cli.run(["claude", "plugin", "marketplace", "add", str(generated_plugin)], env)
    cli.run(["claude", "plugin", "install", f"demo@{market}", "--config", f"demo_host={_SENTINEL}"], env)

    # Assert: the skill is in the inventory.
    details = cli.run(["claude", "plugin", "details", "demo"], env)
    assert re.search(r"Skills \(1\)", details.stdout + details.stderr), "skill not loaded"

    # Act + Assert: a session starts the server, which resolves the config value.
    cli.run_session_until(["claude", "-p", "say ok"], cli.PROBE_DUMP, env)
    assert cli.PROBE_DUMP.exists(), "MCP server was not started"
    assert f"DEMO_HOST={_SENTINEL}" in cli.PROBE_DUMP.read_text()
