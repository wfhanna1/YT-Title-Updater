"""Unit tests for CLI Restream commands."""

import argparse
from unittest.mock import patch, MagicMock

import pytest

from youtube_updater.cli import YouTubeUpdaterCLI
from youtube_updater.exceptions.custom_exceptions import (
    AuthenticationError,
    RestreamAPIError,
)


@pytest.fixture
def cli_with_mock_core(tmp_path):
    """Create a CLI instance with a mocked core."""
    with patch("youtube_updater.core.factory.ComponentFactory.create_core") as mock_factory:
        mock_core = MagicMock()
        mock_core.config.config_dir = tmp_path
        mock_core.config.ensure_restream_token.return_value = True
        mock_core.config.get_restream_token_path.return_value = str(
            tmp_path / "restream_token.json"
        )
        mock_core.restream_client = None
        mock_factory.return_value = mock_core

        cli = YouTubeUpdaterCLI(str(tmp_path))
        yield cli, mock_core


class TestRestreamStatus:
    def test_restream_status_lists_channels(self, cli_with_mock_core, capsys):
        cli, mock_core = cli_with_mock_core
        mock_client = MagicMock()
        mock_client.get_channels.return_value = [
            {"displayName": "My YT", "platform": "youtube", "active": True},
            {"displayName": "My FB", "platform": "facebook", "active": False},
        ]
        mock_core.restream_client = mock_client

        args = argparse.Namespace(command="restream-status")
        result = cli.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "youtube" in captured.out
        assert "facebook" in captured.out

    def test_restream_status_no_creds(self, cli_with_mock_core, capsys):
        cli, mock_core = cli_with_mock_core
        mock_core.config.ensure_restream_token.return_value = False

        args = argparse.Namespace(command="restream-status")
        result = cli.run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "restream-auth" in captured.err


class TestUpdateModeRouting:
    def test_update_mode_restream(self, cli_with_mock_core, capsys):
        cli, mock_core = cli_with_mock_core
        mock_client = MagicMock()
        mock_core.restream_client = mock_client
        mock_core.update_title_restream.return_value = None
        mock_core.current_title = "Updated Title"

        args = argparse.Namespace(
            command="update", mode="restream", wait=False, wait_timeout=90
        )
        result = cli.run(args)

        assert result == 0
        mock_core.update_title_restream.assert_called_once()

    def test_update_mode_youtube_default(self, cli_with_mock_core):
        cli, mock_core = cli_with_mock_core
        mock_core.check_live_status.return_value = {
            "is_live": True, "video_id": "v1", "title": "Old"
        }
        mock_core.is_live = True
        mock_core.current_title = "New"

        args = argparse.Namespace(
            command="update", mode="youtube", wait=False, wait_timeout=90
        )
        result = cli.run(args)

        assert result == 0
        mock_core.update_title.assert_called_once()

    def test_update_mode_restream_wait(self, cli_with_mock_core, capsys):
        cli, mock_core = cli_with_mock_core
        mock_client = MagicMock()
        mock_core.restream_client = mock_client

        call_count = [0]
        def mock_update():
            call_count[0] += 1
            if call_count[0] < 2:
                raise RestreamAPIError("Not ready")
            mock_core.current_title = "Waited Title"
        mock_core.update_title_restream.side_effect = mock_update

        args = argparse.Namespace(
            command="update", mode="restream", wait=True, wait_timeout=5
        )
        with patch("youtube_updater.cli._WAIT_POLL_INTERVAL", 0.01):
            result = cli.run(args)

        assert result == 0
        assert call_count[0] == 2

    def test_update_mode_restream_no_creds(self, cli_with_mock_core, capsys):
        cli, mock_core = cli_with_mock_core
        mock_core.config.ensure_restream_token.return_value = False

        args = argparse.Namespace(
            command="update", mode="restream", wait=False, wait_timeout=90
        )
        result = cli.run(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "restream-auth" in captured.err
