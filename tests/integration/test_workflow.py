"""
Integration tests for the complete application workflow.

The GUI (PyQt6) has been removed. These tests verify the end-to-end
workflow from YouTubeUpdaterCore through TitleManager to the YouTube
client mock, simulating going live, updating titles, and going offline.
"""

import os
import tempfile
import shutil
import unittest
from unittest.mock import MagicMock, patch

from youtube_updater.core import YouTubeUpdaterCore
from youtube_updater.core.title_manager import TitleManager


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


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration test for the complete workflow of the application."""

    def setUp(self):
        """Set up test environment for each test."""
        self.test_dir = tempfile.mkdtemp()

        with open(os.path.join(self.test_dir, "titles.txt"), "w") as f:
            f.write("Test Title 1\nTest Title 2\nTest Title 3\n")

        with open(os.path.join(self.test_dir, "applied-titles.txt"), "w") as f:
            f.write("")

        with open(os.path.join(self.test_dir, "history.log"), "w") as f:
            f.write("")

        self.mock_youtube = MagicMock()
        self.core = _build_core_with_real_title_manager(
            self.test_dir, youtube_client=self.mock_youtube
        )

    def tearDown(self):
        """Clean up after each test."""
        shutil.rmtree(self.test_dir)

    def test_initial_state_not_live(self):
        """Test that the core starts in a not-live state."""
        self.assertFalse(self.core.is_live)
        self.assertEqual(self.core.current_title, "Not Live")

    def test_simulate_going_live(self):
        """Test transitioning from not live to live."""
        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid_123",
            "title": "Current Live Title",
        }

        self.core.check_live_status()

        self.assertTrue(self.core.is_live)
        self.assertEqual(self.core.current_title, "Current Live Title")
        self.assertEqual(self.core.status, "Channel is live")

    def test_update_title_after_going_live(self):
        """Test updating title when live, then verifying the title was changed."""
        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid_123",
            "title": "Current Live Title",
        }
        self.mock_youtube.update_video_title.return_value = None

        self.core.check_live_status()
        self.assertTrue(self.core.is_live)

        self.core.update_title()

        self.mock_youtube.update_video_title.assert_called_once_with(
            "vid_123", "Test Title 1"
        )
        self.assertEqual(self.core.current_title, "Test Title 1")
        self.assertEqual(self.core.status_type, "success")

    def test_title_rotation_after_update(self):
        """Test that after updating, the titles file rotates correctly."""
        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid_123",
            "title": "Current Title",
        }
        self.mock_youtube.update_video_title.return_value = None

        self.core.update_title()

        # After applying Title 1, the file should rotate it to the end
        with open(os.path.join(self.test_dir, "titles.txt"), "r") as f:
            remaining = [line.strip() for line in f if line.strip()]

        self.assertEqual(remaining, ["Test Title 2", "Test Title 3", "Test Title 1"])

    def test_simulate_going_offline(self):
        """Test transitioning from live back to not live."""
        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid_123",
            "title": "Live Title",
        }
        self.core.check_live_status()
        self.assertTrue(self.core.is_live)

        self.mock_youtube.get_live_stream_info.return_value = {"is_live": False}
        self.core.check_live_status()
        self.assertFalse(self.core.is_live)
        self.assertEqual(self.core.current_title, "Not Live")
        self.assertEqual(self.core.status, "Channel is not live")

    def test_applied_titles_recorded_after_update(self):
        """Test that applied-titles.txt is updated after a title change."""
        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid_123",
            "title": "Current Title",
        }
        self.mock_youtube.update_video_title.return_value = None

        self.core.update_title()

        with open(os.path.join(self.test_dir, "applied-titles.txt"), "r") as f:
            applied = f.read()
        self.assertIn("Test Title 1", applied)

    def test_history_log_recorded_after_update(self):
        """Test that history.log is updated after a title change."""
        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "vid_123",
            "title": "Current Title",
        }
        self.mock_youtube.update_video_title.return_value = None

        self.core.update_title()

        with open(os.path.join(self.test_dir, "history.log"), "r") as f:
            history = f.read()
        self.assertTrue(len(history) > 0)

    def test_update_when_not_live_does_not_change_title(self):
        """Test that calling update_title when not live does not change anything."""
        self.mock_youtube.get_live_stream_info.return_value = {"is_live": False}

        self.core.update_title()

        self.mock_youtube.update_video_title.assert_not_called()
        self.assertEqual(self.core.status, "Channel is not live")
        self.assertEqual(self.core.status_type, "warning")


if __name__ == "__main__":
    unittest.main()
