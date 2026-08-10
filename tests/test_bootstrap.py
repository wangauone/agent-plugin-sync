"""Bootstrapping spec source files from an existing gemini-extension.json."""

from __future__ import annotations

import json

from agent_plugin_sync import bootstrap

_GEMINI_EXTENSION = {
    "name": "demo",
    "version": "1.0.0",
    "description": "Demo extension.",
    "mcpServers": {
        "demo": {"command": "${extensionPath}${/}toolbox", "args": ["--stdio"]}
    },
    "contextFileName": "CTX.md",
    "settings": [
        {"name": "Password", "description": "the password", "envVar": "DEMO_PASSWORD"},
        {"name": "Host", "description": "the host", "envVar": "DEMO_HOST"},
    ],
}


def _seed_gemini_extension(root, *, with_license=True):
    (root / "gemini-extension.json").write_text(json.dumps(_GEMINI_EXTENSION), encoding="utf-8")
    if with_license:
        (root / "LICENSE").write_text("Apache-2.0", encoding="utf-8")


class TestBootstrap:
    def test_carries_identity_and_context_into_the_spec_manifest(self, tmp_path):
        """Name/version/description and the Gemini context file transfer to plugin.json."""
        # Arrange
        _seed_gemini_extension(tmp_path)

        # Act
        result = bootstrap.bootstrap(tmp_path)

        # Assert
        google = result.plugin["extensions"]["com.google.cloud"]
        assert result.plugin["name"] == "demo"
        assert result.plugin["version"] == "1.0.0"
        assert google["gemini"]["contextFileName"] == "CTX.md"

    def test_converts_settings_to_config_and_infers_sensitivity(self, tmp_path):
        """Settings become config vars; secret-looking names are marked sensitive."""
        # Arrange
        _seed_gemini_extension(tmp_path)

        # Act
        config = bootstrap.bootstrap(tmp_path).plugin["extensions"]["com.google.cloud"]["config"]

        # Assert
        by_key = {var["key"]: var for var in config}
        assert by_key["DEMO_PASSWORD"]["sensitive"] is True
        assert "sensitive" not in by_key["DEMO_HOST"]

    def test_rewrites_mcp_command_to_spec_form(self, tmp_path):
        """The Gemini ${extensionPath} command becomes the spec's ./ command + cwd."""
        # Arrange
        _seed_gemini_extension(tmp_path)

        # Act
        server = bootstrap.bootstrap(tmp_path).mcp["mcpServers"]["demo"]

        # Assert
        assert server["command"] == "./toolbox"
        assert server["cwd"] == "${PLUGIN_ROOT}"
        assert server["type"] == "stdio"

    def test_sets_license_only_when_a_license_file_exists(self, tmp_path):
        """License is inferred from the presence of a LICENSE file, not assumed."""
        # Arrange
        _seed_gemini_extension(tmp_path, with_license=False)

        # Act
        plugin = bootstrap.bootstrap(tmp_path).plugin

        # Assert
        assert "license" not in plugin
