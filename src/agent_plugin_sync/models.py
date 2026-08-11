"""Typed models for the source files, one per JSON shape.

    Plugin                ->  plugin.json
    Mcp                   ->  mcp.json
    McpServer             ->  an entry in mcpServers
    GoogleCloudExtension  ->  extensions["com.google.cloud"]
    ConfigVar             ->  an item in config[]
    GeminiConfig          ->  the gemini object

Python attributes are snake_case; JSON keys are camelCase, bridged by an alias
generator. Our own bucket (GoogleCloudExtension and friends) forbids unknown
fields so typos are caught; the spec-owned Plugin/Mcp/McpServer tolerate fields
we don't model.
"""

from __future__ import annotations

from typing import Any

import pydantic
from pydantic.alias_generators import to_camel

import agent_plugin_sync

_STRICT = pydantic.ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")
_LENIENT = pydantic.ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


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


class GoogleCloudExtension(pydantic.BaseModel):
    model_config = _STRICT

    comment: str | None = None
    config: list[ConfigVar] = pydantic.Field(default_factory=list)
    gemini: GeminiConfig | None = None


class Author(pydantic.BaseModel):
    model_config = _LENIENT

    name: str
    email: str | None = None
    url: str | None = None


class Plugin(pydantic.BaseModel):
    model_config = _LENIENT

    name: str
    version: str | None = None
    description: str | None = None
    author: Author | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] | None = None
    extensions: dict[str, Any] = pydantic.Field(default_factory=dict)

    @property
    def google(self) -> GoogleCloudExtension:
        """The com.google.cloud extension bucket, validated on access."""
        return GoogleCloudExtension.model_validate(self.extensions.get(agent_plugin_sync.GOOGLE_NS, {}))


class McpServer(pydantic.BaseModel):
    model_config = _LENIENT

    type: str | None = None
    command: str
    args: list[str] | None = None
    env: dict[str, str] | None = None
    cwd: str | None = None


class Mcp(pydantic.BaseModel):
    model_config = _LENIENT

    mcp_servers: dict[str, McpServer] = pydantic.Field(default_factory=dict)
