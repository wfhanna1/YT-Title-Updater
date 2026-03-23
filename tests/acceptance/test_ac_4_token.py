"""Acceptance tests for Restream token management (AC 4.1, 4.2)."""

import json
import time
from unittest.mock import patch, MagicMock

import pytest


def test_ac_4_1_expired_token_silent_refresh(temp_config_dir):
    """AC 4.1: Expired access token -> silent refresh via refresh_token.

    Given: restream_token.json exists with expired access_token but valid refresh_token
    When: get_valid_token() is called
    Then: Refresh happens automatically without user interaction
    And: New access token saved to restream_token.json
    And: Operation proceeds normally
    """
    from youtube_updater.core.restream_auth import RestreamAuth

    token_path = str(temp_config_dir / "restream_token.json")

    # Write expired token
    expired_token = {
        "access_token": "old_expired",
        "refresh_token": "valid_refresh",
        "client_id": "cid",
        "expires_at": time.time() - 300,
    }
    with open(token_path, "w") as f:
        json.dump(expired_token, f)

    auth = RestreamAuth(client_id="cid", client_secret="csec", token_path=token_path)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "fresh_token",
        "refresh_token": "fresh_refresh",
        "expires_in": 3600,
    }

    with patch("youtube_updater.core.restream_auth.requests.post", return_value=mock_response):
        token = auth.get_valid_token()

    assert token == "fresh_token"

    # Verify new token was persisted
    with open(token_path) as f:
        saved = json.load(f)
    assert saved["access_token"] == "fresh_token"


def test_ac_4_2_invalid_refresh_token_error(temp_config_dir):
    """AC 4.2: Invalid refresh token -> error directing to re-run restream-auth.

    Given: restream_token.json exists with invalid/revoked refresh_token
    When: Token refresh is attempted
    Then: AuthenticationError is raised with message about re-running restream-auth
    """
    from youtube_updater.core.restream_auth import RestreamAuth
    from youtube_updater.exceptions.custom_exceptions import AuthenticationError

    token_path = str(temp_config_dir / "restream_token.json")

    expired_token = {
        "access_token": "old",
        "refresh_token": "revoked_rt",
        "client_id": "cid",
        "expires_at": time.time() - 300,
    }
    with open(token_path, "w") as f:
        json.dump(expired_token, f)

    auth = RestreamAuth(client_id="cid", client_secret="csec", token_path=token_path)

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "invalid_grant"

    with patch("youtube_updater.core.restream_auth.requests.post", return_value=mock_response):
        with pytest.raises(AuthenticationError, match="restream-auth"):
            auth.get_valid_token()
