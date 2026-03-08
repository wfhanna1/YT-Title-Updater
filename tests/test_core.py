"""
Tests for the YouTubeUpdaterCore orchestration class.

YouTubeUpdaterCore now uses dependency injection (config_manager,
title_manager, auth_manager, youtube_client, logger).
"""

import unittest
from unittest.mock import patch, MagicMock
import os

from youtube_updater.core import YouTubeUpdaterCore
from youtube_updater.exceptions.custom_exceptions import YouTubeAPIError


def _build_core(youtube_client=None, title_manager=None, config_manager=None):
    """Build a YouTubeUpdaterCore with mocked collaborators."""
    if config_manager is None:
        config_manager = MagicMock()
        config_manager.get_client_secrets_path.return_value = "/fake/client_secrets.json"
        config_manager.get_file_paths.return_value = {
            "titles_file": "/fake/titles.txt",
            "applied_titles_file": "/fake/applied-titles.txt",
            "history_log": "/fake/history.log",
            "token_path": "/fake/token.pickle",
        }

    if title_manager is None:
        title_manager = MagicMock()
        title_manager.get_next_title.return_value = "Default Title"

    return YouTubeUpdaterCore(
        config_manager=config_manager,
        title_manager=title_manager,
        youtube_client=youtube_client,
    )


class TestYouTubeUpdaterCore(unittest.TestCase):
    """Test cases for YouTubeUpdaterCore class."""

    def setUp(self):
        """Set up test environment."""
        self.mock_youtube_client = MagicMock()
        self.mock_title_manager = MagicMock()
        self.mock_title_manager.get_next_title.return_value = "Test Title 1"
        self.core = _build_core(
            youtube_client=self.mock_youtube_client,
            title_manager=self.mock_title_manager,
        )

    def test_initialization(self):
        """Test initialization of YouTubeUpdaterCore."""
        core = _build_core()
        self.assertEqual(core.status_type, "info")
        self.assertEqual(core.status, "Initializing")
        self.assertFalse(core.is_live)

    def test_set_status(self):
        """Test setting status message and type via StatusManager."""
        self.core.status_manager.set_status("Test message", "success")
        self.assertEqual(self.core.status, "Test message")
        self.assertEqual(self.core.status_type, "success")

        with self.assertRaises(ValueError):
            self.core.status_manager.set_status("Test message", "invalid_type")

    def test_check_live_status_no_youtube(self):
        """Test check_live_status returns None when YouTube client is not initialized."""
        core = _build_core(youtube_client=None)
        result = core.check_live_status()
        self.assertIsNone(result)
        self.assertEqual(core.status, "YouTube client not initialized")
        self.assertEqual(core.status_type, "error")

    def test_check_live_status_with_live_stream(self):
        """Test check_live_status when channel is live."""
        self.mock_youtube_client.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "test_video_id",
            "title": "Test Title",
        }

        self.core.check_live_status()
        self.assertTrue(self.core.is_live)
        self.assertEqual(self.core.status, "Channel is live")

    def test_check_live_status_no_broadcast(self):
        """Test check_live_status when no broadcast is active."""
        self.mock_youtube_client.get_live_stream_info.return_value = {"is_live": False}

        self.core.check_live_status()
        self.assertFalse(self.core.is_live)
        self.assertEqual(self.core.status, "Channel is not live")
        self.assertEqual(self.core.status_type, "info")

    def test_update_title_success(self):
        """Test successful title update."""
        self.mock_youtube_client.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "test_video_id",
            "title": "Old Title",
        }
        self.mock_youtube_client.update_video_title.return_value = None
        self.mock_title_manager.get_next_title.return_value = "New Title"

        self.core.update_title()
        self.assertEqual(self.core.status, "Title updated to: New Title")
        self.assertEqual(self.core.status_type, "success")
        self.mock_title_manager.archive_title.assert_called_once_with("New Title")

    def test_update_title_not_live(self):
        """Test update_title when channel is not live."""
        self.mock_youtube_client.get_live_stream_info.return_value = {"is_live": False}

        self.core.update_title()
        self.assertEqual(self.core.status, "Channel is not live")
        self.assertEqual(self.core.status_type, "warning")

    def test_update_title_no_client(self):
        """Test update_title raises when YouTube client is not initialized."""
        core = _build_core(youtube_client=None)
        with self.assertRaises(Exception):
            core.update_title()
        self.assertEqual(core.status, "YouTube client not initialized")
        self.assertEqual(core.status_type, "error")

    def test_add_title(self):
        """Test adding a title delegates to title_manager."""
        self.core.add_title("New Title")
        self.mock_title_manager.add_title.assert_called_once_with("New Title")
        self.assertEqual(self.core.status, "Title added: New Title")
        self.assertEqual(self.core.status_type, "success")

    def test_get_next_title_delegates_to_title_manager(self):
        """Test get_next_title delegates to title_manager."""
        self.mock_title_manager.get_next_title.return_value = "Test Title 1"
        result = self.core.get_next_title()
        self.assertEqual(result, "Test Title 1")

    @patch("youtube_updater.core.open_path")
    def test_open_config_dir(self, mock_open_path):
        """Test open_config_dir calls open_path with the config directory."""
        self.core.config.get_client_secrets_path.return_value = "/fake/dir/client_secrets.json"
        self.core.open_config_dir()
        mock_open_path.assert_called_once_with("/fake/dir")

    @patch("youtube_updater.core.open_path")
    def test_open_titles_file(self, mock_open_path):
        """Test open_titles_file calls open_path with the titles file path."""
        self.core.config.get_file_paths.return_value = {
            "titles_file": "/fake/titles.txt"
        }
        self.core.open_titles_file()
        mock_open_path.assert_called_once_with("/fake/titles.txt")


if __name__ == "__main__":
    unittest.main()
