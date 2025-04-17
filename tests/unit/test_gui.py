import sys
from unittest import TestCase, mock
from PyQt6.QtWidgets import QApplication, QMenu, QStatusBar
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
from youtube_updater.gui import YouTubeUpdaterGUI
from youtube_updater.core import YouTubeUpdaterCore

class TestYouTubeUpdaterGUI(TestCase):
    """Test cases for YouTubeUpdaterGUI class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create QApplication instance
        cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock core with all required attributes
        self.mock_core = mock.MagicMock(spec=YouTubeUpdaterCore)
        self.mock_core.current_title = "Test Current Title"
        self.mock_core.next_title = "Test Next Title"
        self.mock_core.status = "Test Status"
        self.mock_core.status_type = "info"
        self.mock_core.is_live = True  # Add is_live attribute
        self.mock_core._test_mode = True  # Add test mode flag
        
        # Create GUI with mock core
        self.gui = YouTubeUpdaterGUI(core=self.mock_core)
        self.gui.show()
        QTest.qWaitForWindowExposed(self.gui)
    
    def tearDown(self):
        """Clean up test environment."""
        self.gui.close()
    
    def test_initialization(self):
        """Test GUI initialization."""
        self.assertEqual(self.gui.windowTitle(), "YouTube Title Updater")
        self.assertIsNotNone(self.gui.menuBar())
        self.assertIsNotNone(self.gui.statusBar)  # statusBar is a property, not a method
    
    def test_menu_creation(self):
        """Test menu creation."""
        menubar = self.gui.menuBar()
        file_menu = menubar.findChild(QMenu, "File")
        self.assertIsNotNone(file_menu)
        
        # Check menu actions
        actions = file_menu.actions()
        self.assertEqual(actions[0].text(), "Open Config Folder")
        self.assertEqual(actions[1].text(), "Open Titles File")
        self.assertEqual(actions[3].text(), "Check Now")
        self.assertEqual(actions[5].text(), "Exit")
    
    def test_status_update(self):
        """Test status update."""
        # Test different status types
        status_types = {
            "success": "green",
            "error": "red",
            "warning": "orange",
            "info": "black"
        }
        
        for status_type, color in status_types.items():
            self.mock_core.status_type = status_type
            self.mock_core.status = "Test Status"  # Reset status for each test
            self.gui.update_status()
            self.assertEqual(self.gui.statusBar.currentMessage(), "Test Status")
    
    def test_button_actions(self):
        """Test button actions."""
        # Test Update Title button
        QTest.mouseClick(self.gui.update_button, Qt.MouseButton.LeftButton)
        self.mock_core.check_live_status.assert_called_once()
        self.mock_core.update_title.assert_called_once()
        
        # Test Open Titles button
        QTest.mouseClick(self.gui.open_titles_button, Qt.MouseButton.LeftButton)
        self.mock_core.open_titles_file.assert_called_once()
    
    def test_menu_actions(self):
        """Test menu actions."""
        menubar = self.gui.menuBar()
        file_menu = menubar.findChild(QMenu, "File")
        
        # Test Open Config Folder action
        open_config_action = file_menu.actions()[0]
        open_config_action.trigger()
        self.mock_core.open_config_dir.assert_called_once()
        
        # Test Open Titles File action
        open_titles_action = file_menu.actions()[1]
        open_titles_action.trigger()
        self.mock_core.open_titles_file.assert_called_once()
        
        # Test Check Now action
        check_now_action = file_menu.actions()[3]
        check_now_action.trigger()
        self.mock_core.check_live_status.assert_called_once()
    
    def test_display_update(self):
        """Test display update."""
        # Update core values
        self.mock_core.current_title = "New Current Title"
        self.mock_core.next_title = "New Next Title"
        
        # Update display
        self.gui.update_display()
        
        # Check if labels were updated
        self.assertEqual(self.gui.current_title_display.text(), "New Current Title")
        self.assertEqual(self.gui.next_title_display.text(), "New Next Title")
    
    def test_error_handling(self):
        """Test error handling."""
        # Set error status
        self.mock_core.status_type = "error"
        self.mock_core.status = "Test Error Message"
        
        # Update status
        self.gui.update_status()
        
        # Check if error message was shown
        self.assertEqual(self.gui.statusBar.currentMessage(), "Test Error Message")