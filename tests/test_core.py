import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import tempfile
import shutil
import json
from google.oauth2.credentials import Credentials
from youtube_updater.core import YouTubeUpdaterCore

class TestYouTubeUpdaterCore(unittest.TestCase):
    """Test cases for YouTubeUpdaterCore class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create a mock client secrets file with valid format
        self.client_secrets_path = os.path.join(self.test_dir, "client_secrets.json")
        client_secrets_content = {
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "redirect_uris": ["http://localhost"]
            }
        }
        with open(self.client_secrets_path, "w") as f:
            json.dump(client_secrets_content, f)
        
        # Create a mock credentials object that can be pickled
        mock_creds = Credentials(
            token="test_token",
            refresh_token="test_refresh_token",
            token_uri="https://oauth2.googleapis.com/token",
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        # Mock the YouTube API setup
        with patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file') as mock_flow:
            mock_flow.return_value.run_local_server.return_value = mock_creds
            
            # Initialize the core with the test directory
            self.core = YouTubeUpdaterCore(config_dir=self.test_dir)
            
            # Create a mock YouTube service
            self.mock_youtube = MagicMock()
            self.core.youtube = self.mock_youtube

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test core initialization."""
        self.assertEqual(self.core.current_title, "Not Live")
        self.assertEqual(self.core.next_title, "Live Stream")
        self.assertEqual(self.core._status, "Titles loaded successfully")
        self.assertEqual(self.core._status_type, "success")

    def test_set_status(self):
        """Test status setting functionality."""
        self.core._set_status("Test message", "success")
        self.assertEqual(self.core._status, "Test message")
        self.assertEqual(self.core._status_type, "success")

    def test_load_titles(self):
        """Test loading titles from file."""
        # Create a titles file with test content
        with open(os.path.join(self.test_dir, "titles.txt"), "w") as f:
            f.write("Title 1\nTitle 2\n\n")
        
        self.core.load_titles()
        self.assertEqual(self.core.titles, ["Title 1", "Title 2"])
        self.assertEqual(self.core.next_title, "Title 1")

    def test_load_titles_empty_file(self):
        """Test loading titles when file doesn't exist."""
        # Remove the titles file if it exists
        titles_file = os.path.join(self.test_dir, "titles.txt")
        if os.path.exists(titles_file):
            os.remove(titles_file)
        
        self.core.load_titles()
        self.assertEqual(self.core.titles, ["Live Stream"])
        self.assertEqual(self.core.next_title, "Live Stream")

    def test_check_live_status_no_youtube(self):
        """Test check_live_status when YouTube service is not initialized."""
        self.core.youtube = None
        result = self.core.check_live_status()
        expected = ("Not Live", "Live Stream", 
                   "YouTube API not initialized. Please check client secrets file.", "error")
        self.assertEqual(result, expected)

    @patch.object(YouTubeUpdaterCore, 'load_titles')
    def test_check_live_status_with_titles(self, mock_load_titles):
        """Test check_live_status when titles are available."""
        # Setup mock response
        mock_response = {
            "items": [{
                "snippet": {
                    "title": "Current Title"
                }
            }]
        }
        self.mock_youtube.liveBroadcasts().list().execute.return_value = mock_response
        self.core.titles = ["New Title"]
        self.core.next_title = "New Title"

        result = self.core.check_live_status()
        self.assertEqual(result[0], "Current Title")
        self.assertEqual(result[1], "New Title")
        self.assertEqual(result[2], "Status updated successfully")
        self.assertEqual(result[3], "success")

    def test_check_live_status_no_broadcast(self):
        """Test check_live_status when no broadcast is active."""
        mock_response = {"items": []}
        self.mock_youtube.liveBroadcasts().list().execute.return_value = mock_response

        result = self.core.check_live_status()
        self.assertEqual(result[0], "Not Live")
        self.assertEqual(result[1], "No titles available")
        self.assertEqual(result[2], "Status updated successfully")
        self.assertEqual(result[3], "success")

    @patch('os.system')
    def test_open_config_dir(self, mock_system):
        """Test opening configuration directory."""
        self.core.open_config_dir()
        mock_system.assert_called_once()

    @patch('os.system')
    def test_open_titles_file(self, mock_system):
        """Test opening titles file."""
        self.core.open_titles_file()
        mock_system.assert_called_once()

if __name__ == '__main__':
    unittest.main() 