import pytest
from datetime import datetime
import pytz
from youtube_updater.core.default_title_generator import DefaultTitleGenerator

class TestDefaultTitleGenerator:
    """Test cases for DefaultTitleGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create a DefaultTitleGenerator instance."""
        return DefaultTitleGenerator()
    
    def test_generate_title_weekday(self, generator, monkeypatch):
        """Test title generation on a weekday."""
        # Mock current time to a weekday (Monday) at 2 PM
        mock_time = datetime(2024, 3, 18, 14, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
        monkeypatch.setattr("datetime.datetime", lambda *args, **kwargs: mock_time)
        
        title = generator.generate_title()
        assert title == "Monday, March 18, 2024 - Divine Liturgy"
    
    def test_generate_title_saturday_morning(self, generator, monkeypatch):
        """Test title generation on Saturday morning."""
        # Mock current time to Saturday at 10 AM
        mock_time = datetime(2024, 3, 23, 10, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
        monkeypatch.setattr("datetime.datetime", lambda *args, **kwargs: mock_time)
        
        title = generator.generate_title()
        assert title == "Saturday, March 23, 2024 - Divine Liturgy"
    
    def test_generate_title_saturday_evening(self, generator, monkeypatch):
        """Test title generation on Saturday evening."""
        # Mock current time to Saturday at 6 PM
        mock_time = datetime(2024, 3, 23, 18, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
        monkeypatch.setattr("datetime.datetime", lambda *args, **kwargs: mock_time)
        
        title = generator.generate_title()
        assert title == "Saturday, March 23, 2024 - Vespers and Midnight Praises"
    
    def test_generate_title_saturday_late_night(self, generator, monkeypatch):
        """Test title generation on Saturday late night."""
        # Mock current time to Saturday at 11:30 PM
        mock_time = datetime(2024, 3, 23, 23, 30, 0, tzinfo=pytz.timezone("US/Eastern"))
        monkeypatch.setattr("datetime.datetime", lambda *args, **kwargs: mock_time)
        
        title = generator.generate_title()
        assert title == "Saturday, March 23, 2024 - Vespers and Midnight Praises"
    
    def test_generate_title_saturday_after_midnight(self, generator, monkeypatch):
        """Test title generation on Saturday after midnight."""
        # Mock current time to Saturday at 12:30 AM
        mock_time = datetime(2024, 3, 24, 0, 30, 0, tzinfo=pytz.timezone("US/Eastern"))
        monkeypatch.setattr("datetime.datetime", lambda *args, **kwargs: mock_time)
        
        title = generator.generate_title()
        assert title == "Sunday, March 24, 2024 - Divine Liturgy"
    
    def test_custom_timezone(self):
        """Test title generation with a custom timezone."""
        # Create generator with Pacific timezone
        generator = DefaultTitleGenerator(timezone="US/Pacific")
        
        # Mock current time to Saturday at 6 PM Pacific (9 PM Eastern)
        mock_time = datetime(2024, 3, 23, 21, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
        monkeypatch.setattr("datetime.datetime", lambda *args, **kwargs: mock_time)
        
        title = generator.generate_title()
        assert title == "Saturday, March 23, 2024 - Vespers and Midnight Praises" 