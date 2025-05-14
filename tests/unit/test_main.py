import sys
import unittest
from unittest.mock import patch, MagicMock
import argparse
import logging
from pathlib import Path
from youtube_updater.gui import YouTubeUpdaterGUI

# Import the main module
sys.path.append('.')  # Ensure we can import from the root directory
import youtube_title_updater


class TestMainApplication(unittest.TestCase):
    """Test cases for the main application entry point and argument handling."""
    
    def setUp(self):
        """Set up test environment."""
        # Save original sys.argv
        self.original_argv = sys.argv
    
    def tearDown(self):
        """Clean up test environment."""
        # Restore original sys.argv
        sys.argv = self.original_argv
    
    def test_parse_arguments_defaults(self):
        """Test parsing command line arguments with defaults."""
        # Set up test arguments
        sys.argv = ['youtube_title_updater.py']
        
        # Parse arguments
        args = youtube_title_updater.parse_arguments()
        
        # Verify defaults
        self.assertIsNone(args.config_dir)
        self.assertEqual(args.log_level, 'INFO')
    
    def test_parse_arguments_custom(self):
        """Test parsing command line arguments with custom values."""
        # Set up test arguments
        sys.argv = ['youtube_title_updater.py', 
                   '--config-dir', '/custom/config/dir',
                   '--log-level', 'DEBUG']
        
        # Parse arguments
        args = youtube_title_updater.parse_arguments()
        
        # Verify custom values
        self.assertEqual(args.config_dir, '/custom/config/dir')
        self.assertEqual(args.log_level, 'DEBUG')
    
    def test_parse_arguments_invalid_log_level(self):
        """Test parsing command line arguments with invalid log level."""
        # Set up test arguments with invalid log level
        sys.argv = ['youtube_title_updater.py', '--log-level', 'INVALID']
        
        # Should raise SystemExit because argparse will exit on invalid choice
        with self.assertRaises(SystemExit):
            youtube_title_updater.parse_arguments()
    
    @patch('youtube_title_updater.logging')
    def test_logging_setup(self, mock_logging):
        """Test logging setup with different log levels."""
        # Set up mock logger
        mock_root_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_root_logger
        
        # Test different log levels
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            # Set up test arguments
            sys.argv = ['youtube_title_updater.py', '--log-level', level]
            
            # Call main function with minimum execution
            with patch('youtube_title_updater.QApplication'), \
                 patch('youtube_title_updater.YouTubeUpdaterGUI'):
                try:
                    youtube_title_updater.main()
                except Exception:
                    pass  # We don't care about other errors here
            
            # Verify log level was set
            mock_logging.getLogger().setLevel.assert_called_with(getattr(logging, level))
    
    @patch('youtube_title_updater.Path')
    @patch('youtube_title_updater.YouTubeUpdaterGUI')
    @patch('youtube_title_updater.QApplication')
    def test_custom_config_dir_path_object(self, mock_app, mock_gui, mock_path):
        """Test handling of custom config directory as Path object."""
        # Set up test arguments
        sys.argv = ['youtube_title_updater.py', '--config-dir', '/custom/config/path']
        
        # Set up mocks
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        
        # Call main function
        with patch('youtube_title_updater.sys.exit'):
            youtube_title_updater.main()
        
        # Verify Path object was created and passed to GUI
        mock_path.assert_called_with('/custom/config/path')
        mock_gui.assert_called_with(config_dir=mock_path_instance)
    
    @patch('youtube_title_updater.YouTubeUpdaterGUI')
    @patch('youtube_title_updater.QApplication')
    def test_main_with_no_config_dir(self, mock_app, mock_gui):
        """Test main function with no custom config directory."""
        # Set up test arguments
        sys.argv = ['youtube_title_updater.py']
        
        # Call main function
        with patch('youtube_title_updater.sys.exit'):
            youtube_title_updater.main()
        
        # Verify GUI was initialized with None config_dir
        mock_gui.assert_called_with(config_dir=None)
    
    @patch('youtube_title_updater.logger')
    def test_main_exception_handling(self, mock_logger):
        """Test exception handling in main function."""
        # Set up test arguments
        sys.argv = ['youtube_title_updater.py']
        
        # Make QApplication raise an exception
        with patch('youtube_title_updater.QApplication', 
                  side_effect=Exception("Test exception")):
            result = youtube_title_updater.main()
        
        # Verify exception was logged and error code returned
        mock_logger.critical.assert_called_once()
        self.assertEqual(result, 1)
        

if __name__ == '__main__':
    unittest.main() 