import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from pathlib import Path

# Import the components
from youtube_updater.core import YouTubeUpdaterCore
from youtube_updater.gui import YouTubeUpdaterGUI

class TestIntegrationWorkflow(unittest.TestCase):
    """Integration test for the complete workflow of the application."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment once for all tests."""
        # Create QApplication instance
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """Set up test environment for each test."""
        # Create a temporary directory for configuration
        self.test_dir = tempfile.mkdtemp()
        
        # Create necessary test files
        self.setup_test_files()
        
        # Create a mock for the YouTube API service
        self.setup_youtube_mock()
        
        # Create core and GUI instances
        self.core = YouTubeUpdaterCore(config_dir=self.test_dir)
        self.core.youtube = self.mock_youtube
        self.core.channel_id = "test_channel_id"
        self.core.is_live = False
        
        # Override the check_live_status method to control live status
        self.original_check_live_status = self.core.check_live_status
        self.core.check_live_status = MagicMock(return_value=False)
        
        # Create GUI with the core
        self.gui = YouTubeUpdaterGUI(core=self.core)
        self.gui.show()
        QTest.qWaitForWindowExposed(self.gui)
    
    def tearDown(self):
        """Clean up after each test."""
        # Close the GUI
        self.gui.close()
        
        # Restore original check_live_status method
        if hasattr(self, 'original_check_live_status'):
            self.core.check_live_status = self.original_check_live_status
        
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
    
    def setup_test_files(self):
        """Create necessary test files in the temporary directory."""
        # Create titles.txt with test titles
        with open(os.path.join(self.test_dir, "titles.txt"), "w") as f:
            f.write("Test Title 1\nTest Title 2\nTest Title 3\n")
        
        # Create empty applied-titles.txt and history.log
        with open(os.path.join(self.test_dir, "applied-titles.txt"), "w") as f:
            f.write("")
        with open(os.path.join(self.test_dir, "history.log"), "w") as f:
            f.write("")
        
        # Create mock client_secrets.json
        with open(os.path.join(self.test_dir, "client_secrets.json"), "w") as f:
            f.write('{"installed": {"client_id": "test_client_id"}}')
    
    def setup_youtube_mock(self):
        """Set up mock YouTube API service."""
        self.mock_youtube = MagicMock()
        
        # Mock search response for live streams
        mock_search_response = {
            "items": [{
                "id": {"videoId": "test_video_id"},
                "snippet": {"title": "Current Live Title"}
            }]
        }
        self.mock_youtube.search().list().execute.return_value = mock_search_response
        
        # Mock video update response
        self.mock_youtube.videos().update().execute.return_value = {}
    
    def test_complete_workflow(self):
        """Test the complete workflow from start to finish."""
        # Initial state check
        self.assertEqual(self.gui.current_title_display.text(), "Not Live")
        self.assertEqual(self.gui.next_title_display.text(), "Test Title 1")
        self.assertEqual(self.gui.live_status_display.text(), "Not Live")
        self.assertFalse(self.gui.update_button.isEnabled())
        
        # 1. Simulate going live
        with patch.object(self.gui, '_notify_went_live', return_value=None):
            # Change mock live status
            self.core.is_live = True
            self.core.check_live_status.return_value = True
            self.core.current_title = "Current Live Title"
            
            # Trigger check_status
            QTest.mouseClick(self.gui.refresh_button, Qt.MouseButton.LeftButton)
            
            # Verify display updated
            self.assertEqual(self.gui.current_title_display.text(), "Current Live Title")
            self.assertEqual(self.gui.live_status_display.text(), "LIVE")
            self.assertTrue(self.gui.update_button.isEnabled())
        
        # 2. Test updating the title
        with patch('youtube_updater.gui.QMessageBox'):
            # Trigger update title
            QTest.mouseClick(self.gui.update_button, Qt.MouseButton.LeftButton)
            
            # Verify core methods were called
            self.core.update_title.assert_called_once()
            
            # Check history.log for title change
            with open(os.path.join(self.test_dir, "history.log"), "r") as f:
                history = f.read()
            
            # History log should have been written to
            self.assertTrue(len(history) > 0)
        
        # 3. Test going offline
        with patch.object(self.gui, '_notify_went_live', return_value=None):
            # Change mock live status
            self.core.is_live = False
            self.core.check_live_status.return_value = False
            self.core.current_title = "Not Live"
            
            # Trigger check_status
            QTest.mouseClick(self.gui.refresh_button, Qt.MouseButton.LeftButton)
            
            # Verify display updated
            self.assertEqual(self.gui.current_title_display.text(), "Not Live")
            self.assertEqual(self.gui.live_status_display.text(), "Not Live")
            self.assertFalse(self.gui.update_button.isEnabled())
    
    def test_menu_actions(self):
        """Test the menu actions in an integrated context."""
        # Get the menu bar
        menubar = self.gui.menuBar()
        file_menu = menubar.findChild(QMenu, "File")
        
        # Save references to original system methods
        original_open_config = self.core.open_config_dir
        original_open_titles = self.core.open_titles_file
        
        try:
            # Mock core methods
            self.core.open_config_dir = MagicMock(return_value=True)
            self.core.open_titles_file = MagicMock(return_value=True)
            
            # Trigger Open Config Folder action
            open_config_action = file_menu.actions()[0]
            open_config_action.trigger()
            self.core.open_config_dir.assert_called_once()
            
            # Trigger Open Titles File action
            open_titles_action = file_menu.actions()[1]
            open_titles_action.trigger()
            self.core.open_titles_file.assert_called_once()
            
            # Check title file exists
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, "titles.txt")))
            
        finally:
            # Restore original methods
            self.core.open_config_dir = original_open_config
            self.core.open_titles_file = original_open_titles
    
    def test_error_handling_integration(self):
        """Test error handling in an integrated context."""
        # Make update_title raise an exception
        self.core.update_title = MagicMock(side_effect=Exception("Test error"))
        
        # Set up live status
        self.core.is_live = True
        self.core.check_live_status.return_value = True
        
        # Mock QMessageBox to avoid dialogs
        with patch('youtube_updater.gui.QMessageBox'):
            # Trigger update title
            QTest.mouseClick(self.gui.update_button, Qt.MouseButton.LeftButton)
            
            # Verify error status updated
            self.assertTrue(self.gui.statusBar.currentMessage())
            
            # Check history.log for error
            with open(os.path.join(self.test_dir, "history.log"), "r") as f:
                history = f.read()
            
            # Log file should have content after error
            self.assertTrue(len(history) > 0)
    
    def test_title_rotation_integration(self):
        """Test title rotation in an integrated context."""
        # Set up initial titles state
        self.core.titles = ["Title 1", "Title 2", "Title 3"]
        self.core.next_title = "Title 1"
        
        # Mock out actual API calls
        original_update_title = self.core.update_title
        self.core.update_title = MagicMock(return_value=True)
        
        try:
            # Set live status
            self.core.is_live = True
            self.core.check_live_status.return_value = True
            
            # Capture initial state
            initial_next_title = self.core.next_title
            
            # Mock QMessageBox to avoid dialogs
            with patch('youtube_updater.gui.QMessageBox'):
                # Trigger update title
                QTest.mouseClick(self.gui.update_button, Qt.MouseButton.LeftButton)
                
                # Call the actual _rotate_titles method
                self.core.update_title.assert_called_once()
                
                # The next title should have changed
                with open(os.path.join(self.test_dir, "titles.txt"), "r") as f:
                    remaining_titles = [line.strip() for line in f if line.strip()]
                
                # Verify applied-titles.txt has the archived title
                with open(os.path.join(self.test_dir, "applied-titles.txt"), "r") as f:
                    applied_titles = f.read()
                
                # Applied titles file should have content
                self.assertTrue(len(applied_titles) > 0)
        
        finally:
            # Restore original method
            self.core.update_title = original_update_title

if __name__ == '__main__':
    unittest.main() 