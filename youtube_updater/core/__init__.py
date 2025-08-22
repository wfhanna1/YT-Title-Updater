"""Core package for YouTube Title Updater."""

from .title_manager import TitleManager
from .default_title_generator import DefaultTitleGenerator
from .youtube_client import YouTubeClient
from .auth_manager import AuthManager
from .config_manager import ConfigManager
from .factory import ComponentFactory

__all__ = [
    'TitleManager',
    'DefaultTitleGenerator',
    'YouTubeClient',
    'AuthManager',
    'ConfigManager',
    'ComponentFactory'
]

from typing import Optional

class YouTubeUpdaterCore:
    """Core functionality for YouTube title updating.
    
    This class coordinates the interaction between YouTube API,
    title management, and configuration management.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        title_manager: TitleManager,
        auth_manager: Optional[AuthManager] = None,
        youtube_client: Optional[YouTubeClient] = None
    ):
        """Initialize the YouTube updater core.
        
        Args:
            config_manager: Configuration manager instance
            title_manager: Title manager instance
            auth_manager: Optional authentication manager instance
            youtube_client: Optional YouTube client instance
        """
        self.config = config_manager
        self.title_manager = title_manager
        self.auth_manager = auth_manager
        self.youtube_client = youtube_client
        
        # Initialize state
        self.current_title = "Not Live"
        self.is_live = False
        self.status = "Initializing"
        self.status_type = "info"
    
    def _set_status(self, message: str, status_type: str = "info") -> None:
        """Set status message and type.
        
        Args:
            message: Status message
            status_type: Type of status (info, success, error, warning)
        """
        valid_types = ("info", "success", "error", "warning")
        if status_type not in valid_types:
            raise ValueError(f"Invalid status type: {status_type}")
        
        self.status = message
        self.status_type = status_type
    
    def check_live_status(self) -> None:
        """Check if the channel is currently live streaming."""
        try:
            if not self.youtube_client:
                self._set_status("YouTube client not initialized", "error")
                return
            
            stream_info = self.youtube_client.get_live_stream_info()
            self.is_live = stream_info["is_live"]
            
            if self.is_live:
                self.current_title = stream_info["title"]
                self._set_status("Channel is live", "success")
            else:
                self.current_title = "Not Live"
                self._set_status("Channel is not live", "info")
                
        except Exception as e:
            self._set_status(f"Error checking live status: {str(e)}", "error")
    
    def update_title(self) -> None:
        """Update the title of the current live stream."""
        try:
            if not self.youtube_client:
                self._set_status("YouTube client not initialized", "error")
                return
            
            # Get live stream info first
            stream_info = self.youtube_client.get_live_stream_info()
            if not stream_info["is_live"]:
                self._set_status("Channel is not live", "warning")
                return
                
            # Get next title and update
            new_title = self.title_manager.get_next_title()
            if not new_title:
                self._set_status("No titles available to update.", "warning")
                return
                
            # Update the title using the video_id from our initial check
            self.youtube_client.update_video_title(stream_info["video_id"], new_title)
            
            # Archive the used title
            self.title_manager.archive_title(new_title)
            
            # Update current title
            self.current_title = new_title
            self._set_status(f"Title updated to: {new_title}", "success")
            
        except Exception as e:
            self._set_status(f"Error updating title: {str(e)}", "error")
    
    def get_next_title(self) -> str:
        """Get the next title in the rotation.
        
        Returns:
            str: Next title to use
        """
        return self.title_manager.get_next_title()
    
    def add_title(self, title: str) -> None:
        """Add a new title to the list.
        
        Args:
            title: Title to add
        """
        try:
            self.title_manager.add_title(title)
            self._set_status(f"Title added: {title}", "success")
        except Exception as e:
            self._set_status(f"Error adding title: {str(e)}", "error")
    
    def open_config_dir(self) -> None:
        """Open the configuration directory in Finder (macOS)."""
        import os
        config_dir = os.path.dirname(self.config.get_client_secrets_path())
        os.system(f'open "{config_dir}"')

    def open_titles_file(self) -> None:
        """Open the titles file in the default editor (macOS)."""
        import os
        file_paths = self.config.get_file_paths()
        titles_file = file_paths.get("titles_file")
        if titles_file:
            os.system(f'open "{titles_file}"')

    @property
    def next_title(self) -> str:
        """Get the next title in the rotation (property for GUI compatibility)."""
        return self.get_next_title() 