"""
Integration tests for dynamic title generation with the title update workflow.

When the titles file is empty, TitleManager falls back to DefaultTitleGenerator
which produces a time-based title. We patch
youtube_updater.core.default_title_generator.datetime to control time.
"""

import os
import tempfile
import shutil
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytz

from youtube_updater.core import YouTubeUpdaterCore
from youtube_updater.core.title_manager import TitleManager

DATETIME_PATCH_TARGET = "youtube_updater.core.default_title_generator.datetime"


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


class TestDynamicTitleIntegration(unittest.TestCase):
    """Integration tests for dynamic title generation with title update workflow."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        # Start with an empty titles file
        with open(os.path.join(self.temp_dir, "titles.txt"), "w") as f:
            f.write("")

        self.mock_youtube = MagicMock()
        self.core = _build_core_with_real_title_manager(
            self.temp_dir, youtube_client=self.mock_youtube
        )

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_empty_titles_file_triggers_dynamic_title_saturday_night(self):
        """Test that an empty titles file triggers dynamic title generation on Saturday night."""
        est = pytz.timezone("US/Eastern")
        # Saturday July 15, 2023 at 8 PM Eastern
        saturday_8pm_est = est.localize(datetime(2023, 7, 15, 20, 0, 0))

        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "test_video_id",
            "title": "Current Live Title",
        }
        self.mock_youtube.update_video_title.return_value = None

        with patch(DATETIME_PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = saturday_8pm_est
            self.core.update_title()

        self.mock_youtube.update_video_title.assert_called_once_with(
            "test_video_id",
            "Saturday, July 15, 2023 - Vespers and Midnight Praises",
        )
        self.assertEqual(
            self.core.current_title,
            "Saturday, July 15, 2023 - Vespers and Midnight Praises",
        )

    def test_empty_titles_file_triggers_dynamic_title_weekday(self):
        """Test that an empty titles file triggers dynamic title generation on a weekday."""
        est = pytz.timezone("US/Eastern")
        # Wednesday July 12, 2023 at 3 PM Eastern
        wednesday_3pm_est = est.localize(datetime(2023, 7, 12, 15, 0, 0))

        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "test_video_id",
            "title": "Current Live Title",
        }
        self.mock_youtube.update_video_title.return_value = None

        with patch(DATETIME_PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = wednesday_3pm_est
            self.core.update_title()

        self.mock_youtube.update_video_title.assert_called_once_with(
            "test_video_id",
            "Wednesday, July 12, 2023 - Divine Liturgy",
        )

    def test_titles_available_uses_file_title_not_dynamic(self):
        """Test that when titles are available in the file, dynamic generation is skipped."""
        # Write actual titles to the file
        with open(os.path.join(self.temp_dir, "titles.txt"), "w") as f:
            f.write("My Custom Title\nAnother Title\n")

        # Rebuild the core so TitleManager loads the new file contents
        self.core = _build_core_with_real_title_manager(
            self.temp_dir, youtube_client=self.mock_youtube
        )

        self.mock_youtube.get_live_stream_info.return_value = {
            "is_live": True,
            "video_id": "test_video_id",
            "title": "Current Live Title",
        }
        self.mock_youtube.update_video_title.return_value = None

        self.core.update_title()

        self.mock_youtube.update_video_title.assert_called_once_with(
            "test_video_id", "My Custom Title"
        )
        self.assertEqual(self.core.current_title, "My Custom Title")


if __name__ == "__main__":
    unittest.main()
