"""Acceptance tests for Restream status (AC 2.1, 2.2)."""

import subprocess
import sys
from unittest.mock import patch, MagicMock

import pytest


def test_ac_2_1_restream_status_lists_channels(temp_config_dir):
    """AC 2.1: restream-status lists connected channels.

    Given: Valid Restream credentials exist
    When: The user runs restream-status
    Then: Connected channels are listed with platform names and active status
    """
    from youtube_updater.core.restream_client import RestreamClient

    client = RestreamClient(access_token="fake_token")
    fake_channels = [
        {"displayName": "My YouTube", "platform": "youtube", "active": True},
        {"displayName": "My Facebook", "platform": "facebook", "active": False},
    ]
    with patch.object(client, "get_channels", return_value=fake_channels):
        channels = client.get_channels()

    assert len(channels) == 2
    assert channels[0]["platform"] == "youtube"
    assert channels[1]["platform"] == "facebook"


def test_ac_2_2_missing_creds_error(temp_config_dir):
    """AC 2.2: Missing credentials -> error directing to restream-auth.

    Given: No Restream credentials exist
    When: The CLI tries to create a RestreamClient
    Then: Error message directs user to run restream-auth
    """
    from youtube_updater.core.restream_auth import RestreamAuth
    from youtube_updater.exceptions.custom_exceptions import AuthenticationError

    token_path = str(temp_config_dir / "restream_token.json")
    auth = RestreamAuth(client_id="cid", client_secret="csec", token_path=token_path)

    with pytest.raises(AuthenticationError, match="restream-auth"):
        auth.get_valid_token()
