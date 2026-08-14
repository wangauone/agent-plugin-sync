"""Registry of generators. Each turns the canonical model into a set of files.

One generator per non-spec harness: Gemini, Claude, Codex (legacy `.codex-plugin/`,
because its spec `mcp.json` cannot forward user env vars), and Antigravity
(`mcp_config.json`). See docs/harness-plugin-layouts.md.
"""

from __future__ import annotations

from agent_plugin_sync import loader
from agent_plugin_sync.generators import antigravity, artifact, claude, codex, gemini

GENERATORS = {
    "gemini": gemini.generate_gemini,
    "claude": claude.generate_claude,
    "codex": codex.generate_codex,
    "antigravity": antigravity.generate_antigravity,
}


def generate_all(plugin_model: loader.Model) -> list[artifact.GeneratedFile]:
    """Run every generator and return the combined file list."""
    files: list[artifact.GeneratedFile] = []
    for generate in GENERATORS.values():
        files.extend(generate(plugin_model))
    return files
