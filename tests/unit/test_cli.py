"""Unit tests for YouTubeUpdaterCLI."""
import sys
import argparse
from unittest import TestCase, mock
from unittest.mock import MagicMock, patch, call

from youtube_updater.cli import YouTubeUpdaterCLI


def _make_core_mock(is_live=True, current_title="Test Title"):
    """Build a mock YouTubeUpdaterCore with sensible defaults."""
    core = MagicMock()
    core.is_live = is_live
    core.current_title = current_title
    core.status = "ok"
    core.status_type = "success"
    core.next_title = "Next Title"
    # get_live_stream_info returns a dict used by update_title
    core.youtube_client = MagicMock()
    core.youtube_client.get_live_stream_info.return_value = {
        "is_live": is_live,
        "title": current_title,
        "video_id": "vid123",
    }
    return core


def _make_args(command="update", wait=False, wait_timeout=90):
    """Build a minimal argparse Namespace for CLI tests."""
    return argparse.Namespace(
        command=command,
        wait=wait,
        wait_timeout=wait_timeout,
    )


class TestUpdateDoesNotDoubleFetchStreamInfo(TestCase):
    """Task 1: update flow must call get_live_stream_info exactly once."""

    @patch("youtube_updater.cli.ComponentFactory.create_core")
    def test_update_does_not_double_fetch_stream_info(self, mock_create_core):
        """get_live_stream_info should be called exactly ONCE during _handle_update.

        The CLI calls check_live_status() which calls get_live_stream_info()
        internally, then passes the result to update_title().  update_title()
        must use the provided stream_info and NOT make a second API call.
        """
        from unittest.mock import MagicMock
        from youtube_updater.core import YouTubeUpdaterCore
        from youtube_updater.core.title_manager import TitleManager
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            titles_file = str(tmp / "titles.txt")
            applied_file = str(tmp / "applied-titles.txt")
            history_file = str(tmp / "history.log")

            with open(titles_file, "w") as f:
                f.write("Test Title\n")
            for p in (applied_file, history_file):
                open(p, "w").close()

            title_manager = TitleManager(titles_file, applied_file, history_file)

            config = MagicMock()
            config.get_client_secrets_path.return_value = str(tmp / "client_secrets.json")
            config.get_file_paths.return_value = {
                "titles_file": titles_file,
                "applied_titles_file": applied_file,
                "history_log": history_file,
                "token_path": str(tmp / "token.pickle"),
            }

            # youtube_client with a tracked get_live_stream_info
            youtube_client = MagicMock()
            stream_info = {"is_live": True, "title": "Old Title", "video_id": "vid123"}
            youtube_client.get_live_stream_info.return_value = stream_info

            core = YouTubeUpdaterCore(
                config_manager=config,
                title_manager=title_manager,
                youtube_client=youtube_client,
            )
            mock_create_core.return_value = core

            cli = YouTubeUpdaterCLI()
            args = _make_args(command="update")
            result = cli.run(args)

            self.assertEqual(result, 0)
            # get_live_stream_info must have been called exactly once
            youtube_client.get_live_stream_info.assert_called_once()


class TestWaitFlag(TestCase):
    """Task 2: --wait flag retry loop."""

    @patch("youtube_updater.cli.time.sleep")
    @patch("youtube_updater.cli.ComponentFactory.create_core")
    def test_wait_flag_retries_until_live(self, mock_create_core, mock_sleep):
        """With --wait, polls every 10s and succeeds on 3rd attempt."""
        core = MagicMock()
        call_count = {"n": 0}

        # First two check_live_status calls report not live; third reports live
        def side_effect_check():
            call_count["n"] += 1
            if call_count["n"] < 3:
                core.is_live = False
                core.current_title = "Not Live"
            else:
                core.is_live = True
                core.current_title = "Live Title"

        core.check_live_status.side_effect = side_effect_check
        core.is_live = False
        core.current_title = "Not Live"
        core.status = "ok"
        core.status_type = "info"
        core.next_title = "Next"
        mock_create_core.return_value = core

        cli = YouTubeUpdaterCLI()
        args = _make_args(command="update", wait=True, wait_timeout=90)
        result = cli.run(args)

        self.assertEqual(result, 0)
        # Should have slept at least once (between retries)
        self.assertTrue(mock_sleep.called)
        # check_live_status called 3 times (2 failures + 1 success)
        self.assertEqual(call_count["n"], 3)

    @patch("youtube_updater.cli.time.sleep")
    @patch("youtube_updater.cli.ComponentFactory.create_core")
    def test_wait_flag_timeout_exits_with_code_1(self, mock_create_core, mock_sleep):
        """With --wait, exits with code 1 after timeout when never live."""
        core = MagicMock()
        core.is_live = False
        core.current_title = "Not Live"
        core.status = "ok"
        core.status_type = "info"
        core.next_title = "Next"
        core.youtube_client = MagicMock()
        core.youtube_client.get_live_stream_info.return_value = {
            "is_live": False,
            "title": "Not Live",
            "video_id": None,
        }
        mock_create_core.return_value = core

        cli = YouTubeUpdaterCLI()
        # Short timeout so the test runs quickly (30s), polling every 10s
        args = _make_args(command="update", wait=True, wait_timeout=30)
        result = cli.run(args)

        self.assertEqual(result, 1)
        # sleep should have been called (retries happened before timeout)
        self.assertTrue(mock_sleep.called)

    @patch("youtube_updater.cli.ComponentFactory.create_core")
    def test_no_wait_flag_exits_immediately(self, mock_create_core):
        """Without --wait, exits immediately with code 1 when not live."""
        core = _make_core_mock(is_live=False)
        mock_create_core.return_value = core

        cli = YouTubeUpdaterCLI()
        args = _make_args(command="update", wait=False)
        result = cli.run(args)

        self.assertEqual(result, 1)
        # check_live_status called once, no retries
        core.check_live_status.assert_called_once()


class TestStatusCommand(TestCase):
    """Ensure the existing status command still works after refactoring."""

    @patch("youtube_updater.cli.ComponentFactory.create_core")
    def test_status_command_returns_0(self, mock_create_core):
        core = _make_core_mock(is_live=True)
        mock_create_core.return_value = core

        cli = YouTubeUpdaterCLI()
        args = argparse.Namespace(command="status", wait=False, wait_timeout=90)
        result = cli.run(args)

        self.assertEqual(result, 0)
