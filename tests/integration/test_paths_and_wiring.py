"""Integration tests for paths with spaces and real component wiring."""

import json
import os
import time

from youtube_updater.core.config_manager import ConfigManager
from youtube_updater.core.title_manager import TitleManager
from youtube_updater.core.restream_auth import RestreamAuth
from youtube_updater.core.factory import ComponentFactory
from youtube_updater.core import YouTubeUpdaterCore


class TestPathsWithSpaces:
    """All file operations work with spaces in directory names."""

    def test_config_manager_with_spaces(self, tmp_path):
        config_dir = tmp_path / "St Mary Church" / "config dir"
        cm = ConfigManager(str(config_dir))
        assert config_dir.exists()
        paths = cm.get_file_paths()
        assert "St Mary Church" in paths["titles_file"]

    def test_title_manager_with_spaces(self, tmp_path):
        config_dir = tmp_path / "path with spaces"
        config_dir.mkdir()
        titles = config_dir / "titles.txt"
        titles.write_text("Title One\nTitle Two\n")
        applied = config_dir / "applied-titles.txt"
        history = config_dir / "history.log"

        tm = TitleManager(str(titles), str(applied), str(history))
        t = tm.get_next_title()
        assert t == "Title One"
        tm.archive_title(t)
        assert "Title One" in applied.read_text()

    def test_restream_auth_with_spaces(self, tmp_path):
        config_dir = tmp_path / "St Mary" / "App Data"
        config_dir.mkdir(parents=True)
        token_path = str(config_dir / "restream_token.json")

        auth = RestreamAuth(client_id="cid", client_secret="csec", token_path=token_path)
        # No token file yet
        assert auth.load_token() is None

        # Write and load
        token_data = {
            "access_token": "at", "refresh_token": "rt",
            "client_id": "cid", "expires_at": time.time() + 3600,
        }
        with open(token_path, "w") as f:
            json.dump(token_data, f)
        loaded = auth.load_token()
        assert loaded["access_token"] == "at"

    def test_email_config_with_spaces(self, tmp_path):
        config_dir = tmp_path / "church config"
        cm = ConfigManager(str(config_dir))
        cm.save_email_config({
            "connection_string": "endpoint=https://x/;accesskey=k",
            "sender": "a@b.com",
            "recipients": ["c@d.com"],
        })
        loaded = cm.get_email_config()
        assert loaded["sender"] == "a@b.com"


class TestComponentFactoryIntegration:
    """Test real ComponentFactory wiring without mocks."""

    def test_create_core_no_credentials(self, tmp_path):
        """Factory creates core with None youtube_client when no creds."""
        core = ComponentFactory.create_core(str(tmp_path))
        assert isinstance(core, YouTubeUpdaterCore)
        assert core.youtube_client is None
        assert core.auth_manager is None
        assert core.restream_client is None
        assert core.title_manager is not None
        assert core.config is not None

    def test_create_core_titles_file_created(self, tmp_path):
        """Factory creates required files in config dir."""
        ComponentFactory.create_core(str(tmp_path))
        assert (tmp_path / "titles.txt").exists()
        assert (tmp_path / "applied-titles.txt").exists()
        assert (tmp_path / "history.log").exists()

    def test_create_core_title_rotation_works(self, tmp_path):
        """Titles written before factory creation are readable."""
        (tmp_path / "titles.txt").write_text("Pre-Written Title\n")
        core = ComponentFactory.create_core(str(tmp_path))
        title = core.title_manager.get_next_title()
        assert title == "Pre-Written Title"

    def test_create_core_restream_paths_available(self, tmp_path):
        """Config manager has restream/email paths after factory creation."""
        core = ComponentFactory.create_core(str(tmp_path))
        paths = core.config.get_file_paths()
        assert "restream_token_path" in paths
        assert "email_config_path" in paths

    def test_create_core_with_spaces_in_path(self, tmp_path):
        """Factory works with spaces in config dir path."""
        config_dir = tmp_path / "St Mary Church"
        core = ComponentFactory.create_core(str(config_dir))
        assert core.title_manager is not None
        assert config_dir.exists()


class TestRestreamUpdateIntegration:
    """Integration: real core + real title manager + mock restream client."""

    def test_update_restream_rotates_and_archives(self, tmp_path):
        """Full flow: get title, update via restream, verify rotation + archive."""
        from unittest.mock import MagicMock
        from youtube_updater.core.restream_client import RestreamClient

        (tmp_path / "titles.txt").write_text("First\nSecond\nThird\n")
        core = ComponentFactory.create_core(str(tmp_path))
        mock_client = MagicMock(spec=RestreamClient)
        core.restream_client = mock_client

        # First update
        core.update_title_restream()
        assert core.current_title == "First"
        mock_client.update_stream_title.assert_called_with("First")

        # Verify rotation
        remaining = (tmp_path / "titles.txt").read_text().strip().split("\n")
        assert remaining == ["Second", "Third", "First"]

        # Verify archive
        applied = (tmp_path / "applied-titles.txt").read_text()
        assert "First" in applied

        # Second update
        core.update_title_restream()
        assert core.current_title == "Second"

    def test_update_restream_with_unicode_title(self, tmp_path):
        """Unicode titles flow through the full update path."""
        from unittest.mock import MagicMock
        from youtube_updater.core.restream_client import RestreamClient

        (tmp_path / "titles.txt").write_text("القداس الإلهي - Sunday Liturgy\n")
        core = ComponentFactory.create_core(str(tmp_path))
        mock_client = MagicMock(spec=RestreamClient)
        core.restream_client = mock_client

        core.update_title_restream()
        mock_client.update_stream_title.assert_called_with("القداس الإلهي - Sunday Liturgy")
        assert "القداس" in (tmp_path / "applied-titles.txt").read_text()
