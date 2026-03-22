import json
import os
from pathlib import Path
from typing import Dict, Optional
import platformdirs
from ..exceptions.custom_exceptions import ConfigError
from ..utils.file_operations import FileOperations

class ConfigManager:
    """Manages application configuration and file paths."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the config manager.
        
        Args:
            config_dir: Optional custom config directory path
        """
        # Use provided config_dir or default to platformdirs user data directory
        if config_dir:
            self.config_dir = Path(config_dir).resolve()
        else:
            self.config_dir = Path(platformdirs.user_data_dir("YTTitleUpdater", "YTTitleUpdater"))
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Initialize file operations
        self.file_ops = FileOperations()
        
        # Set up file paths
        self._setup_file_paths()
    
    def _setup_file_paths(self) -> None:
        """Set up all file paths used by the application."""
        self.titles_file = os.path.join(self.config_dir, "titles.txt")
        self.applied_titles_file = os.path.join(self.config_dir, "applied-titles.txt")
        self.token_path = os.path.join(self.config_dir, "token.json")
        self.client_secrets_path = os.path.join(self.config_dir, "client_secrets.json")
        self.history_log = os.path.join(self.config_dir, "history.log")
        self.restream_token_path = os.path.join(self.config_dir, "restream_token.json")
        self.email_config_path = os.path.join(self.config_dir, "email_config.json")

        # Create empty files if they don't exist
        for file_path in [self.titles_file, self.applied_titles_file, self.history_log]:
            self.file_ops.ensure_file_exists(file_path)
    
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
            "history_log": self.history_log,
            "restream_token_path": self.restream_token_path,
            "email_config_path": self.email_config_path,
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

    def get_restream_token_path(self) -> str:
        """Get the path to the Restream token file.

        Returns:
            str: Path to restream_token.json
        """
        return self.restream_token_path

    def ensure_restream_token(self) -> bool:
        """Check if the Restream token file exists.

        Returns:
            bool: True if restream_token.json exists
        """
        return os.path.exists(self.restream_token_path)

    def save_email_config(self, config: Dict[str, str]) -> None:
        """Save email notification configuration.

        Args:
            config: Dict with connection_string, sender, recipient
        """
        if os.path.basename(self.email_config_path) != "email_config.json":
            raise ConfigError(
                f"Refusing to write: unexpected email config path '{self.email_config_path}'"
            )
        fd = os.open(self.email_config_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(config, f, indent=2)

    def get_email_config(self) -> Optional[Dict[str, str]]:
        """Load email notification configuration.

        Returns:
            Dict with email config, or None if not configured
        """
        if not os.path.exists(self.email_config_path):
            return None
        try:
            with open(self.email_config_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"email_config.json is corrupt: {e}") from e