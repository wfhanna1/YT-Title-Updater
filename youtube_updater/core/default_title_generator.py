from datetime import datetime
import pytz
from typing import Optional
from .interfaces import ITitleGenerator

class DefaultTitleGenerator(ITitleGenerator):
    """Generates default titles based on current date and time."""
    
    def __init__(self, timezone: str = "US/Eastern"):
        """Initialize the title generator.
        
        Args:
            timezone: Timezone to use for time-based decisions (default: US/Eastern)
        """
        self.timezone = pytz.timezone(timezone)
    
    def generate_title(self) -> str:
        """Generate a title based on current date and time.
        
        Returns:
            str: Generated title following the pattern:
                - For Saturday after 5 PM EST: "Day of week, Month DD, YYYY - Vespers and Midnight Praises"
                - For all other times: "Day of week, Month DD, YYYY - Divine Liturgy"
        """
        current_time = datetime.now(self.timezone)
        
        # Format the date part
        date_part = current_time.strftime("%A, %B %d, %Y")
        
        # Determine if it's Saturday after 5 PM EST
        is_saturday_after_5pm = (
            current_time.weekday() == 5 and  # Saturday
            current_time.hour >= 17  # After 5 PM
        )
        
        # Generate the appropriate suffix
        suffix = "Vespers and Midnight Praises" if is_saturday_after_5pm else "Divine Liturgy"
        
        return f"{date_part} - {suffix}" 