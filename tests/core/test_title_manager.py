"""Tests for TitleManager."""

import pytest
import os
from datetime import datetime
from unittest.mock import patch
import pytz
from youtube_updater.core.title_manager import TitleManager
from youtube_updater.core.default_title_generator import DefaultTitleGenerator

DATETIME_PATCH_TARGET = "youtube_updater.core.default_title_generator.datetime"


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
            "history_log": str(history_log),
        }

    @pytest.fixture
    def title_manager(self, temp_files):
        """Create a TitleManager instance with temporary files."""
        return TitleManager(
            titles_file=temp_files["titles_file"],
            applied_titles_file=temp_files["applied_titles_file"],
            history_log=temp_files["history_log"],
        )

    def _make_eastern_dt(self, year, month, day, hour, minute=0):
        """Return a timezone-aware datetime in US/Eastern."""
        est = pytz.timezone("US/Eastern")
        return est.localize(datetime(year, month, day, hour, minute, 0))

    def test_get_next_title_with_empty_file(self, title_manager):
        """Test getting next title when titles file is empty uses default generator."""
        monday_2pm_est = self._make_eastern_dt(2024, 3, 18, 14)  # Monday

        with patch(DATETIME_PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = monday_2pm_est
            title = title_manager.get_next_title()

        assert title == "Monday, March 18, 2024 - Divine Liturgy"

    def test_get_next_title_with_titles(self, title_manager):
        """Test getting next title when titles file has content."""
        with open(title_manager.titles_file, "w") as f:
            f.write("Title 1\nTitle 2\nTitle 3\n")

        # Reload titles after writing
        title_manager.load_titles()

        title = title_manager.get_next_title()
        assert title == "Title 1"

        # Verify rotation -- titles should have been rotated
        with open(title_manager.titles_file, "r") as f:
            titles = [line.strip() for line in f if line.strip()]
        assert titles == ["Title 2", "Title 3", "Title 1"]

    def test_archive_title(self, title_manager):
        """Test archiving a title writes to applied titles and history."""
        title = "Test Title"
        title_manager.archive_title(title)

        with open(title_manager.applied_titles_file, "r") as f:
            applied_titles = f.read().strip().split("\n")
        assert applied_titles[0] == title

        with open(title_manager.history_log, "r") as f:
            history = f.read().strip().split("\n")
        assert title in history[0]

    def test_add_title(self, title_manager):
        """Test adding a new title appends to the titles file."""
        title = "New Title"
        title_manager.add_title(title)

        with open(title_manager.titles_file, "r") as f:
            titles = [line.strip() for line in f if line.strip()]
        assert title in titles

    def test_default_title_on_saturday_evening(self, title_manager):
        """Test default title generation on Saturday evening (Vespers)."""
        saturday_6pm_est = self._make_eastern_dt(2024, 3, 23, 18)

        with patch(DATETIME_PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = saturday_6pm_est
            title = title_manager.get_next_title()

        assert title == "Saturday, March 23, 2024 - Vespers and Midnight Praises"

    def test_default_title_on_saturday_morning(self, title_manager):
        """Test default title generation on Saturday morning (Divine Liturgy)."""
        saturday_10am_est = self._make_eastern_dt(2024, 3, 23, 10)

        with patch(DATETIME_PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = saturday_10am_est
            title = title_manager.get_next_title()

        assert title == "Saturday, March 23, 2024 - Divine Liturgy"
