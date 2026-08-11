"""Validate a plugin's source files against the typed models.

Errors are prefixed with the file/namespace they came from (e.g.
``com.google.cloud/config/0/key``) so authors can locate them.
"""

from __future__ import annotations

import dataclasses
import pathlib

import pydantic

import agent_plugin_sync
from agent_plugin_sync import io, models


@dataclasses.dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = dataclasses.field(default_factory=list)


def validate_plugin(root: pathlib.Path) -> ValidationResult:
    errors: list[str] = []

    raw = io.read_json(root / "plugin.json")
    try:
        plugin = models.Plugin.model_validate(raw)
    except pydantic.ValidationError as e:
        # Malformed top level; can't check the bucket meaningfully after this.
        return ValidationResult(ok=False, errors=_format(e, "plugin.json"))

    bucket = plugin.extensions.get(agent_plugin_sync.GOOGLE_NS, {})
    try:
        models.GoogleCloudExtension.model_validate(bucket)
    except pydantic.ValidationError as e:
        errors += _format(e, agent_plugin_sync.GOOGLE_NS)

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
