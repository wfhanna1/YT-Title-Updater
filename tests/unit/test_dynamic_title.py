import os
import sys
import tempfile
from unittest import TestCase, mock
from datetime import datetime, timezone
import pytz
from pathlib import Path
from youtube_updater.core import YouTubeUpdaterCore

class TestDynamicTitleGeneration(TestCase):
    """Test cases for dynamic title generation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
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
    def test_generate_dynamic_title_saturday_after_5pm(self, mock_datetime):
        """Test dynamic title generation on Saturday after 5 PM EST."""
        # Mock datetime to return Saturday at 6 PM EST
        est_timezone = pytz.timezone('US/Eastern')
        # Saturday (weekday=5) at 6 PM EST
        mock_date = datetime(2023, 7, 15, 18, 0, 0)  # July 15, 2023 was a Saturday
        mock_date_est = est_timezone.localize(mock_date)
        mock_date_utc = mock_date_est.astimezone(timezone.utc)
        
        # Configure the mock
        mock_datetime.now.return_value = mock_date_utc
        
        # Call the method
        title = self.core._generate_dynamic_title()
        
        # Verify the result
        expected_title = f"Saturday Night Stream - {mock_date.strftime('%Y-%m-%d')}"
        self.assertEqual(title, expected_title)
    
    @mock.patch('youtube_updater.core.datetime')
    def test_generate_dynamic_title_saturday_before_5pm(self, mock_datetime):
        """Test dynamic title generation on Saturday before 5 PM EST."""
        # Mock datetime to return Saturday at 2 PM EST
        est_timezone = pytz.timezone('US/Eastern')
        # Saturday (weekday=5) at 2 PM EST
        mock_date = datetime(2023, 7, 15, 14, 0, 0)  # July 15, 2023 was a Saturday
        mock_date_est = est_timezone.localize(mock_date)
        mock_date_utc = mock_date_est.astimezone(timezone.utc)
        
        # Configure the mock
        mock_datetime.now.return_value = mock_date_utc
        
        # Call the method
        title = self.core._generate_dynamic_title()
        
        # Verify the result
        expected_title = f"Live Stream - {mock_date.strftime('%Y-%m-%d')}"
        self.assertEqual(title, expected_title)
    
    @mock.patch('youtube_updater.core.datetime')
    def test_generate_dynamic_title_not_saturday(self, mock_datetime):
        """Test dynamic title generation on a day other than Saturday."""
        # Mock datetime to return Wednesday at 8 PM EST
        est_timezone = pytz.timezone('US/Eastern')
        # Wednesday (weekday=2) at 8 PM EST
        mock_date = datetime(2023, 7, 12, 20, 0, 0)  # July 12, 2023 was a Wednesday
        mock_date_est = est_timezone.localize(mock_date)
        mock_date_utc = mock_date_est.astimezone(timezone.utc)
        
        # Configure the mock
        mock_datetime.now.return_value = mock_date_utc
        
        # Call the method
        title = self.core._generate_dynamic_title()
        
        # Verify the result
        expected_title = f"Live Stream - {mock_date.strftime('%Y-%m-%d')}"
        self.assertEqual(title, expected_title)
    
    @mock.patch('youtube_updater.core.datetime')
    def test_generate_dynamic_title_integration_with_update_title(self, mock_datetime):
        """Test integration of dynamic title generation with update_title method."""
        # Mock datetime to return Saturday at 8 PM EST
        est_timezone = pytz.timezone('US/Eastern')
        mock_date = datetime(2023, 7, 15, 20, 0, 0)  # July 15, 2023 was a Saturday
        mock_date_est = est_timezone.localize(mock_date)
        mock_date_utc = mock_date_est.astimezone(timezone.utc)
        
        # Configure the mock
        mock_datetime.now.return_value = mock_date_utc
        
        # Setup empty titles file to trigger dynamic title generation
        with open(os.path.join(self.temp_dir, "titles.txt"), "w") as f:
            f.write("")
        
        # Mock YouTube API and live status
        with mock.patch.object(self.core, 'youtube') as mock_youtube, \
             mock.patch.object(self.core, 'is_live', True), \
             mock.patch.object(self.core, 'channel_id', 'test_channel_id'):
            
            # Mock search response
            mock_search = mock.MagicMock()
            mock_youtube.search.return_value.list.return_value.execute.return_value = {
                "items": [{"id": {"videoId": "test_video_id"}}]
            }
            
            # Mock video details response
            mock_video = mock.MagicMock()
            mock_youtube.videos.return_value.list.return_value.execute.return_value = {
                "items": [{
                    "snippet": {
                        "title": "Old Title",
                        "description": "Test description"
                    }
                }]
            }
            
            # Call update_title which should use dynamic title generation
            self.core.update_title()
            
            # Verify the dynamic title was generated and used
            expected_title = f"Saturday Night Stream - {mock_date.strftime('%Y-%m-%d')}"
            self.assertEqual(self.core.next_title, expected_title)