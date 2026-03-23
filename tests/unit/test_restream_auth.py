"""Unit tests for RestreamAuth."""

import json
import os
import stat
import time
from unittest.mock import patch, MagicMock

import pytest

from youtube_updater.core.restream_auth import RestreamAuth
from youtube_updater.exceptions.custom_exceptions import AuthenticationError


@pytest.fixture
def token_path(tmp_path):
    return str(tmp_path / "restream_token.json")


@pytest.fixture
def auth(token_path):
    return RestreamAuth(
        client_id="test_cid",
        client_secret="test_csec",
        token_path=token_path,
    )


class TestAuthenticate:
    def test_authenticate_opens_browser(self, auth):
        """authenticate() should trigger the OAuth browser flow."""
        fake_token = {"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
        with patch.object(auth, "_run_oauth_flow", return_value=fake_token) as mock_flow:
            auth.authenticate()
        mock_flow.assert_called_once()

    def test_authenticate_saves_token_0600(self, auth, token_path):
        """authenticate() saves the token file with 0o600 permissions."""
        fake_token = {"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
        with patch.object(auth, "_run_oauth_flow", return_value=fake_token):
            auth.authenticate()
        mode = stat.S_IMODE(os.stat(token_path).st_mode)
        assert mode == 0o600


class TestLoadToken:
    def test_load_token_returns_dict(self, auth, token_path):
        """load_token() returns dict when valid file exists."""
        data = {"access_token": "at", "refresh_token": "rt", "expires_at": time.time() + 3600}
        with open(token_path, "w") as f:
            json.dump(data, f)
        result = auth.load_token()
        assert result["access_token"] == "at"

    def test_load_token_returns_none(self, auth):
        """load_token() returns None when file doesn't exist."""
        result = auth.load_token()
        assert result is None


class TestRefreshToken:
    def test_refresh_token_success(self, auth, token_path):
        """refresh_token() exchanges refresh token for new access token."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "new_at",
            "refresh_token": "new_rt",
            "expires_in": 3600,
        }
        with patch("youtube_updater.core.restream_auth.requests.post", return_value=mock_resp):
            auth.refresh_token("old_rt")
        # Token file should be updated
        with open(token_path) as f:
            saved = json.load(f)
        assert saved["access_token"] == "new_at"

    def test_refresh_token_failure_401(self, auth):
        """refresh_token() raises AuthenticationError on 401."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "invalid_grant"
        with patch("youtube_updater.core.restream_auth.requests.post", return_value=mock_resp):
            with pytest.raises(AuthenticationError, match="restream-auth"):
                auth.refresh_token("bad_rt")


class TestGetValidToken:
    def test_get_valid_token_not_expired(self, auth, token_path):
        """get_valid_token() returns cached token when not expired."""
        data = {
            "access_token": "valid_at",
            "refresh_token": "rt",
            "client_id": "test_cid",
            "expires_at": time.time() + 3600,
        }
        with open(token_path, "w") as f:
            json.dump(data, f)
        token = auth.get_valid_token()
        assert token == "valid_at"

    def test_get_valid_token_expired_refreshes(self, auth, token_path):
        """get_valid_token() refreshes when token is expired."""
        data = {
            "access_token": "expired_at",
            "refresh_token": "valid_rt",
            "client_id": "test_cid",
            "expires_at": time.time() - 100,
        }
        with open(token_path, "w") as f:
            json.dump(data, f)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "refreshed_at",
            "refresh_token": "new_rt",
            "expires_in": 3600,
        }
        with patch("youtube_updater.core.restream_auth.requests.post", return_value=mock_resp):
            token = auth.get_valid_token()
        assert token == "refreshed_at"

    def test_get_valid_token_no_file(self, auth):
        """get_valid_token() raises AuthenticationError when no token file."""
        with pytest.raises(AuthenticationError, match="restream-auth"):
            auth.get_valid_token()


class TestErrorHandling:
    def test_load_token_corrupt_json(self, auth, token_path):
        """load_token() raises AuthenticationError on corrupt JSON."""
        with open(token_path, "w") as f:
            f.write("{corrupt")
        with pytest.raises(AuthenticationError, match="corrupt"):
            auth.load_token()

    def test_build_token_data_missing_access_token(self, auth):
        """_build_token_data raises AuthenticationError if access_token missing."""
        with pytest.raises(AuthenticationError, match="access_token"):
            auth._build_token_data({"refresh_token": "rt", "expires_in": 3600})

    def test_saved_token_does_not_contain_client_secret(self, auth, token_path):
        """Token file must not contain client_secret."""
        fake_token = {"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
        with patch.object(auth, "_run_oauth_flow", return_value=fake_token):
            auth.authenticate()
        with open(token_path) as f:
            saved = json.load(f)
        assert "client_secret" not in saved
