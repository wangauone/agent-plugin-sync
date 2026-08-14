"""Generic plumbing for driving a harness CLI in a test.

Only harness-neutral helpers live here: run a command, skip when the CLI is
absent, and run a session until the probe fires. The probe MCP server itself is
committed at fixtures/reference/probe.sh and dumps its env to PROBE_DUMP.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import time

import pytest

# Where the committed probe.sh writes the environment it was launched with.
PROBE_DUMP = pathlib.Path("/tmp/aps_probe_env.txt")


def requires(name: str) -> None:
    """Skip the calling test unless the CLI ``name`` is on PATH."""
    if shutil.which(name) is None:
        pytest.skip(f"{name} not installed")


def run(
    cmd: list[str], env: dict[str, str] | None = None, stdin: str | None = None
) -> subprocess.CompletedProcess:
    """Run ``cmd`` (optional ``env`` overlay and ``stdin`` input), capturing output."""
    merged = {**os.environ, **(env or {})}
    return subprocess.run(
        cmd, capture_output=True, text=True, env=merged, check=False, timeout=120, input=stdin
    )


def run_session_until(cmd: list[str], dump: pathlib.Path, env: dict[str, str] | None = None) -> None:
    """Start a harness session (which spawns MCP servers), wait for the probe to
    write ``dump``, then stop the session."""
    session = subprocess.Popen(
        cmd,
        env={**os.environ, **(env or {})},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(60):
            time.sleep(1)
            if dump.exists():
                return
    finally:
        session.terminate()
