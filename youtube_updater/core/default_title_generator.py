from datetime import datetime
import pytz
from typing import Optional

class DefaultTitleGenerator:
    """Generates dynamic titles based on current time and day."""
    
    def __init__(self, timezone: str = "US/Eastern"):
        """Initialize the title generator.
        
        Args:
            timezone: Timezone to use for title generation (default: US/Eastern)
        """
        self.timezone = timezone
        self.tz = pytz.timezone(timezone)
    
    def generate_title(self) -> str:
        """Generate a title based on current time and day.
        
        Returns:
            str: Generated title
        """
        now = datetime.now(self.tz)
        weekday = now.weekday()  # Monday=0, Sunday=6
        hour = now.hour
        
        # Saturday logic (weekday=5)
        if weekday == 5:  # Saturday
            if hour < 17:  # Before 5 PM
                return f"{now.strftime('%A, %B %d, %Y')} - Divine Liturgy"
            else:  # 5 PM and after
                return f"{now.strftime('%A, %B %d, %Y')} - Vespers and Midnight Praises"
        
        # Sunday logic (weekday=6)
        elif weekday == 6:  # Sunday
            return f"{now.strftime('%A, %B %d, %Y')} - Divine Liturgy"
        
        # Weekday logic (Monday=0 through Friday=4)
        else:
            return f"{now.strftime('%A, %B %d, %Y')} - Divine Liturgy"
    
    def generate_title_for_datetime(self, dt: datetime) -> str:
        """Generate a title for a specific datetime.
        
        Args:
            dt: Datetime to generate title for
            
        Returns:
            str: Generated title
        """
        # Convert to our timezone if it's naive
        if dt.tzinfo is None:
            dt = self.tz.localize(dt)
        else:
            dt = dt.astimezone(self.tz)
        
        weekday = dt.weekday()
        hour = dt.hour
        
        # Saturday logic
        if weekday == 5:  # Saturday
            if hour < 17:  # Before 5 PM
                return f"{dt.strftime('%A, %B %d, %Y')} - Divine Liturgy"
            else:  # 5 PM and after
                return f"{dt.strftime('%A, %B %d, %Y')} - Vespers and Midnight Praises"
        
        # Sunday logic
        elif weekday == 6:  # Sunday
            return f"{dt.strftime('%A, %B %d, %Y')} - Divine Liturgy"
        
        # Weekday logic
        else:
            return f"{dt.strftime('%A, %B %d, %Y')} - Divine Liturgy"
    
    def get_service_type(self, dt: Optional[datetime] = None) -> str:
        """Get the type of service for a given time.
        
        Args:
            dt: Datetime to check (defaults to current time)
            
        Returns:
            str: Service type
        """
        if dt is None:
            dt = datetime.now(self.tz)
        else:
            if dt.tzinfo is None:
                dt = self.tz.localize(dt)
            else:
                dt = dt.astimezone(self.tz)
        
        weekday = dt.weekday()
        hour = dt.hour
        
        if weekday == 5:  # Saturday
            if hour < 17:
                return "Divine Liturgy"
            else:
                return "Vespers and Midnight Praises"
        elif weekday == 6:  # Sunday
            return "Divine Liturgy"
        else:
            return "Divine Liturgy"
