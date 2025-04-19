import os
import sys
import pickle
from typing import Optional, Tuple, List, Dict
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import urllib3
from datetime import datetime
from pathlib import Path

# Suppress the OpenSSL warning
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

class YouTubeUpdaterCore:
    """Core functionality for YouTube title updating.
    
    This class handles the core functionality of the YouTube Title Updater,
    including YouTube API interaction, title management, and file operations.
    """
    
    # Constants
    DEFAULT_CONFIG_DIR = "yt_title_updater"
    DEFAULT_TITLE = "Live Stream"
    STATUS_TYPES = ("info", "success", "error", "warning")
    
    def __init__(self, config_dir: Optional[str] = None) -> None:
        """Initialize the YouTube updater core.
        
        Args:
            config_dir: Directory for configuration files.
                       Defaults to platform-specific config directory
        """
        self.config_dir = self._setup_config_dir(config_dir)
        self._setup_file_paths()
        self._initialize_state()
        
        # Check for client secrets file
        if not os.path.exists(self.client_secrets_path):
            self._set_status(
                f"Client secrets file not found. Please copy it to: {self.client_secrets_path}",
                "error"
            )
            return
        
        # Initialize YouTube API and load titles
        self.setup_youtube()
        self.load_titles()
    
    def _get_platform_config_dir(self) -> str:
        """Get the platform-specific configuration directory.
        
        Returns:
            str: Path to the configuration directory
        """
        if sys.platform == "win32":
            return os.path.join(os.getenv("APPDATA"), self.DEFAULT_CONFIG_DIR)
        elif sys.platform == "darwin":
            return os.path.join(os.path.expanduser("~"), "Documents", self.DEFAULT_CONFIG_DIR)
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
        
        # Ensure required files exist
        for file_path in [self.applied_titles_file, self.history_log]:
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write("")
    
    def _initialize_state(self) -> None:
        """Initialize the application state."""
        self.youtube = None
        self.current_title = "Not Live"
        self.next_title = "No titles available"
        self.titles: List[str] = []
        self._status = "Initializing"
        self._status_type = "info"
        self.is_live = False
        self.channel_id = None
    
    @property
    def status(self) -> str:
        """Get the current status message."""
        return self._status
    
    @property
    def status_type(self) -> str:
        """Get the current status type."""
        return self._status_type
    
    def _set_status(self, message: str, status_type: str = "info") -> None:
        """Set status message and type.
        
        Args:
            message: Status message
            status_type: One of: info, success, error, warning
        """
        if status_type not in self.STATUS_TYPES:
            raise ValueError(f"Invalid status type. Must be one of: {self.STATUS_TYPES}")
            
        self._status = message
        self._status_type = status_type
    
    def setup_youtube(self) -> None:
        """Set up YouTube API and get initial state."""
        try:
            if not os.path.exists(self.client_secrets_path):
                self._set_status(
                    f"Client secrets file not found. Please copy it to: {self.client_secrets_path}",
                    "error"
                )
                return
            
            creds = self._load_credentials()
            if not creds or not creds.valid:
                creds = self._refresh_or_authenticate(creds)
                if not creds:
                    return
            
            self.youtube = build("youtube", "v3", credentials=creds)
            
            # Get the channel ID and current live stream title
            request = self.youtube.channels().list(
                part="id",
                mine=True
            )
            response = request.execute()
            
            if response["items"]:
                self.channel_id = response["items"][0]["id"]
                # Get current live stream title
                live_request = self.youtube.search().list(
                    part="snippet",
                    channelId=self.channel_id,
                    eventType="live",
                    type="video"
                )
                live_response = live_request.execute()
                if live_response.get("items"):
                    self.is_live = True
                    self.current_title = live_response["items"][0]["snippet"]["title"]
                    self._set_status("Connected to YouTube API", "success")
                else:
                    self.is_live = False
                    self.current_title = "Not Live"
                    self._set_status("Connected to YouTube API (not streaming)", "info")
            else:
                self._set_status("Could not retrieve channel ID", "error")
        
        except Exception as e:
            self._set_status(f"Error connecting to YouTube API: {str(e)}", "error")
    
    def _load_credentials(self) -> Optional[Credentials]:
        """Load credentials from token file if it exists.
        
        Returns:
            Optional[Credentials]: Loaded credentials or None if file doesn't exist
        """
        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as token:
                return pickle.load(token)
        return None
    
    def _refresh_or_authenticate(self, creds: Optional[Credentials]) -> Optional[Credentials]:
        """Refresh existing credentials or authenticate new ones.
        
        Args:
            creds: Existing credentials to refresh, or None for new authentication
            
        Returns:
            Optional[Credentials]: Refreshed or new credentials, or None if failed
        """
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_path,
                    ["https://www.googleapis.com/auth/youtube"]
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials
            with open(self.token_path, "wb") as token:
                pickle.dump(creds, token)
            return creds
            
        except Exception as e:
            self._set_status(f"Error during authentication: {str(e)}", "error")
            return None
    
    def load_titles(self) -> None:
        """Load titles from the titles file."""
        try:
            if os.path.exists(self.titles_file):
                self._load_existing_titles()
            else:
                self._create_default_titles_file()
            
            self._set_status("Titles loaded successfully", "success")
        
        except Exception as e:
            self._set_status(f"Error loading titles: {str(e)}", "error")
    
    def _load_existing_titles(self) -> None:
        """Load titles from existing titles file."""
        with open(self.titles_file, "r") as f:
            self.titles = [line.strip() for line in f if line.strip()]
            if self.titles:
                self.next_title = self.titles[0]
    
    def _create_default_titles_file(self) -> None:
        """Create titles file with default title."""
        self.titles = [self.DEFAULT_TITLE]
        self.next_title = self.titles[0]
        with open(self.titles_file, "w") as f:
            f.write(f"{self.DEFAULT_TITLE}\n")
    
    def _archive_title(self, title: str) -> None:
        """Archive a title that has been successfully applied to the stream.
        
        Args:
            title: The title to archive
        """
        try:
            # Add the title to applied-titles.txt with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Remove the title from titles.txt
            if os.path.exists(self.titles_file):
                with open(self.titles_file, "r") as f:
                    titles = [line.strip() for line in f if line.strip()]
                
                if title in titles:
                    titles.remove(title)
                    
                    with open(self.titles_file, "w") as f:
                        f.write("\n".join(titles) + "\n")
            
            # Add to applied titles
            with open(self.applied_titles_file, "a") as f:
                f.write(f"{timestamp} - {title}\n")
            
            # Log the change
            with open(self.history_log, "a") as f:
                f.write(f"{timestamp} - Title updated: {title}\n")
            
        except Exception as e:
            self._set_status(f"Error archiving title: {str(e)}", "error")
    
    def check_live_status(self) -> None:
        """Check if the channel is currently live streaming."""
        try:
            if not self.youtube or not self.channel_id:
                self._set_status("YouTube API not initialized", "error")
                return
            
            request = self.youtube.search().list(
                part="snippet",
                channelId=self.channel_id,
                eventType="live",
                type="video"
            )
            response = request.execute()
            
            if response.get("items"):
                self.is_live = True
                self.current_title = response["items"][0]["snippet"]["title"]
                self._set_status("Channel is live", "success")
            else:
                self.is_live = False
                self.current_title = "Not Live"
                self._set_status("Channel is not live", "info")
        
        except Exception as e:
            self._set_status(f"Error checking live status: {str(e)}", "error")
    
    def update_title(self) -> None:
        """Update the current live stream title."""
        try:
            if not self.youtube or not self.channel_id:
                self._set_status("YouTube API not initialized", "error")
                return
            
            if not self.is_live:
                self._set_status("Cannot update title: Channel is not live", "warning")
                return
            
            if not self.titles:
                self._set_status("No titles available to update", "warning")
                return
            
            # Get the current live video ID
            request = self.youtube.search().list(
                part="snippet",
                channelId=self.channel_id,
                eventType="live",
                type="video"
            )
            response = request.execute()
            
            if not response.get("items"):
                self._set_status("Could not find live video", "error")
                return
            
            video_id = response["items"][0]["id"]["videoId"]
            
            # Get the video details to get the category ID
            video_request = self.youtube.videos().list(
                part="snippet",
                id=video_id
            )
            video_response = video_request.execute()
            
            if not video_response.get("items"):
                self._set_status("Could not get video details", "error")
                return
                
            current_snippet = video_response["items"][0]["snippet"]
            
            # Update the video title while preserving other snippet fields
            current_snippet["title"] = self.next_title
            
            # Update the video title
            request = self.youtube.videos().update(
                part="snippet",
                body={
                    "id": video_id,
                    "snippet": current_snippet
                }
            )
            request.execute()
            
            # Archive the old title and rotate to next title
            self._archive_title(self.next_title)
            self._rotate_titles()
            
            self._set_status("Title updated successfully", "success")
        
        except Exception as e:
            self._set_status(f"Error updating title: {str(e)}", "error")
    
    def _rotate_titles(self) -> None:
        """Rotate to the next title in the list."""
        if self.titles:
            self.titles.append(self.titles.pop(0))
            self.next_title = self.titles[0]
    
    def open_config_dir(self) -> None:
        """Open the configuration directory in the system's file explorer."""
        try:
            if sys.platform == "win32":
                os.startfile(self.config_dir)
            elif sys.platform == "darwin":
                os.system(f"open '{self.config_dir}'")
            else:
                os.system(f"xdg-open '{self.config_dir}'")
        except Exception as e:
            self._set_status(f"Error opening config directory: {str(e)}", "error")
    
    def open_titles_file(self) -> None:
        """Open the titles file in the system's default text editor."""
        try:
            if sys.platform == "win32":
                os.startfile(self.titles_file)
            elif sys.platform == "darwin":
                os.system(f"open '{self.titles_file}'")
            else:
                os.system(f"xdg-open '{self.titles_file}'")
        except Exception as e:
            self._set_status(f"Error opening titles file: {str(e)}", "error") 