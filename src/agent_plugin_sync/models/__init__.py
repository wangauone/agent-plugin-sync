"""Typed source models, split by ownership:

- `spec` — the Agent Plugin spec shapes (Plugin, Mcp, McpServer, Author).
- `google` — our com.google.cloud extension (GoogleCloudExtension, ConfigVar,
  GeminiConfig) plus `google_extension()` to extract it from a Plugin.

Names are re-exported here so callers use `models.Plugin`, `models.google_extension`, etc.
"""

from agent_plugin_sync.models.google import (
    ConfigVar,
    GeminiConfig,
    GoogleCloudExtension,
    google_extension,
)
from agent_plugin_sync.models.spec import Author, Mcp, McpServer, Plugin

__all__ = [
    "Author",
    "ConfigVar",
    "GeminiConfig",
    "GoogleCloudExtension",
    "Mcp",
    "McpServer",
    "Plugin",
    "google_extension",
]
