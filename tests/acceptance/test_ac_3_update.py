"""Acceptance tests for Restream update (AC 3.1, 3.2, 3.3, 3.4, 3.5)."""

import json
import subprocess
import sys
import time
from unittest.mock import patch, MagicMock

import pytest


def test_ac_3_1_update_mode_restream_patches_archives_exits_0(temp_config_dir, titles_file):
    """AC 3.1: update --mode restream -> PATCH title -> archive -> exit 0.

    Given: Valid Restream credentials and titles.txt with entries
    When: update_title_restream() is called
    Then: Next title is read from titles.txt
    And: PATCH sent to Restream API
    And: Used title archived
    """
    from youtube_updater.core import YouTubeUpdaterCore
    from youtube_updater.core.config_manager import ConfigManager
    from youtube_updater.core.title_manager import TitleManager
    from youtube_updater.core.restream_client import RestreamClient

    cm = ConfigManager(str(temp_config_dir))
    tm = TitleManager(
        str(titles_file),
        str(temp_config_dir / "applied-titles.txt"),
        str(temp_config_dir / "history.log"),
    )
    core = YouTubeUpdaterCore(config_manager=cm, title_manager=tm)

    mock_client = MagicMock(spec=RestreamClient)
    mock_client.update_stream_title.return_value = None
    core.restream_client = mock_client

    core.update_title_restream()

    mock_client.update_stream_title.assert_called_once_with("Test Title One")
    assert core.current_title == "Test Title One"
    # Title was archived
    applied = (temp_config_dir / "applied-titles.txt").read_text()
    assert "Test Title One" in applied


def test_ac_3_2_update_mode_youtube_preserves_existing(temp_config_dir):
    """AC 3.2: update --mode youtube preserves existing behavior.

    Given: Valid YouTube credentials
    When: update is called in youtube mode
    Then: Uses existing YouTube update path (unchanged)
    """
    from youtube_updater.core import YouTubeUpdaterCore
    from youtube_updater.core.config_manager import ConfigManager
    from youtube_updater.core.title_manager import TitleManager

    cm = ConfigManager(str(temp_config_dir))
    titles_file = temp_config_dir / "titles.txt"
    titles_file.write_text("YT Title\n")
    tm = TitleManager(
        str(titles_file),
        str(temp_config_dir / "applied-titles.txt"),
        str(temp_config_dir / "history.log"),
    )

    mock_yt = MagicMock()
    mock_yt.get_live_stream_info.return_value = {
        "is_live": True, "video_id": "vid1", "title": "Old"
    }
    core = YouTubeUpdaterCore(
        config_manager=cm, title_manager=tm, youtube_client=mock_yt
    )

    core.update_title()
    mock_yt.update_video_title.assert_called_once_with("vid1", "YT Title")


def test_ac_3_3_update_no_flag_defaults_youtube(temp_config_dir):
    """AC 3.3: update (no flag) defaults to youtube.

    Verified via CLI argument parsing: --mode defaults to 'youtube'.
    """
    from youtube_updater.cli import main
    import argparse

    # Parse args without --mode
    with patch("youtube_updater.cli.argparse.ArgumentParser.parse_args") as mock_parse:
        mock_parse.return_value = argparse.Namespace(
            command="update", wait=False, wait_timeout=90,
            mode="youtube", config_dir=str(temp_config_dir)
        )
        with patch("youtube_updater.cli.YouTubeUpdaterCLI") as mock_cli:
            mock_cli.return_value.run.return_value = 0
            # Just verify parse_args would produce mode=youtube by default
            pass

    # Direct test: argparse default
    from youtube_updater.cli import main as cli_main
    import io
    with patch("sys.argv", ["prog", "--config-dir", str(temp_config_dir), "update"]):
        with patch("youtube_updater.cli.YouTubeUpdaterCLI") as mock_cli:
            mock_cli.return_value.run.return_value = 0
            cli_main()
            args = mock_cli.return_value.run.call_args[0][0]
            assert args.mode == "youtube"


def test_ac_3_4_restream_wait_polls(temp_config_dir, titles_file):
    """AC 3.4: Restream mode + --wait polls until stream data available.

    Given: Valid Restream credentials and titles
    When: update --mode restream --wait is called
    Then: CLI polls until stream data is available, then updates
    """
    from youtube_updater.cli import YouTubeUpdaterCLI
    from youtube_updater.core.restream_client import RestreamClient
    from youtube_updater.exceptions.custom_exceptions import RestreamAPIError
    import argparse

    with patch("youtube_updater.core.factory.ComponentFactory.create_core") as mock_factory:
        mock_core = MagicMock()
        mock_factory.return_value = mock_core
        mock_core.config.ensure_restream_token.return_value = True
        mock_core.config.get_restream_token_path.return_value = str(
            temp_config_dir / "restream_token.json"
        )

        # First call: no stream, second call: success
        mock_restream = MagicMock(spec=RestreamClient)
        mock_core.restream_client = mock_restream
        mock_core.title_manager.get_next_title.return_value = "Polled Title"
        mock_core.title_manager.peek_next_title.return_value = "Polled Title"

        call_count = [0]

        def mock_update_restream():
            call_count[0] += 1
            if call_count[0] < 2:
                raise RestreamAPIError("Not streaming yet")
            mock_core.current_title = "Polled Title"

        mock_core.update_title_restream.side_effect = mock_update_restream

        cli = YouTubeUpdaterCLI.__new__(YouTubeUpdaterCLI)
        cli.core = mock_core

        args = argparse.Namespace(
            command="update", mode="restream", wait=True, wait_timeout=5
        )
        with patch("youtube_updater.cli._WAIT_POLL_INTERVAL", 0.01):
            result = cli.run(args)

    assert result == 0


def test_ac_3_5_missing_creds_error_email_exit_1(temp_config_dir):
    """AC 3.5: Missing/expired Restream creds -> error + exit 1.

    Given: No valid Restream credentials
    When: update --mode restream is run
    Then: Clear error message directing to restream-auth
    And: Exit code is 1

    Note: Email notification part verified in Phase 4.
    """
    from youtube_updater.cli import YouTubeUpdaterCLI
    from youtube_updater.exceptions.custom_exceptions import AuthenticationError
    import argparse

    with patch("youtube_updater.core.factory.ComponentFactory.create_core") as mock_factory:
        mock_core = MagicMock()
        mock_factory.return_value = mock_core
        mock_core.config.ensure_restream_token.return_value = False

        cli = YouTubeUpdaterCLI.__new__(YouTubeUpdaterCLI)
        cli.core = mock_core

        args = argparse.Namespace(
            command="update", mode="restream", wait=False, wait_timeout=90
        )
        result = cli.run(args)

    assert result == 1
