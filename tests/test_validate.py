"""Schema validation of the com.google.cloud source bucket."""

from __future__ import annotations

from agent_plugin_sync import validate


class TestValidatePlugin:
    def test_accepts_a_well_formed_source(self, make_plugin, tmp_path):
        """A plugin with valid config and gemini fields passes validation."""
        # Arrange
        root = make_plugin(
            tmp_path,
            config=[{"key": "DEMO_HOST", "title": "Host", "description": "h"}],
            gemini={"contextFileName": "CTX.md"},
        )

        # Act
        result = validate.validate_plugin(root)

        # Assert
        assert result.ok, result.errors

    def test_rejects_config_key_that_is_not_an_env_var(self, make_plugin, tmp_path):
        """Config keys must be UPPER_SNAKE env var names."""
        # Arrange
        root = make_plugin(
            tmp_path,
            config=[{"key": "lowercase", "title": "Bad", "description": "d"}],
        )

        # Act
        result = validate.validate_plugin(root)

        # Assert
        assert not result.ok

    def test_rejects_config_var_missing_required_field(self, make_plugin, tmp_path):
        """A config var without a description fails (key/title/description required)."""
        # Arrange
        root = make_plugin(tmp_path, config=[{"key": "DEMO_HOST", "title": "Host"}])

        # Act
        result = validate.validate_plugin(root)

        # Assert
        assert not result.ok

    def test_rejects_unknown_field_in_gemini_bucket(self, make_plugin, tmp_path):
        """The gemini bucket is closed (additionalProperties: false)."""
        # Arrange
        root = make_plugin(tmp_path, gemini={"contextFileName": "CTX.md", "bogus": True})

        # Act
        result = validate.validate_plugin(root)

        # Assert
        assert not result.ok

    def test_error_messages_are_namespaced_for_context(self, make_plugin, tmp_path):
        """Errors are prefixed with com.google.cloud so authors can locate them."""
        # Arrange
        root = make_plugin(tmp_path, config=[{"key": "lowercase", "title": "Bad", "description": "d"}])

        # Act
        result = validate.validate_plugin(root)

        # Assert
        assert result.errors
        assert all(message.startswith("com.google.cloud") for message in result.errors)
