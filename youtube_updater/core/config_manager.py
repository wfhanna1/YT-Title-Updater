import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

class ConfigManager:
    """Manages application configuration and file paths."""
    
    DEFAULT_CONFIG_DIR = "yt_title_updater"
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Optional custom config directory path
        """
        self.config_dir = self._setup_config_dir(config_dir)
        self._setup_file_paths()
    
    def _get_platform_config_dir(self) -> str:
        """Get the platform-specific configuration directory.
        
        Returns:
            str: Path to the configuration directory
        """
        if sys.platform == "win32":
            return os.path.join(os.getenv("APPDATA"), self.DEFAULT_CONFIG_DIR)
        elif sys.platform == "darwin":
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", self.DEFAULT_CONFIG_DIR)
        else:
            return os.path.join(os.path.expanduser("~"), ".config", self.DEFAULT_CONFIG_DIR)
    
    def _setup_config_dir(self, config_dir: Optional[str]) -> str:
        """Set up the configuration directory.
        
        Args:
            config_dir: Optional custom config directory path
            
        Returns:
            str: Path to the configuration directory
        """
        if config_dir is None:
            # First check current directory
            current_dir = os.getcwd()
            if os.path.exists(os.path.join(current_dir, "client_secrets.json")):
                return current_dir
            # Fall back to platform-specific directory
            config_dir = self._get_platform_config_dir()
        os.makedirs(config_dir, exist_ok=True)
        return config_dir
    
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