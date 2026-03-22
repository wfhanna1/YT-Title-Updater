"""Acceptance tests for Restream status (AC 2.1, 2.2)."""

import subprocess
import sys

import pytest


@pytest.mark.xfail(reason="Phase 3: not yet implemented", strict=True)
def test_ac_2_1_restream_status_lists_channels(temp_config_dir):
    """AC 2.1: restream-status lists connected channels.

    Given: Valid Restream credentials exist
    When: The user runs `yt-title-updater restream-status`
    Then: Connected channels are listed with platform names and active status
    And: Exit code is 0
    """
    from youtube_updater.core.restream_client import RestreamClient
    pytest.fail("RestreamClient not yet implemented")


@pytest.mark.xfail(reason="Phase 3: not yet implemented", strict=True)
def test_ac_2_2_missing_creds_error(temp_config_dir):
    """AC 2.2: Missing credentials -> error directing to restream-auth.

    Given: No Restream credentials exist
    When: The user runs `yt-title-updater restream-status`
    Then: Error message directs user to run `restream-auth`
    And: Exit code is 1
    """
    from youtube_updater.core.restream_client import RestreamClient
    pytest.fail("RestreamClient not yet implemented")
