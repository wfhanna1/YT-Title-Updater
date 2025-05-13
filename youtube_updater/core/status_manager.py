from typing import Optional, Callable
from ..utils.logger import Logger

class StatusManager:
    """Manages application status updates."""
    
    STATUS_TYPES = ("info", "success", "error", "warning")
    
    def __init__(self, logger: Optional[Logger] = None):
        """Initialize the status manager.
        
        Args:
            logger: Optional logger instance
        """
        self._status = "Initializing"
        self._status_type = "info"
        self._logger = logger
        self._status_callbacks: List[Callable[[str, str], None]] = []
    
    @property
    def status(self) -> str:
        """Get the current status message."""
        return self._status
    
    @property
    def status_type(self) -> str:
        """Get the current status type."""
        return self._status_type
    
    def set_status(self, message: str, status_type: str = "info") -> None:
        """Set status message and type.
        
        Args:
            message: Status message
            status_type: One of: info, success, error, warning
        """
        if status_type not in self.STATUS_TYPES:
            raise ValueError(f"Invalid status type. Must be one of: {self.STATUS_TYPES}")
            
        self._status = message
        self._status_type = status_type
        
        # Log the status if logger is available
        if self._logger:
            if status_type == "error":
                self._logger.error(message)
            elif status_type == "warning":
                self._logger.warning(message)
            else:
                self._logger.info(message)
        
        # Notify all callbacks
        for callback in self._status_callbacks:
            callback(message, status_type)
    
    def add_status_callback(self, callback: Callable[[str, str], None]) -> None:
        """Add a callback to be notified of status changes.
        
        Args:
            callback: Function to call with (message, status_type)
        """
        self._status_callbacks.append(callback) 