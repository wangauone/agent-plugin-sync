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

    # A spec client recognises the manifest by its $schema, so it must be an
    # agent-plugins URI. Codex 0.150.0 and later still forward user env vars in that
    # case: they overlay the generated .codex-plugin/ env_vars onto the spec servers
    # (openai/codex#40363). Older Codex ignores that overlay, so plugins targeting
    # 0.149.x and earlier must stay on an older release of this tool.
    schema = raw.get("$schema")
    if not (isinstance(schema, str) and schema.startswith(_AGENT_PLUGIN_SCHEMA_PREFIX)):
        errors.append(
            f"plugin.json: $schema must be an Agent Plugin spec URI ({_AGENT_PLUGIN_SCHEMA_PREFIX}...); "
            "without it a spec client does not recognise the manifest"
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
