"""Generator behavior: turning the canonical model into per-harness files."""

from __future__ import annotations

from agent_plugin_sync import loader
from agent_plugin_sync.generators import antigravity, claude, codex, gemini
from tests.helpers import generated_json, generated_paths


class TestGeminiGenerator:
    def test_rewrites_relative_command_to_gemini_placeholder(self, make_plugin, tmp_path):
        """Gemini uses its own ${extensionPath} placeholder, not the spec's ./ command."""
        # Arrange
        root = make_plugin(
            tmp_path,
            mcp={"demo": {"type": "stdio", "command": "./toolbox", "args": ["--stdio"], "cwd": "${PLUGIN_ROOT}"}},
        )

        # Act
        manifest = generated_json(gemini.generate_gemini(loader.load_model(root)), "gemini-extension.json")

        # Assert
        assert manifest["mcpServers"]["demo"]["command"] == "${extensionPath}${/}toolbox"

    def test_drops_spec_only_server_keys(self, make_plugin, tmp_path):
        """`type` and `cwd` are spec-only and must not leak into the Gemini manifest."""
        # Arrange
        root = make_plugin(
            tmp_path,
            mcp={"demo": {"type": "stdio", "command": "npx", "cwd": "${PLUGIN_ROOT}"}},
        )

        # Act
        manifest = generated_json(gemini.generate_gemini(loader.load_model(root)), "gemini-extension.json")

        # Assert
        server = manifest["mcpServers"]["demo"]
        assert "type" not in server
        assert "cwd" not in server

    def test_maps_config_vars_to_settings(self, make_plugin, tmp_path):
        """Each config var becomes a Gemini `settings` entry keyed by envVar."""
        # Arrange
        root = make_plugin(
            tmp_path,
            config=[{"key": "DEMO_HOST", "title": "Host", "description": "the host"}],
        )

        # Act
        manifest = generated_json(gemini.generate_gemini(loader.load_model(root)), "gemini-extension.json")

        # Assert
        assert manifest["settings"] == [
            {"name": "Host", "description": "the host", "envVar": "DEMO_HOST"}
        ]

    def test_renames_single_server_to_configured_name(self, make_plugin, tmp_path):
        """`gemini.mcpServerName` renames the sole server key."""
        # Arrange
        root = make_plugin(
            tmp_path,
            gemini={"mcpServerName": "renamed"},
            mcp={"original": {"type": "stdio", "command": "npx"}},
        )

        # Act
        manifest = generated_json(gemini.generate_gemini(loader.load_model(root)), "gemini-extension.json")

        # Assert
        assert set(manifest["mcpServers"]) == {"renamed"}


class TestClaudeGenerator:
    def test_inlines_mcp_and_emits_no_separate_mcp_file(self, make_plugin, tmp_path):
        """Claude carries MCP inline in the manifest; no root .mcp.json is produced."""
        # Arrange
        root = make_plugin(
            tmp_path,
            mcp={"demo": {"type": "stdio", "command": "npx", "args": ["-y", "demo-mcp"]}},
        )

        # Act
        files = claude.generate_claude(loader.load_model(root))

        # Assert
        assert generated_paths(files) == {".claude-plugin/plugin.json"}
        manifest = generated_json(files, ".claude-plugin/plugin.json")
        assert manifest["mcpServers"]["demo"]["command"] == "npx"

    def test_retargets_plugin_root_placeholder(self, make_plugin, tmp_path):
        """The spec's ${PLUGIN_ROOT} becomes Claude's ${CLAUDE_PLUGIN_ROOT}."""
        # Arrange
        root = make_plugin(
            tmp_path,
            mcp={"demo": {"type": "stdio", "command": "npx", "cwd": "${PLUGIN_ROOT}"}},
        )

        # Act
        manifest = generated_json(
            claude.generate_claude(loader.load_model(root)), ".claude-plugin/plugin.json"
        )

        # Assert
        assert manifest["mcpServers"]["demo"]["cwd"] == "${CLAUDE_PLUGIN_ROOT}"

    def test_maps_config_vars_to_user_config(self, make_plugin, tmp_path):
        """Config vars become userConfig entries keyed by the lowercased env var."""
        # Arrange
        root = make_plugin(
            tmp_path,
            config=[{"key": "DEMO_PASSWORD", "title": "Password", "description": "pw", "sensitive": True}],
        )

        # Act
        manifest = generated_json(
            claude.generate_claude(loader.load_model(root)), ".claude-plugin/plugin.json"
        )

        # Assert
        assert manifest["userConfig"]["demo_password"] == {
            "title": "Password",
            "description": "pw",
            "type": "string",
            "sensitive": True,
        }

    def test_omits_mcp_when_plugin_has_none(self, make_plugin, tmp_path):
        """A plugin without MCP produces a manifest with no mcpServers key."""
        # Arrange
        root = make_plugin(tmp_path, config=[{"key": "X", "title": "X", "description": "x"}])

        # Act
        manifest = generated_json(
            claude.generate_claude(loader.load_model(root)), ".claude-plugin/plugin.json"
        )

        # Assert
        assert "mcpServers" not in manifest

    def test_includes_skills_path_when_skills_present(self, make_plugin, tmp_path):
        """A plugin that ships skills advertises the skills path."""
        # Arrange
        root = make_plugin(tmp_path, skills=True)

        # Act
        manifest = generated_json(
            claude.generate_claude(loader.load_model(root)), ".claude-plugin/plugin.json"
        )

        # Assert
        assert manifest["skills"] == "./skills/"


