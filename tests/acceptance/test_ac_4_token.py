"""Acceptance tests for Restream token management (AC 4.1, 4.2)."""

import pytest


@pytest.mark.xfail(reason="Phase 2: not yet implemented", strict=True)
def test_ac_4_1_expired_token_silent_refresh(temp_config_dir):
    """AC 4.1: Expired access token -> silent refresh via refresh_token.

    Given: restream_token.json exists with expired access_token but valid refresh_token
    When: A Restream operation requires authentication
    Then: Refresh happens automatically without user interaction
    And: New access token saved to restream_token.json
    And: Operation proceeds normally
    """
    from youtube_updater.core.restream_auth import RestreamAuth
    pytest.fail("RestreamAuth not yet implemented")


@pytest.mark.xfail(reason="Phase 2: not yet implemented", strict=True)
def test_ac_4_2_invalid_refresh_token_error(temp_config_dir):
    """AC 4.2: Invalid refresh token -> error directing to re-run restream-auth.

    Given: restream_token.json exists with invalid/revoked refresh_token
    When: Token refresh is attempted
    Then: Clear error message directing user to re-run `restream-auth`
    And: AuthenticationError is raised
    """
    from youtube_updater.core.restream_auth import RestreamAuth
    pytest.fail("RestreamAuth not yet implemented")
