import os
import tempfile
import shutil
from unittest import TestCase
from youtube_updater.core.title_manager import TitleManager

class TestTitleManager(TestCase):
    """Test cases for TitleManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.titles_file = os.path.join(self.temp_dir, "titles.txt")
        self.applied_titles_file = os.path.join(self.temp_dir, "applied-titles.txt")
        self.history_log = os.path.join(self.temp_dir, "history.log")
        
        self.title_manager = TitleManager(
            self.titles_file,
            self.applied_titles_file,
            self.history_log
        )
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test title manager initialization."""
        self.assertIsNotNone(self.title_manager)
        self.assertEqual(self.title_manager.titles_file, self.titles_file)
        self.assertEqual(self.title_manager.applied_titles_file, self.applied_titles_file)
        self.assertEqual(self.title_manager.history_log, self.history_log)
    
    def test_file_creation(self):
        """Test that required files are created."""
        for file_path in [self.titles_file, self.applied_titles_file, self.history_log]:
            self.assertTrue(os.path.exists(file_path))
    
    def test_add_title(self):
        """Test adding titles."""
        self.title_manager.add_title("Test Title 1")
        self.title_manager.add_title("Test Title 2")
        
        # Check that titles were written to file
        with open(self.titles_file, "r") as f:
            content = f.read().strip()
        
        self.assertIn("Test Title 1", content)
        self.assertIn("Test Title 2", content)
    
    def test_get_next_title(self):
        """Test getting next title."""
        # Add some titles
        self.title_manager.add_title("Title 1")
        self.title_manager.add_title("Title 2")
        
        # Get next title
        next_title = self.title_manager.get_next_title()
        self.assertEqual(next_title, "Title 1")
        
        # Check that titles were rotated
        with open(self.titles_file, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        
        self.assertEqual(lines[0], "Title 2")
        self.assertEqual(lines[1], "Title 1")
    
    def test_get_next_title_empty(self):
        """Test getting next title when no titles are available."""
        # No titles added, should generate dynamic title
        next_title = self.title_manager.get_next_title()
        self.assertIsNotNone(next_title)
        
        # Should be a dynamic title with date and service type
        # Format: "Day, Month DD, YYYY - Service Type"
        self.assertIn(" - ", next_title)
        self.assertIn("Divine Liturgy", next_title)
        
        # Should contain a date format
        import re
        date_pattern = r'\w+, \w+ \d{1,2}, \d{4}'
        self.assertIsNotNone(re.search(date_pattern, next_title))
    
    def test_archive_title(self):
        """Test archiving a title."""
        # Archive a title
        self.title_manager.archive_title("Test Title")
        
        # Check applied titles file
        with open(self.applied_titles_file, "r") as f:
            applied_titles = [line.strip() for line in f if line.strip()]
        
        self.assertIn("Test Title", applied_titles)
        
        # Check history log
        with open(self.history_log, "r") as f:
            history = f.read()
        
        self.assertIn("Test Title", history)
    
    def test_rotate_titles(self):
        """Test title rotation."""
        # Add titles
        self.title_manager.add_title("Title 1")
        self.title_manager.add_title("Title 2")
        self.title_manager.add_title("Title 3")
        
        # Rotate titles
        used_title = self.title_manager.rotate_titles()
        self.assertEqual(used_title, "Title 1")
        
        # Check that titles were rotated
        with open(self.titles_file, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        
        self.assertEqual(lines[0], "Title 2")
        self.assertEqual(lines[1], "Title 3")
        self.assertEqual(lines[2], "Title 1")
    
    def test_rotate_titles_empty(self):
        """Test title rotation when no titles are available."""
        # No titles, should return None
        used_title = self.title_manager.rotate_titles()
        self.assertIsNone(used_title)
    
    def test_load_titles(self):
        """Test loading titles from file."""
        # Create titles file with content
        with open(self.titles_file, "w") as f:
            f.write("Loaded Title 1\nLoaded Title 2\n")
        
        # Reload titles
        self.title_manager.load_titles()
        
        # Check that titles were loaded
        self.assertEqual(len(self.title_manager.titles), 2)
        self.assertEqual(self.title_manager.titles[0], "Loaded Title 1")
        self.assertEqual(self.title_manager.titles[1], "Loaded Title 2")
        self.assertEqual(self.title_manager.next_title, "Loaded Title 1")
    
    def test_load_titles_empty_file(self):
        """Test loading titles from empty file."""
        # Create empty titles file
        with open(self.titles_file, "w") as f:
            f.write("")
        
        # Reload titles
        self.title_manager.load_titles()
        
        # Check that titles list is empty
        self.assertEqual(len(self.title_manager.titles), 0)
        self.assertIsNone(self.title_manager.next_title)
