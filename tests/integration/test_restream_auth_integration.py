"""Integration tests for RestreamAuth -- full auth lifecycle with real file I/O."""

import json
import os
import stat
import time
from unittest.mock import patch, MagicMock

from youtube_updater.core.restream_auth import RestreamAuth


class TestRestreamAuthIntegration:
    """Full lifecycle: authenticate -> save -> load -> refresh -> verify file state."""

    def test_full_auth_lifecycle(self, tmp_path):
        """authenticate -> load -> verify -> expire -> refresh -> verify."""
        token_path = str(tmp_path / "restream_token.json")
        auth = RestreamAuth(
            client_id="int_cid",
            client_secret="int_csec",
            token_path=token_path,
        )

        # Step 1: Authenticate (mocked OAuth flow)
        fake_token = {
            "access_token": "initial_at",
            "refresh_token": "initial_rt",
            "expires_in": 3600,
        }
        with patch.object(auth, "_run_oauth_flow", return_value=fake_token):
            auth.authenticate()

        # Step 2: Load and verify
        loaded = auth.load_token()
        assert loaded["access_token"] == "initial_at"
        assert loaded["refresh_token"] == "initial_rt"
        assert loaded["client_id"] == "int_cid"
        assert loaded["client_secret"] == "int_csec"
        assert loaded["expires_at"] > time.time()

        # Step 3: get_valid_token returns cached (not expired)
        token = auth.get_valid_token()
        assert token == "initial_at"

        # Step 4: Simulate expiration
        loaded["expires_at"] = time.time() - 100
        with open(token_path, "w") as f:
            json.dump(loaded, f)

        # Step 5: Refresh (mocked HTTP)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "refreshed_at",
            "refresh_token": "refreshed_rt",
            "expires_in": 7200,
        }
        with patch("youtube_updater.core.restream_auth.requests.post", return_value=mock_resp):
            token = auth.get_valid_token()
        assert token == "refreshed_at"

        # Step 6: Verify refreshed token was persisted
        final = auth.load_token()
        assert final["access_token"] == "refreshed_at"
        assert final["refresh_token"] == "refreshed_rt"

    def test_permissions_preserved_across_operations(self, tmp_path):
        """Token file maintains 0o600 through authenticate and refresh."""
        token_path = str(tmp_path / "restream_token.json")
        auth = RestreamAuth(
            client_id="cid",
            client_secret="csec",
            token_path=token_path,
        )

        # Authenticate
        fake_token = {"access_token": "at", "refresh_token": "rt", "expires_in": 1}
        with patch.object(auth, "_run_oauth_flow", return_value=fake_token):
            auth.authenticate()
        assert stat.S_IMODE(os.stat(token_path).st_mode) == 0o600

        # Expire the token
        data = auth.load_token()
        data["expires_at"] = time.time() - 100
        with open(token_path, "w") as f:
            json.dump(data, f)

        # Refresh
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "new", "refresh_token": "new_rt", "expires_in": 3600}
        with patch("youtube_updater.core.restream_auth.requests.post", return_value=mock_resp):
            auth.get_valid_token()
        assert stat.S_IMODE(os.stat(token_path).st_mode) == 0o600
