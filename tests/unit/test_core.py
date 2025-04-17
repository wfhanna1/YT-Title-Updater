import os
import sys
import tempfile
from unittest import TestCase, mock
from pathlib import Path
from youtube_updater.core import YouTubeUpdaterCore

class TestYouTubeUpdaterCore(TestCase):
    """Test cases for YouTubeUpdaterCore class."""
    
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
    
    def test_initialization(self):
        """Test core initialization."""
        self.assertIsNotNone(self.core)
        self.assertEqual(self.core.current_title, "Not Live")
        self.assertEqual(self.core.next_title, "No titles available")
        self.assertFalse(self.core.is_live)
        self.assertIsNone(self.core.channel_id)
    
    def test_config_dir_setup(self):
        """Test configuration directory setup."""
        # Test with custom config dir
        custom_dir = os.path.join(self.temp_dir, "custom_config")
        core = YouTubeUpdaterCore(config_dir=custom_dir)
        self.assertEqual(core.config_dir, custom_dir)
        
        # Test default config dir
        core = YouTubeUpdaterCore()
        if sys.platform == "win32":
            expected = os.path.join(os.getenv("APPDATA"), "yt_title_updater")
        elif sys.platform == "darwin":
            expected = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "yt_title_updater")
        else:
            expected = os.path.join(os.path.expanduser("~"), ".config", "yt_title_updater")
        self.assertEqual(core.config_dir, expected)
    
    def test_file_paths_setup(self):
        """Test file paths setup."""
        expected_files = [
            "titles.txt",
            "applied-titles.txt",
            "token.pickle",
            "client_secrets.json",
            "history.log"
        ]
        
        for file in expected_files:
            file_path = os.path.join(self.temp_dir, file)
            self.assertTrue(os.path.exists(file_path))
    
    @mock.patch('youtube_updater.core.build')
    @mock.patch('youtube_updater.core.InstalledAppFlow')
    @mock.patch('youtube_updater.core.pickle')
    def test_youtube_setup(self, mock_pickle, mock_flow, mock_build):
        """Test YouTube API setup."""
        # Mock the credentials
        mock_creds = mock.MagicMock()
        mock_creds.valid = True
        mock_pickle.load.return_value = mock_creds
        
        # Mock the YouTube API response
        mock_build.return_value.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "test_channel_id"}]
        }
        
        # Mock the search response
        mock_build.return_value.search.return_value.list.return_value.execute.return_value = {
            "items": [{
                "snippet": {
                    "title": "Test Live Stream",
                    "categoryId": "22"
                }
            }]
        }
        
        # Create a mock client secrets file and token file
        with open(os.path.join(self.temp_dir, "client_secrets.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(self.temp_dir, "token.pickle"), "wb") as f:
            f.write(b"")
        
        core = YouTubeUpdaterCore(config_dir=self.temp_dir)
        core.setup_youtube()
        
        self.assertTrue(core.is_live)
        self.assertEqual(core.current_title, "Test Live Stream")
        self.assertEqual(core.channel_id, "test_channel_id")
    
    def test_title_management(self):
        """Test title management functions."""
        # Test loading titles
        with open(os.path.join(self.temp_dir, "titles.txt"), "w") as f:
            f.write("Title 1\nTitle 2\nTitle 3\n")
        
        core = YouTubeUpdaterCore(config_dir=self.temp_dir)
        core.load_titles()
        
        self.assertEqual(len(core.titles), 3)
        self.assertEqual(core.next_title, "Title 1")
        
        # Test title rotation
        core._rotate_titles()
        self.assertEqual(core.next_title, "Title 2")
        
        # Test title archiving
        core._archive_title("Title 2")
        self.assertEqual(len(core.titles), 2)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "applied-titles.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "history.log")))
    
    def test_status_management(self):
        """Test status management."""
        # Test valid status types
        for status_type in self.core.STATUS_TYPES:
            self.core._set_status("Test message", status_type)
            self.assertEqual(self.core.status, "Test message")
            self.assertEqual(self.core.status_type, status_type)
        
        # Test invalid status type
        with self.assertRaises(ValueError):
            self.core._set_status("Test message", "invalid")
    
    @mock.patch('youtube_updater.core.os')
    def test_file_operations(self, mock_os):
        """Test file operations."""
        # Test opening config directory
        self.core.open_config_dir()
        if sys.platform == "win32":
            mock_os.startfile.assert_called_once_with(self.temp_dir)
        else:
            mock_os.system.assert_called_once()
        
        # Test opening titles file
        self.core.open_titles_file()
        if sys.platform == "win32":
            mock_os.startfile.assert_called_with(os.path.join(self.temp_dir, "titles.txt"))
        else:
            mock_os.system.assert_called() 