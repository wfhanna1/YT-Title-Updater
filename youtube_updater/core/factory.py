from typing import Optional
from .youtube_client import YouTubeClient
from .auth_manager import AuthManager
from .title_manager import TitleManager
from .config_manager import ConfigManager
from .interfaces import IYouTubeClient, IAuthManager, ITitleManager, IConfigManager
from ..utils.logger import Logger
from ..utils.file_operations import FileOperations

class ComponentFactory:
    """Factory for creating application components."""
    
    @staticmethod
    def create_core(config_dir: Optional[str] = None) -> 'YouTubeUpdaterCore':
        """Create a fully configured YouTubeUpdaterCore instance.
        
        Args:
            config_dir: Optional custom config directory path
            
        Returns:
            YouTubeUpdaterCore: Configured core instance
        """
        # Create logger
        logger = Logger()
        
        # Create file operations
        file_ops = FileOperations()
        
        # Create config manager
        config_manager = ConfigManager(config_dir)
        
        # Create title manager
        file_paths = config_manager.get_file_paths()
        title_manager = TitleManager(
            file_paths["titles_file"],
            file_paths["applied_titles_file"],
            file_paths["history_log"]
        )
        
        # Create auth manager and YouTube client if client secrets exist
        auth_manager = None
        youtube_client = None
        
        if config_manager.ensure_client_secrets():
            auth_manager = AuthManager(
                config_manager.get_client_secrets_path(),
                file_paths["token_path"]
            )
            youtube_client = YouTubeClient(auth_manager.get_credentials())
        
        # Create and return core
        from . import YouTubeUpdaterCore
        return YouTubeUpdaterCore(
            config_manager=config_manager,
            title_manager=title_manager,
            auth_manager=auth_manager,
            youtube_client=youtube_client,
            logger=logger
        ) 