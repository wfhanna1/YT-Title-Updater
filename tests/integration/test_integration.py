import os
import sys
import tempfile
from unittest import TestCase, mock
from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from youtube_updater.core import YouTubeUpdaterCore
from youtube_updater.gui import YouTubeUpdaterGUI

class TestIntegration(TestCase):
    """Integration tests for YouTube Title Updater."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create QApplication instance
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock client secrets file
        with open(os.path.join(self.temp_dir, "client_secrets.json"), "w") as f:
            f.write("{}")
        
        # Create core instance
        self.core = YouTubeUpdaterCore(config_dir=self.temp_dir)
        self.core._test_mode = True  # Enable test mode
        
        # Create GUI instance
        self.gui = YouTubeUpdaterGUI(core=self.core)
        self.gui.show()
        QTest.qWaitForWindowExposed(self.gui)
        
        # Ensure initial state
        self.core._set_status("Initialized", "info")
        self.gui.update_display()
        QTest.qWait(100)  # Wait for GUI to update
        
        # Clear any existing status
        self.core._set_status("", "info")
        self.gui.update_display()
        QTest.qWait(100)  # Wait for GUI to update
    
    def tearDown(self):
        """Clean up test environment."""
        self.gui.close()
        # Clean up temporary files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    @mock.patch('youtube_updater.core.build')
    @mock.patch('youtube_updater.core.InstalledAppFlow')
    def test_youtube_integration(self, mock_flow, mock_build):
        """Test YouTube API integration."""
        # Mock the YouTube API response
        mock_build.return_value.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "test_channel_id"}]
        }
        
        # Mock the search response
        mock_build.return_value.search.return_value.list.return_value.execute.return_value = {
            "items": [{
                "id": {"videoId": "test_video_id"},
                "snippet": {
                    "title": "Test Live Stream",
                    "categoryId": "22"
                }
            }]
        }
        
        # Mock the flow
        mock_flow.from_client_secrets_file.return_value.run_local_server.return_value = mock.MagicMock()
        
        # Set up YouTube and wait for GUI update
        self.core.setup_youtube()
        self.gui.update_display()
        QTest.qWait(100)  # Wait for GUI to update
        
        # Check if GUI reflects the changes
        self.assertEqual(self.gui.current_title_display.text(), "Test Live Stream")
        self.assertTrue(self.core.is_live)
    
    def test_title_management_integration(self):
        """Test title management integration."""
        # Create titles file
        with open(os.path.join(self.temp_dir, "titles.txt"), "w") as f:
            f.write("Title 1\nTitle 2\nTitle 3\n")
        
        # Load titles and wait for GUI update
        self.core.load_titles()
        self.gui.update_display()
        QTest.qWait(100)  # Wait for GUI to update
        
        # Check if GUI reflects the changes
        self.assertEqual(self.gui.next_title_display.text(), "Title 1")
        
        # Mock YouTube API for update_title
        with mock.patch.object(self.core, 'youtube') as mock_youtube:
            mock_youtube.search().list().execute.return_value = {
                "items": [{
                    "id": {"videoId": "test_video_id"},
                    "snippet": {"title": "Current Title"}
                }]
            }
            mock_youtube.videos().list().execute.return_value = {
                "items": [{
                    "snippet": {"title": "Current Title"}
                }]
            }
            mock_youtube.videos().update().execute.return_value = {}
            
            # Set live status
            self.core.is_live = True
            self.core.channel_id = "test_channel_id"
            
            # Update title and wait for GUI update
            self.core.update_title()
            self.gui.update_display()
            QTest.qWait(100)  # Wait for GUI to update
            
            # Check if GUI reflects the changes
            self.assertEqual(self.gui.next_title_display.text(), "Title 2")
    
    def test_status_integration(self):
        """Test status integration."""
        # Set status and wait for GUI update
        self.core._set_status("Test Status", "success")
        self.gui.update_display()
        QTest.qWait(100)  # Wait for GUI to update
        
        # Check if GUI reflects the changes
        self.assertEqual(self.gui.statusBar.currentMessage(), "Test Status")
        
        # Set error status and wait for GUI update
        self.core._set_status("Error Message", "error")
        self.gui.update_display()
        QTest.qWait(100)  # Wait for GUI to update
        
        # Check if GUI reflects the changes
        self.assertEqual(self.gui.statusBar.currentMessage(), "Error Message")
    
    def test_button_integration(self):
        """Test button integration."""
        # Mock the update_title method
        with mock.patch.object(self.core, 'update_title') as mock_update:
            # Click the update button and wait for event processing
            QTest.mouseClick(self.gui.update_button, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            QTest.qWait(100)  # Wait for events to be processed
            mock_update.assert_called_once()
        
        # Mock the open_titles_file method
        with mock.patch.object(self.core, 'open_titles_file') as mock_open:
            # Click the open titles button and wait for event processing
            QTest.mouseClick(self.gui.open_titles_button, Qt.MouseButton.LeftButton)
            QApplication.processEvents()
            QTest.qWait(100)  # Wait for events to be processed
            mock_open.assert_called_once()
    
    def test_menu_integration(self):
        """Test menu integration."""
        menubar = self.gui.menuBar()
        file_menu = menubar.findChild(QMenu, "File")
        
        # Mock the open_config_dir method
        with mock.patch.object(self.core, 'open_config_dir') as mock_open:
            # Trigger the open config folder action and wait for event processing
            open_config_action = file_menu.actions()[0]
            open_config_action.trigger()
            QApplication.processEvents()
            QTest.qWait(100)  # Wait for events to be processed
            mock_open.assert_called_once()
        
        # Mock the check_live_status method
        with mock.patch.object(self.core, 'check_live_status') as mock_check:
            # Trigger the check now action and wait for event processing
            check_now_action = file_menu.actions()[3]
            check_now_action.trigger()
            QApplication.processEvents()
            QTest.qWait(100)  # Wait for events to be processed
            mock_check.assert_called_once() 