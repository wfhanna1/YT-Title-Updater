from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Protocol
from google.oauth2.credentials import Credentials

class IYouTubeClient(ABC):
    """Interface for YouTube API client."""
    
    @abstractmethod
    def get_channel_id(self) -> str:
        """Get the authenticated user's channel ID."""
        pass
    
    @abstractmethod
    def get_live_stream_info(self) -> Dict[str, Any]:
        """Get information about the current live stream."""
        pass
    
    @abstractmethod
    def update_video_title(self, video_id: str, new_title: str) -> None:
        """Update the title of a video."""
        pass

class IAuthManager(ABC):
    """Interface for authentication manager."""
    
    @abstractmethod
    def get_credentials(self) -> Credentials:
        """Get valid credentials for YouTube API."""
        pass

class ITitleManager(ABC):
    """Interface for title manager."""
    
    @abstractmethod
    def get_next_title(self) -> str:
        """Get the next title in the rotation."""
        pass
    
    @abstractmethod
    def rotate_titles(self) -> str:
        """Rotate to the next title in the list."""
        pass
    
    @abstractmethod
    def archive_title(self, title: str) -> None:
        """Archive a title that has been used."""
        pass
    
    @abstractmethod
    def add_title(self, title: str) -> None:
        """Add a new title to the list."""
        pass

class IConfigManager(ABC):
    """Interface for configuration manager."""
    
    @abstractmethod
    def get_file_paths(self) -> Dict[str, str]:
        """Get all file paths used by the application."""
        pass
    
    @abstractmethod
    def ensure_client_secrets(self) -> bool:
        """Check if client secrets file exists."""
        pass
    
    @abstractmethod
    def get_client_secrets_path(self) -> str:
        """Get the path to the client secrets file."""
        pass

class IFileOperations(ABC):
    """Interface for file operations."""
    
    @abstractmethod
    def ensure_file_exists(self, file_path: str, default_content: str = "") -> None:
        """Ensure a file exists, create it with default content if it doesn't."""
        pass
    
    @abstractmethod
    def read_lines(self, file_path: str) -> List[str]:
        """Read lines from a file."""
        pass
    
    @abstractmethod
    def write_lines(self, file_path: str, lines: List[str]) -> None:
        """Write lines to a file."""
        pass
    
    @abstractmethod
    def append_line(self, file_path: str, line: str) -> None:
        """Append a line to a file."""
        pass
    
    @abstractmethod
    def get_current_time(self) -> str:
        """Get the current time in a formatted string."""
        pass

class ITitleGenerator(Protocol):
    """Interface for title generation strategies."""
    
    def generate_title(self) -> str:
        """Generate a title based on the strategy.
        
        Returns:
            str: Generated title
        """
        pass 