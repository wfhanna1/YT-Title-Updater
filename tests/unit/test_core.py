"""
Unit tests for YouTubeUpdaterCore (youtube_updater/core/__init__.py).

The core no longer accepts config_dir directly. It is composed via dependency
injection: config_manager, title_manager, auth_manager, youtube_client, logger.
"""

import unittest
from unittest.mock import MagicMock, patch

from youtube_updater.core import YouTubeUpdaterCore
from youtube_updater.exceptions.custom_exceptions import YouTubeAPIError


def _make_core(youtube_client=None, title_manager=None, config_manager=None):
    """Helper to build a YouTubeUpdaterCore with mocked dependencies."""
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


class TestYouTubeUpdaterCoreInitialization(unittest.TestCase):
    """Test initialization of YouTubeUpdaterCore."""

    def test_initial_state_not_live(self):
        """Test that is_live defaults to False."""
        core = _make_core()
        self.assertFalse(core.is_live)

    def test_initial_current_title_not_live(self):
        """Test that current_title defaults to 'Not Live'."""
        core = _make_core()
        self.assertEqual(core.current_title, "Not Live")

    def test_initial_status_and_type(self):
        """Test that initial status reflects Initializing state."""
        core = _make_core()
        self.assertEqual(core.status, "Initializing")
        self.assertEqual(core.status_type, "info")


class TestCheckLiveStatus(unittest.TestCase):
    """Test YouTubeUpdaterCore.check_live_status."""

    def test_check_live_status_no_youtube_client(self):
        """Test check_live_status sets error status when no client."""
        core = _make_core(youtube_client=None)
        core.check_live_status()
        self.assertEqual(core.status, "YouTube client not initialized")
        self.assertEqual(core.status_type, "error")
        self.assertFalse(core.is_live)

    def test_check_live_status_when_live(self):
        """Test check_live_status updates state when channel is live."""
        mock_client = MagicMock()
        mock_client.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid123",
            "title": "Live Stream Title",
        }
        core = _make_core(youtube_client=mock_client)
        core.check_live_status()
        self.assertTrue(core.is_live)
        self.assertEqual(core.current_title, "Live Stream Title")
        self.assertEqual(core.status, "Channel is live")
        self.assertEqual(core.status_type, "success")

    def test_check_live_status_when_not_live(self):
        """Test check_live_status updates state when channel is not live."""
        mock_client = MagicMock()
        mock_client.get_live_stream_info.return_value = {"is_live": False}
        core = _make_core(youtube_client=mock_client)
        core.check_live_status()
        self.assertFalse(core.is_live)
        self.assertEqual(core.current_title, "Not Live")
        self.assertEqual(core.status, "Channel is not live")
        self.assertEqual(core.status_type, "info")

    def test_check_live_status_api_exception_sets_error(self):
        """Test check_live_status catches exceptions and sets error status."""
        mock_client = MagicMock()
        mock_client.get_live_stream_info.side_effect = YouTubeAPIError("API failure")
        core = _make_core(youtube_client=mock_client)
        core.check_live_status()
        self.assertIn("Error checking live status", core.status)
        self.assertEqual(core.status_type, "error")


class TestUpdateTitle(unittest.TestCase):
    """Test YouTubeUpdaterCore.update_title."""

    def test_update_title_no_youtube_client(self):
        """Test update_title sets error status when no client."""
        core = _make_core(youtube_client=None)
        core.update_title()
        self.assertEqual(core.status, "YouTube client not initialized")
        self.assertEqual(core.status_type, "error")

    def test_update_title_when_not_live(self):
        """Test update_title sets warning when channel is not live."""
        mock_client = MagicMock()
        mock_client.get_live_stream_info.return_value = {"is_live": False}
        core = _make_core(youtube_client=mock_client)
        core.update_title()
        self.assertEqual(core.status, "Channel is not live")
        self.assertEqual(core.status_type, "warning")

    def test_update_title_no_titles_available(self):
        """Test update_title sets warning when title manager returns None."""
        mock_client = MagicMock()
        mock_client.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid123",
            "title": "Old Title",
        }
        mock_title_manager = MagicMock()
        mock_title_manager.get_next_title.return_value = None
        core = _make_core(youtube_client=mock_client, title_manager=mock_title_manager)
        core.update_title()
        self.assertIn("No titles available", core.status)
        self.assertEqual(core.status_type, "warning")

    def test_update_title_success(self):
        """Test update_title successfully updates title and archives it."""
        mock_client = MagicMock()
        mock_client.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid123",
            "title": "Old Title",
        }
        mock_client.update_video_title.return_value = None

        mock_title_manager = MagicMock()
        mock_title_manager.get_next_title.return_value = "New Title"

        core = _make_core(youtube_client=mock_client, title_manager=mock_title_manager)
        core.update_title()

        mock_client.update_video_title.assert_called_once_with("vid123", "New Title")
        mock_title_manager.archive_title.assert_called_once_with("New Title")
        self.assertEqual(core.current_title, "New Title")
        self.assertEqual(core.status, "Title updated to: New Title")
        self.assertEqual(core.status_type, "success")

    def test_update_title_api_error_sets_error_status(self):
        """Test update_title catches exceptions and sets error status."""
        mock_client = MagicMock()
        mock_client.get_live_stream_info.side_effect = YouTubeAPIError("API down")
        core = _make_core(youtube_client=mock_client)
        core.update_title()
        self.assertIn("Error updating title", core.status)
        self.assertEqual(core.status_type, "error")


class TestStatusProperty(unittest.TestCase):
    """Test status and status_type properties."""

    def test_status_and_type_are_readable(self):
        """Test that status and status_type properties are accessible."""
        core = _make_core()
        self.assertIsInstance(core.status, str)
        self.assertIsInstance(core.status_type, str)


class TestNextTitleProperty(unittest.TestCase):
    """Test the next_title property delegates to title_manager.peek_next_title."""

    def test_next_title_delegates_to_peek_next_title(self):
        """Test next_title property calls title_manager.peek_next_title."""
        mock_title_manager = MagicMock()
        mock_title_manager.peek_next_title.return_value = "Queued Title"
        core = _make_core(title_manager=mock_title_manager)
        self.assertEqual(core.next_title, "Queued Title")

    def test_next_title_returns_no_titles_available_when_none(self):
        """Test next_title returns 'No titles available' when peek returns None."""
        mock_title_manager = MagicMock()
        mock_title_manager.peek_next_title.return_value = None
        core = _make_core(title_manager=mock_title_manager)
        self.assertEqual(core.next_title, "No titles available")


if __name__ == "__main__":
    unittest.main()
