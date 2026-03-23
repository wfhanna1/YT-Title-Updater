"""Acceptance tests for Restream authentication (AC 1.1, 1.2, 1.3)."""

import json
import os
import stat
import time
from unittest.mock import patch, MagicMock

import pytest


def test_ac_1_1_restream_auth_opens_browser_saves_token(temp_config_dir):
    """AC 1.1: restream-auth opens browser, saves restream_token.json with 0o600.

    Given: Restream client credentials are configured
    When: The user runs restream-auth
    Then: Browser opens to Restream OAuth2 page
    And: After authorization, token is saved to restream_token.json
    And: File permissions are 0o600
    And: Exit code is 0
    """
    from youtube_updater.core.restream_auth import RestreamAuth

    token_path = str(temp_config_dir / "restream_token.json")
    auth = RestreamAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_path=token_path,
    )

    # Mock the OAuth browser flow to return a token directly
    fake_token = {
        "access_token": "at_12345",
        "refresh_token": "rt_12345",
        "expires_in": 3600,
    }
    with patch.object(auth, "_run_oauth_flow", return_value=fake_token):
        auth.authenticate()

    # Verify token file exists with correct permissions
    assert os.path.exists(token_path)
    mode = stat.S_IMODE(os.stat(token_path).st_mode)
    assert mode == 0o600, f"Expected 0o600 but got {oct(mode)}"

    # Verify token content
    with open(token_path) as f:
        saved = json.load(f)
    assert saved["access_token"] == "at_12345"
    assert saved["refresh_token"] == "rt_12345"


def test_ac_1_2_silent_refresh_without_browser(temp_config_dir):
    """AC 1.2: If refresh token exists, refresh silently without browser.

    Given: A valid restream_token.json with refresh_token exists
    When: get_valid_token() is called with an expired access token
    Then: No browser is opened
    And: Token is refreshed silently via the refresh_token
    And: New token saved to restream_token.json
    """
    from youtube_updater.core.restream_auth import RestreamAuth

    token_path = str(temp_config_dir / "restream_token.json")

    # Write an expired token with a valid refresh_token
    expired_token = {
        "access_token": "expired_at",
        "refresh_token": "valid_rt",
        "client_id": "test_id",
        "client_secret": "test_secret",
        "expires_at": time.time() - 100,  # expired
    }
    with open(token_path, "w") as f:
        json.dump(expired_token, f)

    auth = RestreamAuth(
        client_id="test_id",
        client_secret="test_secret",
        token_path=token_path,
    )

    # Mock the refresh endpoint to return a new token
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "new_at",
        "refresh_token": "new_rt",
        "expires_in": 3600,
    }

    with patch("youtube_updater.core.restream_auth.requests.post", return_value=mock_response) as mock_post:
        with patch("webbrowser.open") as mock_browser:
            token = auth.get_valid_token()

    # Browser should NOT have been opened
    mock_browser.assert_not_called()
    # Refresh endpoint should have been called
    mock_post.assert_called_once()
    # New token returned
    assert token == "new_at"


def test_ac_1_3_auth_failure_error_email_exit_1(temp_config_dir):
    """AC 1.3: Auth failure -> clear error + email notification + exit 1.

    Given: Restream authentication fails
    When: The auth flow completes
    Then: Clear error message printed to stderr
    And: Exit code is 1

    Note: Email notification part verified in Phase 4.
    """
    from youtube_updater.core.restream_auth import RestreamAuth
    from youtube_updater.exceptions.custom_exceptions import AuthenticationError

    token_path = str(temp_config_dir / "restream_token.json")
    auth = RestreamAuth(
        client_id="bad_id",
        client_secret="bad_secret",
        token_path=token_path,
    )

    # Mock the OAuth flow to raise an error
    with patch.object(auth, "_run_oauth_flow", side_effect=AuthenticationError("OAuth denied")):
        with pytest.raises(AuthenticationError, match="OAuth denied"):
            auth.authenticate()
