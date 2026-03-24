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
            {"displayName": "My YT", "streamingPlatformId": 5, "enabled": True},
            {"displayName": "My FB", "streamingPlatformId": 37, "enabled": False},
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

    def test_update_mode_restream_dry_run(self, cli_with_mock_core, capsys):
        """--dry-run authenticates and gets title but does not PATCH or archive."""
        cli, mock_core = cli_with_mock_core
        mock_client = MagicMock()
        mock_core.restream_client = mock_client
        mock_core.title_manager.peek_next_title.return_value = "Dry Run Title"

        args = argparse.Namespace(
            command="update", mode="restream", wait=False, wait_timeout=90,
            dry_run=True,
        )
        result = cli.run(args)

        assert result == 0
        # Should NOT have called update_title_restream
        mock_core.update_title_restream.assert_not_called()
        # Should print what it would do
        captured = capsys.readouterr()
        assert "Dry Run Title" in captured.out
        assert "dry run" in captured.out.lower()

    def test_update_mode_restream_dry_run_no_titles_uses_default(self, cli_with_mock_core, capsys):
        """--dry-run with empty titles.txt shows the default generated title."""
        cli, mock_core = cli_with_mock_core
        mock_client = MagicMock()
        mock_core.restream_client = mock_client
        mock_core.title_manager.peek_next_title.return_value = None
        mock_core.title_manager.get_next_title.return_value = "Sunday, March 22, 2026 - Divine Liturgy"

        args = argparse.Namespace(
            command="update", mode="restream", wait=False, wait_timeout=90,
            dry_run=True,
        )
        result = cli.run(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Divine Liturgy" in captured.out
        # Still should not have called the actual update
        mock_core.update_title_restream.assert_not_called()

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


class TestEnvVarSupport:
    def test_restream_client_uses_env_vars(self, cli_with_mock_core, monkeypatch):
        """RESTREAM_CLIENT_ID and RESTREAM_CLIENT_SECRET from env are used."""
        import json
        cli, mock_core = cli_with_mock_core

        monkeypatch.setenv("RESTREAM_CLIENT_ID", "env_cid")
        monkeypatch.setenv("RESTREAM_CLIENT_SECRET", "env_csec")

        # Write a token file with a valid non-expired token
        token_path = mock_core.config.get_restream_token_path()
        import time, os
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w") as f:
            json.dump({
                "access_token": "env_at",
                "refresh_token": "env_rt",
                "client_id": "env_cid",
                "expires_at": time.time() + 3600,
            }, f)

        mock_core.restream_client = None
        mock_core.update_title_restream.return_value = None
        mock_core.current_title = "Env Title"

        args = argparse.Namespace(
            command="update", mode="restream", wait=False, wait_timeout=90,
            dry_run=False,
        )
        result = cli.run(args)
        assert result == 0

    def test_missing_client_secret_with_expired_token_errors(self, cli_with_mock_core, capsys, monkeypatch):
        """Missing client_secret everywhere with expired token produces clear error."""
        import json, time, os
        cli, mock_core = cli_with_mock_core

        monkeypatch.delenv("RESTREAM_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("RESTREAM_CLIENT_ID", raising=False)

        # Write an EXPIRED token WITHOUT client_secret -- refresh impossible
        token_path = mock_core.config.get_restream_token_path()
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w") as f:
            json.dump({
                "access_token": "at",
                "refresh_token": "rt",
                "client_id": "cid",
                "expires_at": time.time() - 100,
            }, f)

        mock_core.restream_client = None

        args = argparse.Namespace(
            command="update", mode="restream", wait=False, wait_timeout=90,
            dry_run=False,
        )
        result = cli.run(args)
        assert result == 1
        captured = capsys.readouterr()
        assert "restream-auth" in captured.err

    def test_missing_client_secret_with_valid_token_succeeds(self, cli_with_mock_core, monkeypatch):
        """Valid (non-expired) token works without RESTREAM_CLIENT_SECRET."""
        import json, time, os
        cli, mock_core = cli_with_mock_core

        monkeypatch.delenv("RESTREAM_CLIENT_SECRET", raising=False)
        monkeypatch.delenv("RESTREAM_CLIENT_ID", raising=False)

        token_path = mock_core.config.get_restream_token_path()
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w") as f:
            json.dump({
                "access_token": "valid_at",
                "refresh_token": "rt",
                "client_id": "cid",
                "expires_at": time.time() + 3600,
            }, f)

        mock_core.restream_client = None
        mock_core.update_title_restream.return_value = None
        mock_core.current_title = "Title"

        args = argparse.Namespace(
            command="update", mode="restream", wait=False, wait_timeout=90,
            dry_run=False,
        )
        result = cli.run(args)
        assert result == 0

    def test_email_config_from_env_vars(self, cli_with_mock_core, monkeypatch):
        """ACS env vars used for email when config file absent."""
        cli, mock_core = cli_with_mock_core
        mock_core.config.get_email_config.return_value = None

        monkeypatch.setenv("ACS_CONNECTION_STRING", "endpoint=https://fake/;accesskey=k")
        monkeypatch.setenv("ACS_SENDER", "noreply@test.azurecomm.net")
        monkeypatch.setenv("ACS_RECIPIENTS", "a@b.com;c@d.com")

        config = cli._get_email_config()
        assert config is not None
        assert config["connection_string"] == "endpoint=https://fake/;accesskey=k"
        assert len(config["recipients"]) == 2
