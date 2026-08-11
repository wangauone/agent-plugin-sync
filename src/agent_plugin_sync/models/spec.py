"""Typed models for the Agent Plugin spec source files.

    Plugin     ->  plugin.json
    Mcp        ->  mcp.json
    McpServer  ->  an entry in mcpServers
    Author     ->  the author object

These mirror spec-owned shapes, so they tolerate fields we don't model
(``extra="ignore"``) — a partial view for reading, not a full spec validator.
Ordered entry-first; the trailing model_rebuild() calls resolve forward refs.

Example plugin.json (parsed into Plugin)::

    {
      "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
      "name": "postgres",
      "version": "0.2.2",
      "description": "Connect and interact with a PostgreSQL database.",
      "author": {"name": "Google LLC", "email": "..."},
      "homepage": "...", "repository": "...", "license": "Apache-2.0",
      "keywords": ["postgres", "database"],
      "extensions": {"com.google.cloud": {...}}    # see models/google.py
    }

Example mcp.json (parsed into Mcp)::

    {
      "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
      "mcpServers": {
        "postgresql": {
          "type": "stdio",
          "command": "npx",
          "args": ["-y", "some-mcp-server", "--stdio"]
        }
      }
    }
"""

from __future__ import annotations

from typing import Any

import pydantic
from pydantic.alias_generators import to_camel

_LENIENT = pydantic.ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


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


class Author(pydantic.BaseModel):
    model_config = _LENIENT

    name: str
    email: str | None = None
    url: str | None = None


class Mcp(pydantic.BaseModel):
    model_config = _LENIENT

    mcp_servers: dict[str, McpServer] = pydantic.Field(default_factory=dict)


class McpServer(pydantic.BaseModel):
    model_config = _LENIENT

    type: str | None = None
    command: str
    args: list[str] | None = None
    env: dict[str, str] | None = None
    cwd: str | None = None


Plugin.model_rebuild()
Mcp.model_rebuild()
