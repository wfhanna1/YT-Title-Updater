import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

class Logger:
    """Handles all logging operations for the application."""
    
    def __init__(self, log_file: Optional[str] = None):
        """Initialize the logger.
        
        Args:
            log_file: Optional path to log file
        """
        self.logger = logging.getLogger("youtube_updater")
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Add file handler if log file specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def log_title_update(self, title: str, log_file: str) -> None:
        """Log title update to history file.
        
        Args:
            title: Title that was updated
            log_file: Path to history log file
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write(f"{timestamp}: {title}\n") 