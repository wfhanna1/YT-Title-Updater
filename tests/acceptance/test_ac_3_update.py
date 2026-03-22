"""Acceptance tests for Restream update (AC 3.1, 3.2, 3.3, 3.4, 3.5)."""

import subprocess
import sys

import pytest


@pytest.mark.xfail(reason="Phase 3: not yet implemented", strict=True)
def test_ac_3_1_update_mode_restream_patches_archives_exits_0(temp_config_dir, titles_file):
    """AC 3.1: update --mode restream -> PATCH title -> archive -> exit 0.

    Given: Valid Restream credentials and titles.txt with entries
    When: The user runs `yt-title-updater update --mode restream`
    Then: Next title is read from titles.txt
    And: PATCH request sent to Restream API
    And: Used title archived to applied-titles.txt
    And: Success message printed
    And: Exit code is 0
    """
    from youtube_updater.core.restream_client import RestreamClient
    pytest.fail("RestreamClient not yet implemented")


@pytest.mark.xfail(reason="Phase 3: not yet implemented", strict=True)
def test_ac_3_2_update_mode_youtube_preserves_existing(temp_config_dir):
    """AC 3.2: update --mode youtube preserves existing behavior.

    Given: Valid YouTube credentials
    When: The user runs `yt-title-updater update --mode youtube`
    Then: Behavior is identical to existing `update` command
    And: YouTube Data API v3 is used (not Restream)
    """
    from youtube_updater.core.restream_client import RestreamClient
    pytest.fail("--mode flag not yet implemented")


@pytest.mark.xfail(reason="Phase 3: not yet implemented", strict=True)
def test_ac_3_3_update_no_flag_defaults_youtube(temp_config_dir):
    """AC 3.3: update (no flag) defaults to youtube.

    Given: Both YouTube and Restream credentials exist
    When: The user runs `yt-title-updater update` (no --mode flag)
    Then: Default mode is youtube
    And: YouTube Data API v3 is used
    """
    from youtube_updater.core.restream_client import RestreamClient
    pytest.fail("--mode flag not yet implemented")


@pytest.mark.xfail(reason="Phase 3: not yet implemented", strict=True)
def test_ac_3_4_restream_wait_polls(temp_config_dir, titles_file):
    """AC 3.4: Restream mode + --wait polls until stream data available.

    Given: Valid Restream credentials and titles
    When: The user runs `yt-title-updater update --mode restream --wait`
    Then: CLI polls Restream API periodically
    And: When stream data becomes available, title is updated
    And: Respects --wait-timeout
    """
    from youtube_updater.core.restream_client import RestreamClient
    pytest.fail("Restream --wait not yet implemented")


@pytest.mark.xfail(reason="Phase 3/4: not yet implemented", strict=True)
def test_ac_3_5_missing_creds_error_email_exit_1(temp_config_dir):
    """AC 3.5: Missing/expired Restream creds -> error + email + exit 1.

    Given: No valid Restream credentials
    When: The user runs `yt-title-updater update --mode restream`
    Then: Clear error message directing to `restream-auth`
    And: Email notification sent (if configured)
    And: Exit code is 1
    """
    from youtube_updater.core.restream_client import RestreamClient
    pytest.fail("Restream creds handling not yet implemented")
