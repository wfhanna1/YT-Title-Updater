"""Acceptance tests for non-functional requirements (NF1, NF2, NF3, NF4)."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.mark.xfail(reason="Phase 3: not yet implemented", strict=True)
def test_nf1_existing_youtube_behavior_unchanged():
    """NF1: No changes to existing YouTube-only behavior.

    All pre-existing unit and integration tests continue to pass,
    confirming no regression in YouTube-only functionality.
    """
    from youtube_updater.core.restream_client import RestreamClient
    pytest.fail("Restream integration not yet implemented -- NF1 verification deferred")


@pytest.mark.xfail(reason="Phase 2: not yet implemented", strict=True)
def test_nf2_restream_creds_0o600(temp_config_dir):
    """NF2: Restream credentials stored with 0o600 permissions.

    Given: A restream_token.json file is written by RestreamAuth
    Then: File permissions are 0o600 (owner read/write only)
    """
    from youtube_updater.core.restream_auth import RestreamAuth
    pytest.fail("RestreamAuth not yet implemented")


def test_nf3_requests_in_requirements(project_root):
    """NF3: requests library added to requirements.txt.

    Given: requirements.txt exists in the project root
    Then: It contains a line matching 'requests'
    """
    req_path = project_root / "requirements.txt"
    content = req_path.read_text()
    assert "requests" in content, "requests not found in requirements.txt"


def test_nf4_youtube_auth_files_never_modified(temp_config_dir):
    """NF4: Never modify token.json, credentials.json, pickle.json.

    Given: YouTube auth files exist in the config directory
    When: Restream and email config operations are performed
    Then: YouTube auth file mtimes are unchanged
    """
    from youtube_updater.core.config_manager import ConfigManager

    # Create sentinel YouTube auth files
    yt_auth_files = ["token.json", "credentials.json", "token.pickle"]
    for name in yt_auth_files:
        path = temp_config_dir / name
        path.write_text("sentinel")

    # Record mtimes
    before = {}
    for name in yt_auth_files:
        path = temp_config_dir / name
        before[name] = path.stat().st_mtime

    # Small delay to ensure mtime would differ if written
    time.sleep(0.05)

    # Perform config operations that touch Restream/email paths
    cm = ConfigManager(str(temp_config_dir))
    _ = cm.get_restream_token_path()
    cm.save_email_config({
        "connection_string": "test",
        "sender": "a@b.com",
        "recipient": "c@d.com",
    })
    _ = cm.get_email_config()

    # Verify YouTube auth files unchanged
    for name in yt_auth_files:
        path = temp_config_dir / name
        assert path.stat().st_mtime == before[name], (
            f"YouTube auth file {name} was modified by config operations"
        )
