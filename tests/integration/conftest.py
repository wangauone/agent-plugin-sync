"""Fixtures for the integration suite.

The flow every harness test shares: take the one committed reference plugin,
generate the harness files into a temp copy, and hand back an installable root.
The reference already carries the hand-authored inputs the tool does not generate
(plugin.json, mcp.json, skills, and the marketplace descriptor Codex/Claude need).
"""

from __future__ import annotations

import pathlib
import shutil

import pytest

from agent_plugin_sync import generators, io, loader
from tests.integration import cli

_REFERENCE = pathlib.Path(__file__).parent / "fixtures" / "reference"


@pytest.fixture(autouse=True)
def _fresh_probe_dump():
    """Each test reads the probe's env dump at a fixed path; start clean."""
    cli.PROBE_DUMP.unlink(missing_ok=True)
    yield
    cli.PROBE_DUMP.unlink(missing_ok=True)


@pytest.fixture
def generated_plugin(tmp_path: pathlib.Path) -> pathlib.Path:
    """A temp copy of the committed reference plugin with all harness files
    generated into it, ready to install."""
    plugin = tmp_path / "plugin"
    shutil.copytree(_REFERENCE, plugin)
    for generated in generators.generate_all(loader.load_model(plugin)):
        io.write_file(plugin / generated.path, generated.contents)
    return plugin
