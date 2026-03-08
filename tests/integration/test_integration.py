"""
Integration tests for YouTube Title Updater.

The GUI (PyQt6) has been removed. These tests now verify integration
between YouTubeUpdaterCore, TitleManager, and YouTubeClient using mocks
where the real YouTube API is not available.
"""

import os
import tempfile
import shutil
import unittest
from unittest.mock import MagicMock, patch

from youtube_updater.core import YouTubeUpdaterCore
from youtube_updater.core.title_manager import TitleManager
from youtube_updater.exceptions.custom_exceptions import YouTubeAPIError


def _build_core_with_real_title_manager(temp_dir, youtube_client=None):
    """Build a YouTubeUpdaterCore with a real TitleManager backed by temp files."""
    config_manager = MagicMock()
    config_manager.get_client_secrets_path.return_value = os.path.join(
        temp_dir, "client_secrets.json"
    )
    config_manager.get_file_paths.return_value = {
        "titles_file": os.path.join(temp_dir, "titles.txt"),
        "applied_titles_file": os.path.join(temp_dir, "applied-titles.txt"),
        "history_log": os.path.join(temp_dir, "history.log"),
        "token_path": os.path.join(temp_dir, "token.pickle"),
    }

    title_manager = TitleManager(
        titles_file=os.path.join(temp_dir, "titles.txt"),
        applied_titles_file=os.path.join(temp_dir, "applied-titles.txt"),
        history_log=os.path.join(temp_dir, "history.log"),
    )

    return YouTubeUpdaterCore(
        config_manager=config_manager,
        title_manager=title_manager,
        youtube_client=youtube_client,
    )


class TestCoreIntegration(unittest.TestCase):
    """Integration tests for YouTubeUpdaterCore with TitleManager."""

    def setUp(self):
        """Set up test environment with a temporary directory."""
        self.temp_dir = tempfile.mkdtemp()

        with open(os.path.join(self.temp_dir, "titles.txt"), "w") as f:
            f.write("Title 1\nTitle 2\nTitle 3\n")

        self.mock_youtube = MagicMock()
        self.core = _build_core_with_real_title_manager(
            self.temp_dir, youtube_client=self.mock_youtube
        )

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_check_live_status_live_integration(self):
        """Test that check_live_status correctly sets is_live and current_title."""
        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid_abc",
            "title": "Live Stream Title",
        }

        self.core.check_live_status()

        self.assertTrue(self.core.is_live)
        self.assertEqual(self.core.current_title, "Live Stream Title")
        self.assertEqual(self.core.status, "Channel is live")

    def test_check_live_status_not_live_integration(self):
        """Test check_live_status sets correct state when not live."""
        self.mock_youtube.get_live_stream_info.return_value = {"is_live": False}

        self.core.check_live_status()

        self.assertFalse(self.core.is_live)
        self.assertEqual(self.core.current_title, "Not Live")

    def test_update_title_reads_from_titles_file(self):
        """Test that update_title reads the next title from the real titles file."""
        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid_abc",
            "title": "Old Title",
        }
        self.mock_youtube.update_video_title.return_value = None

        self.core.update_title()

        self.mock_youtube.update_video_title.assert_called_once_with("vid_abc", "Title 1")
        self.assertEqual(self.core.current_title, "Title 1")
        self.assertEqual(self.core.status_type, "success")

    def test_update_title_archives_applied_title(self):
        """Test that update_title records the used title in applied-titles.txt."""
        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid_abc",
            "title": "Old Title",
        }
        self.mock_youtube.update_video_title.return_value = None

        self.core.update_title()

        with open(os.path.join(self.temp_dir, "applied-titles.txt"), "r") as f:
            content = f.read()
        self.assertIn("Title 1", content)

    def test_full_workflow_check_then_update(self):
        """Test a complete check-then-update workflow."""
        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid_abc",
            "title": "Current Title",
        }
        self.mock_youtube.update_video_title.return_value = None

        self.core.check_live_status()
        self.assertTrue(self.core.is_live)

        self.core.update_title()
        self.assertEqual(self.core.status_type, "success")
        self.mock_youtube.update_video_title.assert_called_once()

    def test_status_integration_error_propagates(self):
        """Test that API errors propagate as exceptions."""
        self.mock_youtube.get_live_stream_info.side_effect = YouTubeAPIError(
            "Connection refused"
        )

        with self.assertRaises(YouTubeAPIError):
            self.core.check_live_status()


if __name__ == "__main__":
    unittest.main()
