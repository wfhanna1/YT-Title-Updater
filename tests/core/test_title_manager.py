import pytest
import os
from datetime import datetime
import pytz
from youtube_updater.core.title_manager import TitleManager
from youtube_updater.core.default_title_generator import DefaultTitleGenerator

class TestTitleManager:
    """Test cases for TitleManager."""
    
    @pytest.fixture
    def temp_files(self, tmp_path):
        """Create temporary files for testing."""
        titles_file = tmp_path / "titles.txt"
        applied_titles_file = tmp_path / "applied-titles.txt"
        history_log = tmp_path / "history.log"
        
        return {
            "titles_file": str(titles_file),
            "applied_titles_file": str(applied_titles_file),
            "history_log": str(history_log)
        }
    
    @pytest.fixture
    def title_manager(self, temp_files):
        """Create a TitleManager instance with temporary files."""
        return TitleManager(
            titles_file=temp_files["titles_file"],
            applied_titles_file=temp_files["applied_titles_file"],
            history_log=temp_files["history_log"]
        )
    
    def test_get_next_title_with_empty_file(self, title_manager, monkeypatch):
        """Test getting next title when titles file is empty."""
        # Mock current time to a weekday
        mock_time = datetime(2024, 3, 18, 14, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
        monkeypatch.setattr("datetime.datetime", lambda *args, **kwargs: mock_time)
        
        title = title_manager.get_next_title()
        assert title == "Monday, March 18, 2024 - Divine Liturgy"
    
    def test_get_next_title_with_titles(self, title_manager):
        """Test getting next title when titles file has content."""
        # Add some titles
        with open(title_manager.titles_file, "w") as f:
            f.write("Title 1\nTitle 2\nTitle 3\n")
        
        # Get next title
        title = title_manager.get_next_title()
        assert title == "Title 1"
        
        # Verify rotation
        with open(title_manager.titles_file, "r") as f:
            titles = f.read().strip().split("\n")
            assert titles == ["Title 2", "Title 3", "Title 1"]
    
    def test_archive_title(self, title_manager):
        """Test archiving a title."""
        title = "Test Title"
        title_manager.archive_title(title)
        
        # Check applied titles file
        with open(title_manager.applied_titles_file, "r") as f:
            applied_titles = f.read().strip().split("\n")
            assert applied_titles[0] == title
        
        # Check history log
        with open(title_manager.history_log, "r") as f:
            history = f.read().strip().split("\n")
            assert title in history[0]
    
    def test_add_title(self, title_manager):
        """Test adding a new title."""
        title = "New Title"
        title_manager.add_title(title)
        
        # Check titles file
        with open(title_manager.titles_file, "r") as f:
            titles = f.read().strip().split("\n")
            assert titles[0] == title
    
    def test_default_title_on_saturday_evening(self, title_manager, monkeypatch):
        """Test default title generation on Saturday evening."""
        # Mock current time to Saturday at 6 PM
        mock_time = datetime(2024, 3, 23, 18, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
        monkeypatch.setattr("datetime.datetime", lambda *args, **kwargs: mock_time)
        
        title = title_manager.get_next_title()
        assert title == "Saturday, March 23, 2024 - Vespers and Midnight Praises"
    
    def test_default_title_on_saturday_morning(self, title_manager, monkeypatch):
        """Test default title generation on Saturday morning."""
        # Mock current time to Saturday at 10 AM
        mock_time = datetime(2024, 3, 23, 10, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
        monkeypatch.setattr("datetime.datetime", lambda *args, **kwargs: mock_time)
        
        title = title_manager.get_next_title()
        assert title == "Saturday, March 23, 2024 - Divine Liturgy" 