"""Acceptance tests for Restream authentication (AC 1.1, 1.2, 1.3)."""

import subprocess
import sys

import pytest


@pytest.mark.xfail(reason="Phase 2: not yet implemented", strict=True)
def test_ac_1_1_restream_auth_opens_browser_saves_token(temp_config_dir):
    """AC 1.1: restream-auth opens browser, saves restream_token.json with 0o600.

    Given: Restream client credentials are configured
    When: The user runs `yt-title-updater restream-auth`
    Then: Browser opens to Restream OAuth2 page
    And: After authorization, token is saved to restream_token.json
    And: File permissions are 0o600
    And: Exit code is 0
    """
    from youtube_updater.core.restream_auth import RestreamAuth
    pytest.fail("RestreamAuth not yet implemented")


@pytest.mark.xfail(reason="Phase 2: not yet implemented", strict=True)
def test_ac_1_2_silent_refresh_without_browser(temp_config_dir):
    """AC 1.2: If refresh token exists, refresh silently without browser.

    Given: A valid restream_token.json with refresh_token exists
    When: A Restream operation requires authentication
    Then: No browser is opened
    And: Token is refreshed silently via the refresh_token
    And: New token saved to restream_token.json
    """
    from youtube_updater.core.restream_auth import RestreamAuth
    pytest.fail("RestreamAuth not yet implemented")


@pytest.mark.xfail(reason="Phase 2/4: not yet implemented", strict=True)
def test_ac_1_3_auth_failure_error_email_exit_1(temp_config_dir):
    """AC 1.3: Auth failure -> clear error + email notification + exit 1.

    Given: Restream authentication fails (bad creds, network error, user denial)
    When: The auth flow completes
    Then: Clear error message printed to stderr
    And: Email notification sent (if email configured)
    And: Exit code is 1
    """
    from youtube_updater.core.restream_auth import RestreamAuth
    pytest.fail("RestreamAuth not yet implemented")
