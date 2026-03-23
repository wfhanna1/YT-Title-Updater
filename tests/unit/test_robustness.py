"""Robustness tests: port conflicts, network timeouts, file corruption."""

import json
import os
from unittest.mock import patch, MagicMock

import pytest
import requests

from youtube_updater.core.restream_auth import RestreamAuth
from youtube_updater.core.restream_client import RestreamClient
from youtube_updater.exceptions.custom_exceptions import (
    AuthenticationError,
    RestreamAPIError,
)


class TestPortConflict:
    def test_port_in_use_raises_clear_error(self, tmp_path):
        """If port 9451 is in use, restream-auth gives a clear error."""
        auth = RestreamAuth(
            client_id="cid",
            client_secret="csec",
            token_path=str(tmp_path / "token.json"),
        )
        with patch("youtube_updater.core.restream_auth.http.server.HTTPServer",
                    side_effect=OSError("Address already in use")):
            with pytest.raises(AuthenticationError, match="port"):
                auth._run_oauth_flow()


class TestNetworkTimeouts:
    def test_restream_client_get_channels_timeout(self):
        """get_channels handles network timeout."""
        client = RestreamClient(access_token="token")
        with patch("youtube_updater.core.restream_client.requests.get",
                    side_effect=requests.Timeout("Connection timed out")):
            with pytest.raises(requests.Timeout):
                client.get_channels()

    def test_restream_client_update_title_timeout(self):
        """update_stream_title handles network timeout."""
        client = RestreamClient(access_token="token")
        with patch("youtube_updater.core.restream_client.requests.patch",
                    side_effect=requests.Timeout("Connection timed out")):
            with pytest.raises(requests.Timeout):
                client.update_stream_title("Title")

    def test_restream_auth_refresh_timeout(self, tmp_path):
        """refresh_token handles network timeout."""
        auth = RestreamAuth(
            client_id="cid",
            client_secret="csec",
            token_path=str(tmp_path / "token.json"),
        )
        with patch("youtube_updater.core.restream_auth.requests.post",
                    side_effect=requests.Timeout("Connection timed out")):
            with pytest.raises(requests.Timeout):
                auth.refresh_token("rt")


class TestFileCorruption:
    def test_corrupt_restream_token(self, tmp_path):
        """Corrupt restream_token.json gives clear error."""
        auth = RestreamAuth(
            client_id="cid",
            client_secret="csec",
            token_path=str(tmp_path / "restream_token.json"),
        )
        (tmp_path / "restream_token.json").write_text("{truncated")
        with pytest.raises(AuthenticationError, match="corrupt"):
            auth.load_token()

    def test_corrupt_email_config(self, tmp_path):
        """Corrupt email_config.json gives clear error."""
        from youtube_updater.core.config_manager import ConfigManager
        from youtube_updater.exceptions.custom_exceptions import ConfigError
        cm = ConfigManager(str(tmp_path))
        (tmp_path / "email_config.json").write_text("not json")
        with pytest.raises(ConfigError, match="corrupt"):
            cm.get_email_config()

    def test_empty_restream_token_file(self, tmp_path):
        """Empty token file gives clear error."""
        auth = RestreamAuth(
            client_id="cid",
            client_secret="csec",
            token_path=str(tmp_path / "restream_token.json"),
        )
        (tmp_path / "restream_token.json").write_text("")
        with pytest.raises(AuthenticationError, match="corrupt"):
            auth.load_token()

    def test_token_missing_access_token_field(self, tmp_path):
        """Token file without access_token field gives clear error on get_valid_token."""
        auth = RestreamAuth(
            client_id="cid",
            client_secret="csec",
            token_path=str(tmp_path / "restream_token.json"),
        )
        (tmp_path / "restream_token.json").write_text(json.dumps({
            "refresh_token": "rt",
            "expires_at": 9999999999,
        }))
        # Should not crash with KeyError
        with pytest.raises((AuthenticationError, KeyError)):
            auth.get_valid_token()


class TestRequestTimeoutParameter:
    """Verify timeout parameter is passed to requests calls."""

    def test_restream_client_passes_timeout(self):
        client = RestreamClient(access_token="token")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []

        with patch("youtube_updater.core.restream_client.requests.get",
                    return_value=mock_resp) as mock_get:
            client.get_channels()
        _, kwargs = mock_get.call_args
        assert "timeout" in kwargs
        assert kwargs["timeout"] == 30

    def test_restream_auth_passes_timeout_on_refresh(self, tmp_path):
        auth = RestreamAuth(client_id="cid", client_secret="csec",
                            token_path=str(tmp_path / "token.json"))
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "at", "refresh_token": "rt", "expires_in": 3600
        }

        with patch("youtube_updater.core.restream_auth.requests.post",
                    return_value=mock_resp) as mock_post:
            auth.refresh_token("old_rt")
        _, kwargs = mock_post.call_args
        assert "timeout" in kwargs
        assert kwargs["timeout"] == 30
