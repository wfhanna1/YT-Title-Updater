import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil
from youtube_updater.core import YouTubeUpdaterCore

class TestYouTubeUpdaterCore(unittest.TestCase):
    """Test cases for YouTubeUpdaterCore class."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create necessary files
        with open(os.path.join(self.test_dir, "titles.txt"), "w") as f:
            f.write("Test Title 1\nTest Title 2\n")
        
        # Create empty applied-titles.txt and history.log
        with open(os.path.join(self.test_dir, "applied-titles.txt"), "w") as f:
            f.write("")
        with open(os.path.join(self.test_dir, "history.log"), "w") as f:
            f.write("")
        
        # Initialize the core with the test directory
        self.core = YouTubeUpdaterCore(config_dir=self.test_dir)
        
        # Create a mock YouTube service
        self.mock_youtube = MagicMock()
        self.core.youtube = self.mock_youtube
        self.core.channel_id = "test_channel_id"

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test initialization of YouTubeUpdaterCore."""
        # Create a new instance without auto-setup
        core = YouTubeUpdaterCore(self.test_dir)
        core._initialize_state()  # Reset state manually
        
        self.assertEqual(core.config_dir, self.test_dir)
        self.assertTrue(os.path.exists(self.test_dir))
        self.assertEqual(core.status_type, "info")
        self.assertEqual(core.status, "Initializing")
        self.assertFalse(core.is_live)
        self.assertIsNone(core.channel_id)

    def test_set_status(self):
        """Test setting status message and type."""
        self.core._set_status("Test message", "success")
        self.assertEqual(self.core.status, "Test message")
        self.assertEqual(self.core.status_type, "success")
        
        with self.assertRaises(ValueError):
            self.core._set_status("Test message", "invalid_type")

    def test_load_titles(self):
        """Test loading titles from file."""
        with open(os.path.join(self.test_dir, "titles.txt"), "w") as f:
            f.write("Test Title 1\nTest Title 2\n")
        
        self.core.load_titles()
        self.assertEqual(self.core.titles, ["Test Title 1", "Test Title 2"])
        self.assertEqual(self.core.next_title, "Test Title 1")

    def test_load_titles_empty_file(self):
        """Test loading titles from empty file."""
        with open(os.path.join(self.test_dir, "titles.txt"), "w") as f:
            f.write("")
        
        self.core.load_titles()
        self.assertEqual(self.core.titles, [])

    def test_check_live_status_no_youtube(self):
        """Test check_live_status when YouTube service is not initialized."""
        self.core.youtube = None
        self.core.check_live_status()
        self.assertEqual(self.core.status, "YouTube client not initialized")
        self.assertEqual(self.core.status_type, "error")

    def test_check_live_status_with_titles(self):
        """Test check_live_status when titles are available."""
        # Mock the live stream response
        mock_response = {
            "items": [{
                "id": {"videoId": "test_video_id"},
                "snippet": {"title": "Test Title"}
            }]
        }
        self.mock_youtube.search().list().execute.return_value = mock_response
        
        self.core.check_live_status()
        self.assertTrue(self.core.is_live)
        self.assertEqual(self.core.status, "Channel is live")

    def test_check_live_status_no_broadcast(self):
        """Test check_live_status when no broadcast is active."""
        mock_response = {"items": []}
        self.mock_youtube.search().list().execute.return_value = mock_response
        
        self.core.check_live_status()
        self.assertFalse(self.core.is_live)
        self.assertEqual(self.core.status, "Channel is not live")
        self.assertEqual(self.core.status_type, "info")

    def test_archive_title(self):
        """Test archiving a title."""
        with open(os.path.join(self.test_dir, "titles.txt"), "w") as f:
            f.write("Test Title 1\nTest Title 2\n")
        
        self.core._archive_title("Test Title 1")
        
        # Check titles.txt
        with open(os.path.join(self.test_dir, "titles.txt"), "r") as f:
            remaining_titles = [line.strip() for line in f if line.strip()]
        self.assertEqual(remaining_titles, ["Test Title 2"])
        
        # Check applied-titles.txt
        with open(os.path.join(self.test_dir, "applied-titles.txt"), "r") as f:
            applied_titles = f.readlines()
        self.assertTrue(len(applied_titles) > 0)
        self.assertTrue("Test Title 1" in applied_titles[0])
        
        # Check history.log
        with open(os.path.join(self.test_dir, "history.log"), "r") as f:
            history = f.readlines()
        self.assertTrue(len(history) > 0)
        self.assertTrue("Title updated: Test Title 1" in history[0])

    def test_archive_title_error(self):
        """Test archiving a title with error."""
        self.core._archive_title("Nonexistent Title")
        self.assertIn("Error archiving title", self.core.status)
        self.assertEqual(self.core.status_type, "error")
        
        # Check history.log for error
        with open(os.path.join(self.test_dir, "history.log"), "r") as f:
            history = f.readlines()
        self.assertTrue(len(history) > 0)
        self.assertTrue("Error" in history[0])

    def test_update_title_no_change(self):
        """Test updating title when it's already current."""
        # Setup mock response with current title
        mock_response = {
            "items": [{
                "id": {"videoId": "test_video_id"},
                "snippet": {"title": "Test Title 1"}
            }]
        }
        self.mock_youtube.search().list().execute.return_value = mock_response
        self.core.current_title = "Test Title 1"
        self.core.next_title = "Test Title 1"
        self.core.titles = ["Test Title 1"]
        self.core.is_live = True
        
        self.core.update_title()
        self.assertEqual(self.core.status, "Title is already up to date")
        self.assertEqual(self.core.status_type, "info")

    def test_update_title_success(self):
        """Test successful title update."""
        # Setup mock response
        mock_response = {
            "items": [{
                "id": {"videoId": "test_video_id"},
                "snippet": {"title": "Current Title"}
            }]
        }
        self.mock_youtube.search().list().execute.return_value = mock_response
        self.mock_youtube.videos().update().execute.return_value = {}
        
        # Add the title to the list
        self.core.titles = ["New Title"]
        self.core.next_title = "New Title"
        self.core.is_live = True
        
        self.core.update_title()
        self.assertEqual(self.core.status, "Title updated to: New Title")
        self.assertEqual(self.core.status_type, "success")
        
        # Check history.log
        with open(os.path.join(self.test_dir, "history.log"), "r") as f:
            history = f.readlines()
        self.assertTrue(len(history) > 0)
        self.assertTrue("Title updated: New Title" in history[0])

    @patch('os.system')
    def test_open_titles_file_creation(self, mock_system):
        """Test that titles file is created if it doesn't exist."""
        # Remove the titles file
        os.remove(os.path.join(self.test_dir, "titles.txt"))
        
        self.core.open_titles_file()
        
        # Verify file was created with default content
        with open(os.path.join(self.test_dir, "titles.txt"), "r") as f:
            content = f.read().strip()
        self.assertEqual(content, "Live Stream")
        
        # Verify status was set correctly
        self.assertEqual(self.core.status, "Opened titles file")
        self.assertEqual(self.core.status_type, "success")

    @patch('os.system')
    def test_open_titles_file_error(self, mock_system):
        """Test error handling when opening titles file."""
        # Make the directory read-only to simulate permission error
        os.chmod(self.test_dir, 0o444)
        
        self.core.open_titles_file()
        
        # Verify error status was set
        self.assertEqual(self.core.status_type, "error")
        self.assertIn("Error opening titles file", self.core.status)
        
        # Restore directory permissions
        os.chmod(self.test_dir, 0o755)

if __name__ == '__main__':
    unittest.main() 