"""Integration tests for Restream update workflow."""

import os
from unittest.mock import MagicMock

from youtube_updater.core import YouTubeUpdaterCore
from youtube_updater.core.config_manager import ConfigManager
from youtube_updater.core.title_manager import TitleManager
from youtube_updater.core.restream_client import RestreamClient


class TestRestreamWorkflowIntegration:
    """Core with mock RestreamClient -> update title -> verify archive."""

    def test_update_restream_archives_title(self, tmp_path):
        """Full flow: get title, update via Restream, verify archived."""
        titles_file = tmp_path / "titles.txt"
        titles_file.write_text("Title A\nTitle B\n")
        applied_file = tmp_path / "applied-titles.txt"
        history_log = tmp_path / "history.log"

        cm = ConfigManager(str(tmp_path))
        tm = TitleManager(str(titles_file), str(applied_file), str(history_log))

        mock_restream = MagicMock(spec=RestreamClient)
        mock_restream.update_stream_title.return_value = None

        core = YouTubeUpdaterCore(config_manager=cm, title_manager=tm)
        core.restream_client = mock_restream

        core.update_title_restream()

        mock_restream.update_stream_title.assert_called_once_with("Title A")
        assert core.current_title == "Title A"
        assert "Title A" in applied_file.read_text()

        # Second call gets next title
        core.update_title_restream()
        mock_restream.update_stream_title.assert_called_with("Title B")
        assert core.current_title == "Title B"

    def test_youtube_path_unchanged_with_restream_on_core(self, tmp_path):
        """Adding restream_client to core doesn't affect YouTube update path."""
        titles_file = tmp_path / "titles.txt"
        titles_file.write_text("YT Title\n")
        applied_file = tmp_path / "applied-titles.txt"
        history_log = tmp_path / "history.log"

        cm = ConfigManager(str(tmp_path))
        tm = TitleManager(str(titles_file), str(applied_file), str(history_log))

        mock_yt = MagicMock()
        mock_yt.get_live_stream_info.return_value = {
            "is_live": True, "video_id": "v1", "title": "Old"
        }
        mock_restream = MagicMock(spec=RestreamClient)

        core = YouTubeUpdaterCore(
            config_manager=cm, title_manager=tm, youtube_client=mock_yt
        )
        core.restream_client = mock_restream

        # YouTube update should use YouTube path, not Restream
        core.update_title()
        mock_yt.update_video_title.assert_called_once_with("v1", "YT Title")
        mock_restream.update_stream_title.assert_not_called()