class TestCodexGenerator:
    def test_emits_legacy_manifest_pointing_at_root_relative_mcp_file(self, make_plugin, tmp_path):
        """Codex gets .codex-plugin/{plugin.json,.mcp.json}; the manifest's mcpServers
        path is root-relative so Codex resolves it correctly."""
        # Arrange
        root = make_plugin(tmp_path, mcp={"demo": {"type": "stdio", "command": "npx"}})

        # Act
        files = codex.generate_codex(loader.load_model(root))

        # Assert
        assert generated_paths(files) == {".codex-plugin/plugin.json", ".codex-plugin/.mcp.json"}
        manifest = generated_json(files, ".codex-plugin/plugin.json")
        assert manifest["mcpServers"] == "./.codex-plugin/.mcp.json"

    def test_maps_config_vars_to_env_vars(self, make_plugin, tmp_path):
        """Config keys become the server's env_vars (forwarded from the user env)."""
        # Arrange
        root = make_plugin(
            tmp_path,
            config=[
                {"key": "DEMO_HOST", "title": "Host", "description": "h"},
                {"key": "DEMO_PASSWORD", "title": "Password", "description": "p", "sensitive": True},
            ],
            mcp={"demo": {"type": "stdio", "command": "npx"}},
        )

        # Act
        mcp = generated_json(codex.generate_codex(loader.load_model(root)), ".codex-plugin/.mcp.json")

        # Assert
        assert mcp["mcpServers"]["demo"]["env_vars"] == ["DEMO_HOST", "DEMO_PASSWORD"]

    def test_drops_spec_only_type(self, make_plugin, tmp_path):
        """The spec-only `type` field must not leak into the legacy MCP file."""
        # Arrange
        root = make_plugin(tmp_path, mcp={"demo": {"type": "stdio", "command": "npx"}})

        # Act
        mcp = generated_json(codex.generate_codex(loader.load_model(root)), ".codex-plugin/.mcp.json")

        # Assert
        assert "type" not in mcp["mcpServers"]["demo"]

    def test_manifest_only_when_no_mcp(self, make_plugin, tmp_path):
        """A plugin without MCP produces just the manifest, with no mcpServers key."""
        # Arrange
        root = make_plugin(tmp_path, config=[{"key": "X", "title": "X", "description": "x"}])

        # Act
        files = codex.generate_codex(loader.load_model(root))

        # Assert
        assert generated_paths(files) == {".codex-plugin/plugin.json"}
        assert "mcpServers" not in generated_json(files, ".codex-plugin/plugin.json")

    def test_includes_skills_path_when_skills_present(self, make_plugin, tmp_path):
        """A plugin that ships skills advertises the skills path."""
        # Arrange
        root = make_plugin(tmp_path, skills=True)

        # Act
        manifest = generated_json(codex.generate_codex(loader.load_model(root)), ".codex-plugin/plugin.json")

        # Assert
        assert manifest["skills"] == "./skills"


class TestAntigravityGenerator:
    def test_emits_mcp_config_subset(self, make_plugin, tmp_path):
        """mcp_config.json mirrors mcpServers, dropping the spec-only `type`."""
        # Arrange
        root = make_plugin(
            tmp_path,
            mcp={"demo": {"type": "stdio", "command": "npx", "args": ["-y", "demo-mcp"]}},
        )

        # Act
        files = antigravity.generate_antigravity(loader.load_model(root))

        # Assert
        assert generated_paths(files) == {"mcp_config.json"}
        server = generated_json(files, "mcp_config.json")["mcpServers"]["demo"]
        assert server == {"command": "npx", "args": ["-y", "demo-mcp"]}

    def test_omits_file_when_no_mcp(self, make_plugin, tmp_path):
        """No MCP servers -> no mcp_config.json at all."""
        # Arrange
        root = make_plugin(tmp_path, config=[{"key": "X", "title": "X", "description": "x"}])

        # Act
        files = antigravity.generate_antigravity(loader.load_model(root))

        # Assert
        assert files == []
