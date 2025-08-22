import os
import sys
from pathlib import Path
from typing import Dict, Optional

class ConfigManager:
    """Manages application configuration and file paths."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the config manager.
        
        Args:
            config_dir: Optional custom config directory path
        """
        # Use provided config_dir or default to platform-specific location
        if config_dir is None:
            if sys.platform == "win32":
                config_dir = os.path.join(os.getenv("APPDATA"), "yt_title_updater")
            elif sys.platform == "darwin":
                config_dir = os.path.join(os.path.expanduser("~"), "Documents", "yt_title_updater")
            else:
                config_dir = os.path.join(os.path.expanduser("~"), ".config", "yt_title_updater")
        
        self.config_dir = Path(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Set up file paths
        self._setup_file_paths()
    
    def _setup_file_paths(self) -> None:
        """Set up all file paths used by the application."""
        self.titles_file = os.path.join(self.config_dir, "titles.txt")
        self.applied_titles_file = os.path.join(self.config_dir, "applied-titles.txt")
        self.token_path = os.path.join(self.config_dir, "token.pickle")
        self.client_secrets_path = os.path.join(self.config_dir, "client_secrets.json")
        self.history_log = os.path.join(self.config_dir, "history.log")
        
        # Create empty files if they don't exist
        for file_path in [self.titles_file, self.applied_titles_file, self.history_log]:
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write("")
    
    def get_file_paths(self) -> Dict[str, str]:
        """Get all file paths used by the application.
        
        Returns:
            Dict[str, str]: Dictionary of file paths
        """
        return {
            "titles_file": self.titles_file,
            "applied_titles_file": self.applied_titles_file,
            "token_path": self.token_path,
            "client_secrets_path": self.client_secrets_path,
            "history_log": self.history_log
        }
    
    def ensure_client_secrets(self) -> bool:
        """Check if client secrets file exists.
        
        Returns:
            bool: True if client secrets file exists, False otherwise
        """
        return os.path.exists(self.client_secrets_path)
    
    def get_client_secrets_path(self) -> str:
        """Get the path to the client secrets file.
        
        Returns:
            str: Path to client secrets file
        """
        return self.client_secrets_path 