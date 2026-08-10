"""Registry of emitters. Each turns the canonical model into a set of files.

Codex and Antigravity are intentionally absent: Codex reads the Agent Plugin
spec files (plugin.json + mcp.json + skills/) directly, and Antigravity consumes
the plugin's skills/ directory. Neither needs a generated vendor manifest.
"""

from __future__ import annotations

from agent_plugin_sync import model
from agent_plugin_sync.emit import base, claude, gemini

EMITTERS = {
    "gemini": gemini.emit_gemini,
    "claude": claude.emit_claude,
}


def emit_all(plugin_model: model.Model) -> list[base.EmittedFile]:
    """Run every emitter and return the combined file list."""
    files: list[base.EmittedFile] = []
    for emitter in EMITTERS.values():
        files.extend(emitter(plugin_model))
    return files
