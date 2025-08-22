import os
import sys
import tempfile
import shutil
from unittest import TestCase, mock
from pathlib import Path
from youtube_updater.core import ComponentFactory, YouTubeUpdaterCore

class TestYouTubeUpdaterCore(TestCase):
    """Test cases for YouTubeUpdaterCore class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.core = ComponentFactory.create_core(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test core initialization."""
        self.assertIsNotNone(self.core)
        self.assertEqual(self.core.current_title, "Not Live")
        self.assertFalse(self.core.is_live)
        self.assertEqual(self.core.status, "Initializing")
        self.assertEqual(self.core.status_type, "info")
    
    def test_config_dir_setup(self):
        """Test configuration directory setup."""
        # Test with custom config dir
        custom_dir = os.path.join(self.temp_dir, "custom_config")
        core = ComponentFactory.create_core(config_dir=custom_dir)
        self.assertEqual(str(core.config.config_dir), custom_dir)
        
        # Test default config dir (when no config_dir is provided)
        # This will use platform-specific default
        core_default = ComponentFactory.create_core()
        self.assertIsNotNone(core_default.config.config_dir)
    
    def test_file_paths_setup(self):
        """Test file paths setup."""
        # Only essential files are created by default
        expected_files = [
            "titles.txt",
            "applied-titles.txt",
            "history.log"
        ]
        
        for file in expected_files:
            file_path = os.path.join(self.temp_dir, file)
            self.assertTrue(os.path.exists(file_path))
        
        # Token and client secrets files should exist as paths but not as actual files
        token_path = os.path.join(self.temp_dir, "token.pickle")
        client_secrets_path = os.path.join(self.temp_dir, "client_secrets.json")
        
        # These should exist as paths in the config but not as actual files
        self.assertEqual(self.core.config.token_path, token_path)
        self.assertEqual(self.core.config.client_secrets_path, client_secrets_path)
        
        # But the actual files should not exist yet
        self.assertFalse(os.path.exists(token_path))
        self.assertFalse(os.path.exists(client_secrets_path))
    
    def test_status_management(self):
        """Test status message and type management."""
        # Test setting status
        self.core._set_status("Test message", "success")
        self.assertEqual(self.core.status, "Test message")
        self.assertEqual(self.core.status_type, "success")
        
        # Test invalid status type
        with self.assertRaises(ValueError):
            self.core._set_status("Test message", "invalid_type")
    
    def test_title_management(self):
        """Test title management functionality."""
        # Test adding titles
        self.core.add_title("Test Title 1")
        self.core.add_title("Test Title 2")
        
        # Test getting next title
        next_title = self.core.get_next_title()
        self.assertEqual(next_title, "Test Title 1")
        
        # Test next_title property
        self.assertEqual(self.core.next_title, "Test Title 2")
    
    def test_live_status_check_without_youtube_client(self):
        """Test live status check when YouTube client is not initialized."""
        # YouTube client should be None without client secrets
        self.assertIsNone(self.core.youtube_client)
        
        # Check live status should set error status
        self.core.check_live_status()
        self.assertEqual(self.core.status, "YouTube client not initialized")
        self.assertEqual(self.core.status_type, "error")
    
    def test_title_update_without_youtube_client(self):
        """Test title update when YouTube client is not initialized."""
        # Add a title first
        self.core.add_title("Test Title")
        
        # Try to update title without YouTube client
        self.core.update_title()
        self.assertEqual(self.core.status, "YouTube client not initialized")
        self.assertEqual(self.core.status_type, "error")
    
    def test_component_creation(self):
        """Test that all components are created correctly."""
        self.assertIsNotNone(self.core.config)
        self.assertIsNotNone(self.core.title_manager)
        
        # Auth manager and YouTube client should be None without client secrets
        self.assertIsNone(self.core.auth_manager)
        self.assertIsNone(self.core.youtube_client)
    
    def test_title_manager_functionality(self):
        """Test title manager methods work correctly."""
        title_manager = self.core.title_manager
        
        # Test adding titles
        title_manager.add_title("Test Title 1")
        title_manager.add_title("Test Title 2")
        
        # Test getting next title
        next_title = title_manager.get_next_title()
        self.assertEqual(next_title, "Test Title 1")
        
        # Test archiving title
        title_manager.archive_title("Test Title 1")
        
        # Check that files were created/updated
        self.assertTrue(os.path.exists(self.core.config.applied_titles_file))
        self.assertTrue(os.path.exists(self.core.config.history_log))
    
    def test_config_manager_functionality(self):
        """Test config manager methods work correctly."""
        config_manager = self.core.config
        
        # Test getting file paths
        file_paths = config_manager.get_file_paths()
        expected_keys = ["titles_file", "applied_titles_file", "token_path", 
                        "client_secrets_path", "history_log"]
        
        for key in expected_keys:
            self.assertIn(key, file_paths)
        
        # Test client secrets check
        self.assertFalse(config_manager.ensure_client_secrets())
        
        # Test getting client secrets path
        expected_path = os.path.join(self.temp_dir, "client_secrets.json")
        self.assertEqual(config_manager.get_client_secrets_path(), expected_path) 