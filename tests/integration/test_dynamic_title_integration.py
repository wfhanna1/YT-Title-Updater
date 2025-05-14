import os
import sys
import tempfile
from unittest import TestCase, mock
from datetime import datetime, timezone
import pytz
from pathlib import Path
from youtube_updater.core import YouTubeUpdaterCore

class TestDynamicTitleIntegration(TestCase):
    """Integration tests for dynamic title generation with title update workflow."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        # Create a client_secrets.json file for testing
        with open(os.path.join(self.temp_dir, "client_secrets.json"), "w") as f:
            f.write("{\"installed\":{\"client_id\":\"test\",\"project_id\":\"test\",\"auth_uri\":\"test\",\"token_uri\":\"test\",\"client_secret\":\"test\"}}")
        self.core = YouTubeUpdaterCore(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary files
        for file in Path(self.temp_dir).glob("*"):
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                for subfile in file.glob("*"):
                    subfile.unlink()
                file.rmdir()
        Path(self.temp_dir).rmdir()
    
    @mock.patch('youtube_updater.core.datetime')
    @mock.patch('youtube_updater.core.build')
    def test_empty_titles_file_triggers_dynamic_title(self, mock_build, mock_datetime):
        """Test that an empty titles file triggers dynamic title generation."""
        # Mock datetime to return Saturday at 8 PM EST
        est_timezone = pytz.timezone('US/Eastern')
        mock_date = datetime(2023, 7, 15, 20, 0, 0)  # July 15, 2023 was a Saturday
        mock_date_est = est_timezone.localize(mock_date)
        mock_date_utc = mock_date_est.astimezone(timezone.utc)
        mock_datetime.now.return_value = mock_date_utc
        
        # Setup YouTube API mocks
        mock_youtube = mock.MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock channel list response
        mock_youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "test_channel_id"}]
        }
        
        # Mock search response for live status
        mock_youtube.search.return_value.list.return_value.execute.return_value = {
            "items": [{
                "id": {"videoId": "test_video_id"},
                "snippet": {"title": "Current Live Title"}
            }]
        }
        
        # Mock video details response
        mock_youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [{
                "snippet": {
                    "title": "Current Live Title",
                    "description": "Test description",
                    "categoryId": "22"
                }
            }]
        }
        
        # Create an empty titles file
        with open(os.path.join(self.temp_dir, "titles.txt"), "w") as f:
            f.write("")
        
        # Initialize core with mocked YouTube API
        self.core.youtube = mock_youtube
        self.core.is_live = True
        self.core.channel_id = "test_channel_id"
        
        # Call update_title which should trigger dynamic title generation
        self.core.update_title()
        
        # Verify the dynamic title was generated
        expected_title = f"Saturday Night Stream - {mock_date.strftime('%Y-%m-%d')}"
        self.assertEqual(self.core.next_title, expected_title)
        
        # Verify the title was updated via the YouTube API
        mock_youtube.videos.return_value.update.assert_called_once()
        update_call = mock_youtube.videos.return_value.update.call_args
        self.assertEqual(update_call[1]['body']['snippet']['title'], expected_title)
    
    @mock.patch('youtube_updater.core.datetime')
    @mock.patch('youtube_updater.core.build')
    def test_no_titles_available_triggers_dynamic_title(self, mock_build, mock_datetime):
        """Test that 'No titles available' triggers dynamic title generation."""
        # Mock datetime to return a weekday at 3 PM EST
        est_timezone = pytz.timezone('US/Eastern')
        mock_date = datetime(2023, 7, 12, 15, 0, 0)  # July 12, 2023 was a Wednesday
        mock_date_est = est_timezone.localize(mock_date)
        mock_date_utc = mock_date_est.astimezone(timezone.utc)
        mock_datetime.now.return_value = mock_date_utc
        
        # Setup YouTube API mocks
        mock_youtube = mock.MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock channel list response
        mock_youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "test_channel_id"}]
        }
        
        # Mock search response for live status
        mock_youtube.search.return_value.list.return_value.execute.return_value = {
            "items": [{
                "id": {"videoId": "test_video_id"},
                "snippet": {"title": "Current Live Title"}
            }]
        }
        
        # Mock video details response
        mock_youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [{
                "snippet": {
                    "title": "Current Live Title",
                    "description": "Test description",
                    "categoryId": "22"
                }
            }]
        }
        
        # Set next_title to "No titles available"
        self.core.next_title = "No titles available"
        self.core.titles = []
        
        # Initialize core with mocked YouTube API
        self.core.youtube = mock_youtube
        self.core.is_live = True
        self.core.channel_id = "test_channel_id"
        
        # Call update_title which should trigger dynamic title generation
        self.core.update_title()
        
        # Verify the dynamic title was generated
        expected_title = f"Live Stream - {mock_date.strftime('%Y-%m-%d')}"
        self.assertEqual(self.core.next_title, expected_title)
        
        # Verify the title was updated via the YouTube API
        mock_youtube.videos.return_value.update.assert_called_once()
        update_call = mock_youtube.videos.return_value.update.call_args
        self.assertEqual(update_call[1]['body']['snippet']['title'], expected_title)