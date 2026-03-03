"""Tests for DefaultTitleGenerator."""

import pytest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo
from youtube_updater.core.default_title_generator import DefaultTitleGenerator

PATCH_TARGET = "youtube_updater.core.default_title_generator.datetime"


class TestDefaultTitleGenerator:
    """Test cases for DefaultTitleGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a DefaultTitleGenerator instance."""
        return DefaultTitleGenerator()

    def _make_eastern_dt(self, year, month, day, hour, minute=0):
        """Return a timezone-aware datetime in US/Eastern."""
        return datetime(year, month, day, hour, minute, 0, tzinfo=ZoneInfo("US/Eastern"))

    def test_generate_title_weekday(self, generator):
        """Test title generation on a weekday (Monday)."""
        monday_2pm_est = self._make_eastern_dt(2024, 3, 18, 14)  # Monday

        with patch(PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = monday_2pm_est
            title = generator.generate_title()

        assert title == "Monday, March 18, 2024 - Divine Liturgy"

    def test_generate_title_saturday_morning(self, generator):
        """Test title generation on Saturday morning (before 5 PM)."""
        saturday_10am_est = self._make_eastern_dt(2024, 3, 23, 10)  # Saturday

        with patch(PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = saturday_10am_est
            title = generator.generate_title()

        assert title == "Saturday, March 23, 2024 - Divine Liturgy"

    def test_generate_title_saturday_evening(self, generator):
        """Test title generation on Saturday evening (after 5 PM)."""
        saturday_6pm_est = self._make_eastern_dt(2024, 3, 23, 18)  # Saturday at 6 PM

        with patch(PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = saturday_6pm_est
            title = generator.generate_title()

        assert title == "Saturday, March 23, 2024 - Vespers and Midnight Praises"

    def test_generate_title_saturday_late_night(self, generator):
        """Test title generation on Saturday late night (11:30 PM)."""
        saturday_1130pm_est = self._make_eastern_dt(2024, 3, 23, 23, 30)

        with patch(PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = saturday_1130pm_est
            title = generator.generate_title()

        assert title == "Saturday, March 23, 2024 - Vespers and Midnight Praises"

    def test_generate_title_saturday_after_midnight(self, generator):
        """Test title generation after midnight Sunday (should be Divine Liturgy)."""
        sunday_1230am_est = self._make_eastern_dt(2024, 3, 24, 0, 30)  # Sunday 12:30 AM

        with patch(PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = sunday_1230am_est
            title = generator.generate_title()

        assert title == "Sunday, March 24, 2024 - Divine Liturgy"

    def test_custom_timezone(self):
        """Test title generation with a custom timezone (US/Pacific)."""
        saturday_6pm_pacific = datetime(2024, 3, 23, 18, 0, 0, tzinfo=ZoneInfo("US/Pacific"))

        with patch(PATCH_TARGET) as mock_dt:
            mock_dt.now.return_value = saturday_6pm_pacific
            generator = DefaultTitleGenerator(timezone="US/Pacific")
            title = generator.generate_title()

        assert title == "Saturday, March 23, 2024 - Vespers and Midnight Praises"
