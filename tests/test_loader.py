"""Plugin discovery and model loading."""

from __future__ import annotations

from agent_plugin_sync import loader


class TestDiscoverRoots:
    def test_returns_root_itself_for_a_single_plugin(self, make_plugin, tmp_path):
        """A directory containing plugin.json is itself the one plugin root."""
        # Arrange
        make_plugin(tmp_path)

        # Act
        roots = loader.discover_roots(tmp_path)

        # Assert
        assert roots == [tmp_path]

    def test_returns_each_subdirectory_in_a_monorepo(self, make_plugin, tmp_path):
        """With no plugin.json at the root, every plugin subdirectory is found."""
        # Arrange
        make_plugin(tmp_path / "plugins" / "a", name="a")
        make_plugin(tmp_path / "plugins" / "b", name="b")

        # Act
        roots = loader.discover_roots(tmp_path)

        # Assert
        assert sorted(root.name for root in roots) == ["a", "b"]

    def test_ignores_generated_manifests_in_dot_directories(self, make_plugin, tmp_path):
        """A generated .claude-plugin/plugin.json must not count as a second plugin."""
        # Arrange
        plugin_root = make_plugin(tmp_path / "plugins" / "a", name="a")
        generated = plugin_root / ".claude-plugin" / "plugin.json"
        generated.parent.mkdir()
        generated.write_text("{}", encoding="utf-8")

        # Act
        roots = loader.discover_roots(tmp_path)

        # Assert
        assert roots == [plugin_root]


class TestLoadModel:
    def test_reads_manifest_mcp_extension_and_skills(self, make_plugin, tmp_path):
        """load_model surfaces plugin.json, mcp.json, the google bucket, and skills presence."""
        # Arrange
        root = make_plugin(
            tmp_path,
            config=[{"key": "DEMO_HOST", "title": "Host", "description": "h"}],
            mcp={"demo": {"type": "stdio", "command": "npx"}},
            skills=True,
        )

        # Act
        loaded = loader.load_model(root)

        # Assert
        assert loaded.plugin.name == "demo"
        assert loaded.mcp.mcp_servers["demo"].command == "npx"
        assert loaded.plugin.google.config[0].key == "DEMO_HOST"
        assert loaded.has_skills is True

    def test_mcp_is_none_when_absent(self, make_plugin, tmp_path):
        """A plugin without mcp.json loads with mcp set to None."""
        # Arrange
        root = make_plugin(tmp_path)

        # Act
        loaded = loader.load_model(root)

        # Assert
        assert loaded.mcp is None
        assert loaded.has_skills is False
