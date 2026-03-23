"""Unit tests for RestreamClient."""

from unittest.mock import patch, MagicMock

import pytest

from youtube_updater.core.restream_client import RestreamClient
from youtube_updater.exceptions.custom_exceptions import RestreamAPIError


@pytest.fixture
def client():
    return RestreamClient(access_token="test_token")


class TestGetChannels:
    def test_get_channels_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {"displayName": "YT", "platform": "youtube", "active": True},
        ]
        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_resp):
            channels = client.get_channels()
        assert len(channels) == 1
        assert channels[0]["platform"] == "youtube"

    def test_get_channels_auth_error(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_resp):
            with pytest.raises(RestreamAPIError, match="401"):
                client.get_channels()


class TestGetStreamInfo:
    def test_get_stream_info_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"title": "Live Now", "status": "active"}
        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_resp):
            info = client.get_stream_info()
        assert info["title"] == "Live Now"

    def test_get_stream_info_not_streaming(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_resp):
            info = client.get_stream_info()
        assert info is None


class TestUpdateStreamTitle:
    def test_update_stream_title_uses_channel_meta_endpoint(self, client):
        """PATCHes /user/channel-meta/{id} (not /user/channel/{id})."""
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {"id": 1, "displayName": "YT", "enabled": True, "streamingPlatformId": 5},
        ]
        mock_patch_resp = MagicMock(status_code=200, text="{}")

        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_get_resp):
            with patch("youtube_updater.core.restream_client.requests.patch", return_value=mock_patch_resp) as mock_patch:
                client.update_stream_title("New Title")
        mock_patch.assert_called_once()
        url = mock_patch.call_args[0][0]
        assert "/user/channel-meta/1" in url

    def test_update_stream_title_sends_title_in_body(self, client):
        """Sends only the title field in the PATCH body."""
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {"id": 1, "displayName": "YT", "enabled": True},
        ]
        mock_patch_resp = MagicMock(status_code=200, text="{}")

        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_get_resp):
            with patch("youtube_updater.core.restream_client.requests.patch", return_value=mock_patch_resp) as mock_patch:
                client.update_stream_title("My Stream Title")
        assert mock_patch.call_args[1]["json"] == {"title": "My Stream Title"}

    def test_update_stream_title_multiple_enabled_channels(self, client):
        """PATCHes all enabled channels."""
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {"id": 1, "displayName": "YT", "enabled": True},
            {"id": 2, "displayName": "FB", "enabled": True},
        ]
        mock_patch_resp = MagicMock(status_code=200, text="{}")

        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_get_resp):
            with patch("youtube_updater.core.restream_client.requests.patch", return_value=mock_patch_resp) as mock_patch:
                client.update_stream_title("New Title")
        assert mock_patch.call_count == 2

    def test_update_stream_title_skips_disabled_channels(self, client):
        """Only PATCHes enabled channels, skips disabled ones."""
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {"id": 1, "displayName": "YT Main", "enabled": True},
            {"id": 2, "displayName": "YT Secondary", "enabled": False},
            {"id": 3, "displayName": "FB", "enabled": True},
        ]
        mock_patch_resp = MagicMock(status_code=200, text="{}")

        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_get_resp):
            with patch("youtube_updater.core.restream_client.requests.patch", return_value=mock_patch_resp) as mock_patch:
                client.update_stream_title("New Title")
        assert mock_patch.call_count == 2
        patched_urls = [call[0][0] for call in mock_patch.call_args_list]
        assert any("/channel-meta/1" in u for u in patched_urls)
        assert any("/channel-meta/3" in u for u in patched_urls)
        assert not any("/channel-meta/2" in u for u in patched_urls)

    def test_update_stream_title_all_disabled_raises(self, client):
        """Raises RestreamAPIError when all channels are disabled."""
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {"id": 1, "displayName": "YT", "enabled": False},
        ]

        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_get_resp):
            with pytest.raises(RestreamAPIError, match="No enabled channels"):
                client.update_stream_title("New Title")

    def test_update_stream_title_all_fail(self, client):
        """Raises RestreamAPIError when all channel updates fail."""
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {"id": 1, "displayName": "YT", "enabled": True},
        ]
        mock_patch_resp = MagicMock()
        mock_patch_resp.status_code = 500
        mock_patch_resp.text = "Internal Server Error"

        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_get_resp):
            with patch("youtube_updater.core.restream_client.requests.patch", return_value=mock_patch_resp):
                with pytest.raises(RestreamAPIError, match="Failed to update"):
                    client.update_stream_title("New Title")

    def test_update_stream_title_no_channels(self, client):
        """Raises RestreamAPIError when no channels exist."""
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = []

        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_get_resp):
            with pytest.raises(RestreamAPIError, match="No channels"):
                client.update_stream_title("New Title")

    def test_update_stream_title_partial_success(self, client):
        """Some channels succeed, some fail -- no error if at least one succeeds."""
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = [
            {"id": 1, "displayName": "YT", "enabled": True},
            {"id": 2, "displayName": "FB", "enabled": True},
        ]
        success_resp = MagicMock(status_code=200, text="{}")
        fail_resp = MagicMock(status_code=500, text="error")

        with patch("youtube_updater.core.restream_client.requests.get", return_value=mock_get_resp):
            with patch("youtube_updater.core.restream_client.requests.patch", side_effect=[success_resp, fail_resp]):
                # Should not raise because at least one succeeded
                client.update_stream_title("New Title")
