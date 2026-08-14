"""Gemini end-to-end via folder install: `gemini extensions install <dir>` loads
the extension and its skill, the generated `${extensionPath}` command resolves the
committed probe, and an ambient env var reaches the server.

Gemini forwards the ambient environment. It prompts to trust the folder (answered
on stdin) and installs into the real home; the `_clean_gemini` fixture uninstalls
before and after (before too, to recover from a crashed prior run).
"""

from __future__ import annotations

import pathlib
import shutil

import pytest

from tests.integration import cli

pytestmark = pytest.mark.integration

_SENTINEL = "sentinel-12345"
_INSTALLED = pathlib.Path.home() / ".gemini" / "extensions" / "demo"


@pytest.fixture
def _clean_gemini():
    cli.requires("gemini")
    _uninstall()
    yield
    _uninstall()


@pytest.mark.usefixtures("_clean_gemini")
def test_gemini_installs_folder_and_forwards_env(generated_plugin):
    # Act: install the folder (answer the trust prompt).
    cli.run(
        ["gemini", "extensions", "install", str(generated_plugin), "--consent", "--skip-settings"],
        stdin="y\n",
    )

    # Assert: the skill is discovered.
    assert "demo" in cli.run(["gemini", "skills", "list"]).stdout, "skill not loaded"

    # Act + Assert: the generated command started the probe, which saw the value.
    cli.run_session_until(
        ["gemini", "-p", "say ok", "--approval-mode", "yolo"], cli.PROBE_DUMP, {"DEMO_HOST": _SENTINEL}
    )
    assert cli.PROBE_DUMP.exists(), "MCP server was not started"
    assert f"DEMO_HOST={_SENTINEL}" in cli.PROBE_DUMP.read_text()


def _uninstall() -> None:
    cli.run(["gemini", "extensions", "uninstall", "demo"])
    shutil.rmtree(_INSTALLED, ignore_errors=True)  # a killed install can leave a stub
