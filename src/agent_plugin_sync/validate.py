"""Validate a plugin's source files against the typed models.

Errors are prefixed with the file/namespace they came from (e.g.
``com.google.cloud.data.agent-plugins/config/0/key``) so authors can locate them.
"""

from __future__ import annotations

import dataclasses
import pathlib

import pydantic

import agent_plugin_sync
from agent_plugin_sync import io, models

_AGENT_PLUGIN_SCHEMA_PREFIX = "https://agent-plugins.org/schemas/"


@dataclasses.dataclass
class ValidationResult:
    """Outcome of validation: ok, plus any namespaced error messages."""

    ok: bool
    errors: list[str] = dataclasses.field(default_factory=list)


def validate_plugin(root: pathlib.Path) -> ValidationResult:
    """Validate a plugin root's source files against the typed models."""
    errors: list[str] = []

    raw = io.read_json(root / "plugin.json")
    try:
        plugin = models.Plugin.model_validate(raw)
    except pydantic.ValidationError as e:
        # Malformed top level; can't check the bucket meaningfully after this.
        return ValidationResult(ok=False, errors=_format(e, "plugin.json"))

    # Codex reads a root manifest as Agent Plugin (and so uses the spec mcp.json,
    # which cannot forward user env vars) only when its $schema is an agent-plugins
    # URI. We route Codex to the generated .codex-plugin/ instead, so $schema must
    # be absent; with it present, that generated file is silently ignored.
    schema = raw.get("$schema", "")
    if isinstance(schema, str) and schema.startswith(_AGENT_PLUGIN_SCHEMA_PREFIX):
        errors.append(
            "plugin.json: omit $schema; with it, Codex reads the spec mcp.json and ignores "
            "the generated .codex-plugin/ (its env_vars)"
        )

    bucket = plugin.extensions.get(agent_plugin_sync.PLUGIN_EXTENSION_NS, {})
    try:
        models.PluginExtension.model_validate(bucket)
    except pydantic.ValidationError as e:
        errors += _format(e, agent_plugin_sync.PLUGIN_EXTENSION_NS)

    mcp_raw = io.read_json_if_exists(root / "mcp.json")
    if mcp_raw is not None:
        try:
            models.Mcp.model_validate(mcp_raw)
        except pydantic.ValidationError as e:
            errors += _format(e, "mcp.json")

    return ValidationResult(ok=not errors, errors=errors)


def _format(error: pydantic.ValidationError, prefix: str) -> list[str]:
    return [
        f"{prefix}/{'/'.join(str(p) for p in item['loc'])} {item['msg']}"
        for item in error.errors()
    ]
