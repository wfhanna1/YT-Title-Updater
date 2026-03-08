"""Core package for YouTube Title Updater."""

from .title_manager import TitleManager
from .default_title_generator import DefaultTitleGenerator
from .youtube_client import YouTubeClient
from .auth_manager import AuthManager
from .config_manager import ConfigManager
from .status_manager import StatusManager
from .factory import ComponentFactory

__all__ = [
    'TitleManager',
    'DefaultTitleGenerator',
    'YouTubeClient',
    'AuthManager',
    'ConfigManager',
    'StatusManager',
    'ComponentFactory'
]

import os
from typing import Dict, Any, Optional
from .interfaces import IYouTubeClient, IAuthManager, ITitleManager, IConfigManager
from ..utils.logger import Logger
from ..exceptions.custom_exceptions import YouTubeUpdaterError
from ..utils.platform_utils import open_path


class YouTubeUpdaterCore:
    """Core functionality for YouTube title updating.

    This class coordinates the interaction between YouTube API,
    title management, and configuration management.
    """

    def __init__(
        self,
        config_manager: IConfigManager,
        title_manager: ITitleManager,
        auth_manager: Optional[IAuthManager] = None,
        youtube_client: Optional[IYouTubeClient] = None,
        logger: Optional[Logger] = None
    ):
        """Initialize the YouTube updater core.

        Args:
            config_manager: Configuration manager instance
            title_manager: Title manager instance
            auth_manager: Optional authentication manager instance
            youtube_client: Optional YouTube client instance
            logger: Optional logger instance
        """
        self.config = config_manager
        self.title_manager = title_manager
        self.auth_manager = auth_manager
        self.youtube_client = youtube_client
        self.logger = logger

        # Initialize status manager
        self.status_manager = StatusManager(logger)

        # Initialize state
        self.current_title = "Not Live"
        self.is_live = False

    def check_live_status(self) -> Optional[Dict[str, Any]]:
        """Check if the channel is currently live streaming.

        Returns:
            Optional[Dict[str, Any]]: The raw stream_info dict from the YouTube
            client if the client is available, or None otherwise.  Callers may
            pass this dict directly to update_title() to avoid a second API call.

        Raises:
            Exception: On API / network failures so that callers (e.g. the
                CLI polling loop) can distinguish transient errors from a
                simple "not live yet" state.
        """
        if not self.youtube_client:
            self.status_manager.set_status("YouTube client not initialized", "error")
            return None

        # Let API / network errors propagate so the caller can log them and
        # decide whether to retry or abort.
        stream_info = self.youtube_client.get_live_stream_info()
        self.is_live = stream_info["is_live"]

        if self.is_live:
            self.current_title = stream_info["title"]
            self.status_manager.set_status("Channel is live", "success")
        else:
            self.current_title = "Not Live"
            self.status_manager.set_status("Channel is not live", "info")

        return stream_info

    def update_title(self, stream_info: Optional[Dict[str, Any]] = None) -> None:
        """Update the title of the current live stream.

        Args:
            stream_info: Optional pre-fetched stream info dict (keys: is_live,
                title, video_id).  When provided, the internal
                get_live_stream_info() call is skipped, eliminating the redundant
                API round-trip that would otherwise occur when the caller has
                already called check_live_status().

        Raises:
            YouTubeUpdaterError: If the YouTube client is not initialized or
                no titles are available.
            YouTubeAPIError (or subclass): On API / network failures.
        """
        if not self.youtube_client:
            self.status_manager.set_status("YouTube client not initialized", "error")
            raise YouTubeUpdaterError("YouTube client not initialized")

        # Use the provided stream_info to avoid a second API call when the
        # caller has already fetched it via check_live_status().
        if stream_info is None:
            stream_info = self.youtube_client.get_live_stream_info()

        if not stream_info["is_live"]:
            self.status_manager.set_status("Channel is not live", "warning")
            return

        # Get next title and update
        new_title = self.title_manager.get_next_title()
        if not new_title:
            self.status_manager.set_status("No titles available to update.", "warning")
            raise YouTubeUpdaterError("No titles available to update.")

        # Update the title using the video_id from the stream info
        self.youtube_client.update_video_title(stream_info["video_id"], new_title)

        # Archive the used title
        self.title_manager.archive_title(new_title)

        # Update current title
        self.current_title = new_title
        self.status_manager.set_status(f"Title updated to: {new_title}", "success")

    def get_next_title(self) -> str:
        """Get the next title in the rotation (rotates the file).

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
            self.status_manager.set_status(f"Title added: {title}", "success")
        except Exception as e:
            self.status_manager.set_status(f"Error adding title: {str(e)}", "error")

    @property
    def status(self) -> str:
        """Get the current status message."""
        return self.status_manager.status

    @property
    def status_type(self) -> str:
        """Get the current status type."""
        return self.status_manager.status_type

    def open_config_dir(self) -> None:
        """Open the configuration directory using the cross-platform open_path helper."""
        config_dir = os.path.dirname(self.config.get_client_secrets_path())
        open_path(config_dir)

    def open_titles_file(self) -> None:
        """Open the titles file using the cross-platform open_path helper."""
        file_paths = self.config.get_file_paths()
        titles_file = file_paths.get("titles_file")
        if titles_file:
            open_path(titles_file)

    @property
    def next_title(self) -> str:
        """Get the next title without side effects (does not rotate the file).

        Uses peek_next_title() so that merely reading the property does not
        consume/rotate a title from the file.
        """
        result = self.title_manager.peek_next_title()
        if result is None:
            return "No titles available"
        return result
