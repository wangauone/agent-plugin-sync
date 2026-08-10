"""Validate the source ``extensions["com.google.cloud"]`` bucket against our
JSON Schema. This is the authoring safety net — it catches typos and missing
fields before generation.
"""

from __future__ import annotations

import dataclasses
import pathlib

import jsonschema

from agent_plugin_sync import io, model

# Schema ships inside the package.
_SCHEMA_PATH = pathlib.Path(__file__).parent / "schema" / "com.google.cloud.schema.json"


@dataclasses.dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = dataclasses.field(default_factory=list)


def validate_model(plugin_model: model.Model) -> ValidationResult:
    schema = io.read_json(_SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema)

    errors = []
    for err in sorted(validator.iter_errors(plugin_model.google), key=str):
        location = "".join(f"/{p}" for p in err.absolute_path)
        errors.append(f"com.google.cloud{location} {err.message}")

    return ValidationResult(ok=not errors, errors=errors)
