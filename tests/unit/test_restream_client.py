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
    def test_update_stream_title_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("youtube_updater.core.restream_client.requests.patch", return_value=mock_resp):
            client.update_stream_title("New Title")
        # No exception = success

    def test_update_stream_title_failure(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        with patch("youtube_updater.core.restream_client.requests.patch", return_value=mock_resp):
            with pytest.raises(RestreamAPIError, match="500"):
                client.update_stream_title("New Title")
