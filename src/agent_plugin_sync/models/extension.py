"""Typed models for our com.google.cloud.data.agent-plugins extension bucket.

    PluginExtension  ->  extensions["com.google.cloud.data.agent-plugins"]
    ConfigVar             ->  an item in config[]
    GeminiConfig          ->  the gemini object

This is our own namespace, so unknown fields are forbidden (``extra="forbid"``)
to catch typos. `plugin_extension()` extracts the bucket from a spec Plugin —
keeping that dependency pointed our way (ours -> spec), never the reverse.
Ordered entry-first; the trailing model_rebuild() resolves forward refs.

Example extensions["com.google.cloud.data.agent-plugins"] bucket (parsed into PluginExtension)::

    {
      "config": [
        {"key": "POSTGRES_HOST", "title": "Host",
         "description": "Host or IP address of the server", "sensitive": false}
      ],
      "gemini": {"contextFileName": "POSTGRESQL.md", "mcpServerName": "postgresql"}
    }
"""

from __future__ import annotations

import pydantic
from pydantic.alias_generators import to_camel

import agent_plugin_sync
from agent_plugin_sync.models import spec

_STRICT = pydantic.ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


def plugin_extension(plugin: spec.Plugin) -> PluginExtension:
    """Extract and validate the com.google.cloud.data.agent-plugins bucket from a spec Plugin."""
    return PluginExtension.model_validate(plugin.extensions.get(agent_plugin_sync.PLUGIN_EXTENSION_NS, {}))


class PluginExtension(pydantic.BaseModel):
    model_config = _STRICT

    comment: str | None = None
    config: list[ConfigVar] = pydantic.Field(default_factory=list)
    gemini: GeminiConfig | None = None


class ConfigVar(pydantic.BaseModel):
    model_config = _STRICT

    key: str = pydantic.Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    title: str
    description: str
    required: bool | None = None
    default: str | None = None
    sensitive: bool | None = None


class GeminiConfig(pydantic.BaseModel):
    model_config = _STRICT

    context_file_name: str | None = None
    mcp_server_name: str | None = None


PluginExtension.model_rebuild()
