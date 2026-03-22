"""Integration tests for ConfigManager Restream and email config with real file I/O."""

import json
import os

from youtube_updater.core.config_manager import ConfigManager


class TestConfigManagerRestreamIntegration:
    """Real file I/O tests for ConfigManager Restream/email methods."""

    def test_restream_token_path_resolves_under_config_dir(self, tmp_path):
        cm = ConfigManager(str(tmp_path))
        path = cm.get_restream_token_path()
        assert os.path.dirname(path) == str(tmp_path)

    def test_email_config_save_load_roundtrip(self, tmp_path):
        cm = ConfigManager(str(tmp_path))
        config = {
            "connection_string": "endpoint=https://acs.azure.com/;key=abc123",
            "sender": "noreply@example.com",
            "recipient": "admin@example.com",
        }
        cm.save_email_config(config)

        # Verify file exists and is valid JSON
        email_path = tmp_path / "email_config.json"
        assert email_path.exists()
        with open(email_path) as f:
            on_disk = json.load(f)
        assert on_disk == config

        # Load via ConfigManager
        loaded = cm.get_email_config()
        assert loaded == config

    def test_email_config_overwrite(self, tmp_path):
        cm = ConfigManager(str(tmp_path))
        cm.save_email_config({"connection_string": "old", "sender": "a", "recipient": "b"})
        cm.save_email_config({"connection_string": "new", "sender": "x", "recipient": "y"})
        loaded = cm.get_email_config()
        assert loaded["connection_string"] == "new"

    def test_get_file_paths_includes_restream_token_with_correct_path(self, tmp_path):
        cm = ConfigManager(str(tmp_path))
        paths = cm.get_file_paths()
        assert paths["restream_token_path"] == os.path.join(str(tmp_path), "restream_token.json")

    def test_ensure_restream_token_false_then_true_after_write(self, tmp_path):
        cm = ConfigManager(str(tmp_path))
        assert cm.ensure_restream_token() is False
        with open(cm.get_restream_token_path(), "w") as f:
            json.dump({"access_token": "test"}, f)
        assert cm.ensure_restream_token() is True
