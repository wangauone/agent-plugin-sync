"""Registry of generators. Each turns the canonical model into a set of files.

Codex and Antigravity are intentionally absent: Codex reads the Agent Plugin spec
files (plugin.json + mcp.json + skills/) directly, and Antigravity consumes the
Gemini output via `agy plugin import gemini`. Neither needs a generated vendor file.
"""

from __future__ import annotations

from agent_plugin_sync import loader
from agent_plugin_sync.generators import artifact, claude, gemini

GENERATORS = {
    "gemini": gemini.generate_gemini,
    "claude": claude.generate_claude,
}


def generate_all(plugin_model: loader.Model) -> list[artifact.GeneratedFile]:
    """Run every generator and return the combined file list."""
    files: list[artifact.GeneratedFile] = []
    for generate in GENERATORS.values():
        files.extend(generate(plugin_model))
    return files
