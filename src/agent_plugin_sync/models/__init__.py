"""Typed source models, split by ownership:

- `spec` — the Agent Plugin spec shapes (Plugin, Mcp, McpServer, Author).
- `extension` — our com.google.cloud.data.agent-plugins extension (PluginExtension, ConfigVar,
  GeminiConfig) plus `plugin_extension()` to extract it from a Plugin.

Names are re-exported here so callers use `models.Plugin`, `models.plugin_extension`, etc.
"""

from agent_plugin_sync.models.extension import (
    ConfigVar,
    GeminiConfig,
    PluginExtension,
    plugin_extension,
)
from agent_plugin_sync.models.spec import Author, Mcp, McpServer, Plugin

__all__ = [
    "Author",
    "ConfigVar",
    "GeminiConfig",
    "Mcp",
    "McpServer",
    "Plugin",
    "PluginExtension",
    "plugin_extension",
]
