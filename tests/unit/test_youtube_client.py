"""Unit tests for YouTubeClient."""

import pytest
from unittest.mock import MagicMock, patch

from youtube_updater.core.youtube_client import YouTubeClient
from youtube_updater.exceptions.custom_exceptions import YouTubeAPIError


class TestYouTubeClient:
    """Test cases for YouTubeClient."""

    def setup_method(self):
        """Set up a YouTubeClient instance with a mocked youtube service."""
        self.mock_credentials = MagicMock()
        with patch("youtube_updater.core.youtube_client.build") as mock_build:
            self.mock_youtube = MagicMock()
            mock_build.return_value = self.mock_youtube
            self.client = YouTubeClient(self.mock_credentials)

    # --- get_channel_id ---

    def test_get_channel_id_success(self):
        """Test get_channel_id returns the channel ID from the API response."""
        self.mock_youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "UC123"}]
        }

        channel_id = self.client.get_channel_id()

        assert channel_id == "UC123"
        assert self.client.channel_id == "UC123"

    def test_get_channel_id_empty_response_raises_error(self):
        """Test get_channel_id raises YouTubeAPIError when items list is empty."""
        self.mock_youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": []
        }

        with pytest.raises(YouTubeAPIError):
            self.client.get_channel_id()

    def test_get_channel_id_api_exception_wraps_as_youtube_api_error(self):
        """Test get_channel_id wraps unexpected exceptions in YouTubeAPIError."""
        self.mock_youtube.channels.return_value.list.return_value.execute.side_effect = Exception(
            "Network error"
        )

        with pytest.raises(YouTubeAPIError, match="Error getting channel ID"):
            self.client.get_channel_id()

    # --- get_live_stream_info ---

    def test_get_live_stream_info_active_broadcast_matching_channel(self):
        """Test get_live_stream_info returns live info for a matching channel broadcast."""
        self.client.channel_id = "UC123"
        self.mock_youtube.liveBroadcasts.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "vid_abc",
                    "snippet": {
                        "channelId": "UC123",
                        "title": "Live Now",
                    },
                    "status": {"lifeCycleStatus": "live"},
                }
            ]
        }

        result = self.client.get_live_stream_info()

        assert result["is_live"] is True
        assert result["video_id"] == "vid_abc"
        assert result["title"] == "Live Now"

    def test_get_live_stream_info_no_active_broadcast(self):
        """Test get_live_stream_info returns is_live=False when no broadcasts."""
        self.client.channel_id = "UC123"
        self.mock_youtube.liveBroadcasts.return_value.list.return_value.execute.return_value = {
            "items": []
        }

        result = self.client.get_live_stream_info()

        assert result["is_live"] is False

    def test_get_live_stream_info_wrong_channel_filtered_out(self):
        """Test get_live_stream_info returns is_live=False for a different channel's broadcast."""
        self.client.channel_id = "UC123"
        self.mock_youtube.liveBroadcasts.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "vid_xyz",
                    "snippet": {
                        "channelId": "UC_OTHER",
                        "title": "Someone Else Live",
                    },
                }
            ]
        }

        result = self.client.get_live_stream_info()

        assert result["is_live"] is False

    def test_get_live_stream_info_fetches_channel_id_if_not_set(self):
        """Test get_live_stream_info calls get_channel_id when channel_id is None."""
        self.client.channel_id = None
        self.mock_youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "UC_FETCHED"}]
        }
        self.mock_youtube.liveBroadcasts.return_value.list.return_value.execute.return_value = {
            "items": []
        }

        result = self.client.get_live_stream_info()

        assert self.client.channel_id == "UC_FETCHED"
        assert result["is_live"] is False

    def test_get_live_stream_info_api_exception_wraps_as_youtube_api_error(self):
        """Test get_live_stream_info wraps unexpected exceptions in YouTubeAPIError."""
        self.client.channel_id = "UC123"
        self.mock_youtube.liveBroadcasts.return_value.list.return_value.execute.side_effect = (
            Exception("Timeout")
        )

        with pytest.raises(YouTubeAPIError, match="Error getting live stream info"):
            self.client.get_live_stream_info()

    # --- update_video_title ---

    def test_update_video_title_success(self):
        """Test update_video_title calls the YouTube API correctly."""
        self.mock_youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "title": "Old Title",
                        "categoryId": "22",
                        "description": "Test",
                    }
                }
            ]
        }
        self.mock_youtube.videos.return_value.update.return_value.execute.return_value = {}

        # Should not raise
        self.client.update_video_title("vid_123", "New Title")

        self.mock_youtube.videos.return_value.update.assert_called_once()
        update_call_kwargs = self.mock_youtube.videos.return_value.update.call_args
        assert update_call_kwargs[1]["body"]["snippet"]["title"] == "New Title"

    def test_update_video_title_no_video_raises_error(self):
        """Test update_video_title raises YouTubeAPIError when video is not found."""
        self.mock_youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": []
        }

        with pytest.raises(YouTubeAPIError):
            self.client.update_video_title("vid_nonexistent", "New Title")

    def test_update_video_title_api_exception_wraps_as_youtube_api_error(self):
        """Test update_video_title wraps unexpected exceptions in YouTubeAPIError."""
        self.mock_youtube.videos.return_value.list.return_value.execute.side_effect = (
            Exception("API quota exceeded")
        )

        with pytest.raises(YouTubeAPIError, match="Error updating video title"):
            self.client.update_video_title("vid_123", "New Title")
