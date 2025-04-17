import os
import sys
import pickle
from typing import Optional, Tuple, List
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import urllib3
import shutil
from datetime import datetime

# Suppress the OpenSSL warning
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

class YouTubeUpdaterCore:
    """Core functionality for YouTube title updating.
    
    This class handles the core functionality of the YouTube Title Updater,
    including YouTube API interaction, title management, and file operations.
    """
    
    # Constants
    DEFAULT_CONFIG_DIR = "~/Documents/yt_title_updater"
    DEFAULT_TITLE = "Live Stream"
    STATUS_TYPES = ("info", "success", "error", "warning")
    
    def __init__(self, config_dir: Optional[str] = None) -> None:
        """Initialize the YouTube updater core.
        
        Args:
            config_dir: Directory for configuration files.
                       Defaults to ~/Documents/yt_title_updater/
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
    
    def _setup_config_dir(self, config_dir: Optional[str]) -> str:
        """Set up the configuration directory.
        
        Args:
            config_dir: Optional custom config directory path
            
        Returns:
            str: Path to the configuration directory
        """
        if config_dir is None:
            config_dir = os.path.expanduser(self.DEFAULT_CONFIG_DIR)
        os.makedirs(config_dir, exist_ok=True)
        return config_dir
    
    def _setup_file_paths(self) -> None:
        """Set up all file paths used by the application."""
        self.titles_file = os.path.join(self.config_dir, "titles.txt")
        self.applied_titles_file = os.path.join(self.config_dir, "applied-titles.txt")
        self.token_path = os.path.join(self.config_dir, "token.pickle")
        self.client_secrets_path = os.path.join(self.config_dir, "client_secrets.json")
        self.history_log = os.path.join(self.config_dir, "history.log")
        
        # Ensure applied-titles.txt exists
        if not os.path.exists(self.applied_titles_file):
            with open(self.applied_titles_file, "w") as f:
                f.write("")
        
        # Ensure history.log exists
        if not os.path.exists(self.history_log):
            with open(self.history_log, "w") as f:
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
    def status(self):
        """Get the current status message."""
        return self._status
    
    @property
    def status_type(self):
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
        print(f"Status: {message} ({status_type})")  # Add logging for debugging
    
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
        """
        Archive a title that has been successfully applied to the stream.
        
        Args:
            title (str): The title to archive
        """
        try:
            # Add the title to applied-titles.txt with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Remove the title from titles.txt
            if os.path.exists(self.titles_file):
                with open(self.titles_file, "r") as f:
                    titles = [line.strip() for line in f if line.strip()]
                
                # Check if title exists
                if title not in titles:
                    error_msg = f"Title not found: {title}"
                    # Log error to history
                    with open(self.history_log, "a") as f:
                        f.write(f"{timestamp} - Error: {error_msg}\n")
                    raise ValueError(error_msg)
                
                # Add to history log
                with open(self.history_log, "a") as f:
                    f.write(f"{timestamp} - Title updated: {title}\n")
                
                # Add to applied-titles.txt
                with open(self.applied_titles_file, "a") as f:
                    f.write(f"{timestamp} - {title}\n")
                
                # Remove the applied title
                titles.remove(title)
                
                # Write back the remaining titles
                with open(self.titles_file, "w") as f:
                    for remaining_title in titles:
                        f.write(f"{remaining_title}\n")
                
                self._set_status(f"Title archived: {title}", "success")
            else:
                error_msg = "Titles file not found"
                # Log error to history
                with open(self.history_log, "a") as f:
                    f.write(f"{timestamp} - Error: {error_msg}\n")
                raise FileNotFoundError(error_msg)
                
        except Exception as e:
            self._set_status(f"Error archiving title: {str(e)}", "error")
            # Log error to history if not already logged
            if not str(e).startswith("Title not found") and not str(e).startswith("Titles file not found"):
                with open(self.history_log, "a") as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error: {str(e)}\n")
    
    def check_live_status(self) -> None:
        """Check if the channel is currently live streaming."""
        if not self.youtube:
            self._set_status("YouTube client not initialized", "error")
            return
        
        try:
            request = self.youtube.search().list(
                part="snippet",
                channelId=self.channel_id,
                eventType="live",
                type="video"
            )
            response = request.execute()
            
            if response["items"]:
                self.is_live = True
                self._set_status("Channel is live", "success")
            else:
                self.is_live = False
                self.current_title = "Not Live"
                self._set_status("Channel is not live", "info")
        
        except Exception as e:
            self._set_status(f"Error checking live status: {str(e)}", "error")
    
    def update_title(self) -> None:
        """Update the title of the current live stream."""
        if not self.youtube:
            self._set_status("YouTube client not initialized", "error")
            return
        
        if not self.is_live:
            self._set_status("Channel is not live", "warning")
            return
        
        try:
            # Get the current live broadcast
            request = self.youtube.search().list(
                part="snippet",
                channelId=self.channel_id,
                eventType="live",
                type="video"
            )
            response = request.execute()
            
            if not response["items"]:
                self._set_status("No live broadcast found", "error")
                return
            
            video_id = response["items"][0]["id"]["videoId"]
            
            # Only update if the title is different from what we want to set
            if self.current_title != self.next_title:
                # Update the video title
                request = self.youtube.videos().update(
                    part="snippet",
                    body={
                        "id": video_id,
                        "snippet": {
                            "title": self.next_title,
                            "categoryId": "22"  # Gaming category
                        }
                    }
                )
                request.execute()
                
                # Log the update
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.history_log, "a") as f:
                    f.write(f"{timestamp} - Changed title from \"{self.current_title}\" to \"{self.next_title}\"\n")
                
                # Archive the old title and move to next
                self._archive_title(self.next_title)
                
                # Update the current title to what we just set
                self.current_title = self.next_title
                
                # Rotate to the next title
                self._rotate_titles()
                
                self._set_status(f"Title updated to: {self.next_title}", "success")
            else:
                self._set_status("Title is already up to date", "info")
        
        except Exception as e:
            self._set_status(f"Error updating title: {str(e)}", "error")
            # Log error to history
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.history_log, "a") as f:
                f.write(f"{timestamp} - Error updating title: {str(e)}\n")
    
    def _rotate_titles(self) -> None:
        """Rotate to the next title in the list."""
        if not self.titles:
            return
            
        current_index = self.titles.index(self.next_title)
        next_index = (current_index + 1) % len(self.titles)
        self.next_title = self.titles[next_index]
    
    def open_config_dir(self):
        """Open the configuration directory in the system file explorer."""
        try:
            if sys.platform == "darwin":  # macOS
                os.system(f"open '{self.config_dir}'")
            elif sys.platform == "win32":  # Windows
                os.system(f'explorer "{self.config_dir}"')
            else:  # Linux and others
                os.system(f"xdg-open '{self.config_dir}'")
            self._set_status("Opened configuration directory", "success")
        except Exception as e:
            self._set_status(f"Error opening configuration directory: {str(e)}", "error")
    
    def open_titles_file(self):
        """Open the titles file in the default text editor."""
        try:
            if not os.path.exists(self.titles_file):
                with open(self.titles_file, 'w') as f:
                    f.write("Live Stream\n")
            
            if sys.platform == "darwin":  # macOS
                os.system(f"open '{self.titles_file}'")
            elif sys.platform == "win32":  # Windows
                os.system(f'notepad "{self.titles_file}"')
            else:  # Linux and others
                os.system(f"xdg-open '{self.titles_file}'")
            self._set_status("Opened titles file", "success")
        except Exception as e:
            self._set_status(f"Error opening titles file: {str(e)}", "error") 