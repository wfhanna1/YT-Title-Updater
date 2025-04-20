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
            local_dev_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "client_secrets.json")
            config_path = os.path.join(self.config_dir, "client_secrets.json")
            self._set_status(
                f"Client secrets file not found. Please place it in either:\n"
                f"1. Local development: {local_dev_path}\n"
                f"2. Deployed location: {config_path}",
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
        
        # Try multiple possible locations for client_secrets.json
        possible_paths = [
            # Local development path (when running from root)
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "client_secrets.json"),
            # Local development path (when running from macos-app)
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "client_secrets.json"),
            # Deployed path
            os.path.join(self.config_dir, "client_secrets.json")
        ]
        
        print(f"Looking for client_secrets.json in:")
        for path in possible_paths:
            print(f"- {path} ({'exists' if os.path.exists(path) else 'does not exist'})")
        
        # Try each path in order
        for path in possible_paths:
            if os.path.exists(path):
                self.client_secrets_path = path
                print(f"Using client_secrets.json from: {path}")
                break
        else:
            # If no path was found, use the deployed path
            self.client_secrets_path = possible_paths[-1]
            print(f"No client_secrets.json found, will use: {self.client_secrets_path}")
            
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
        self.next_title = "Live Stream"  # Set default next title
        self.titles: List[str] = ["Live Stream"]  # Initialize with default title
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
            print(f"Attempting to initialize YouTube API with client_secrets.json from: {self.client_secrets_path}")
            
            if not os.path.exists(self.client_secrets_path):
                self._set_status(
                    f"Client secrets file not found at: {self.client_secrets_path}\n"
                    f"Please ensure the file exists in one of these locations:\n"
                    f"1. Project root directory\n"
                    f"2. {os.path.join(self.config_dir, 'client_secrets.json')}",
                    "error"
                )
                return
            
            print("Loading credentials...")
            creds = self._load_credentials()
            if not creds or not creds.valid:
                print("No valid credentials found, attempting to authenticate...")
                creds = self._refresh_or_authenticate(creds)
                if not creds:
                    self._set_status("Failed to authenticate with YouTube API", "error")
                    return
            else:
                print("Using existing valid credentials")
            
            print("Building YouTube API client...")
            self.youtube = build("youtube", "v3", credentials=creds)
            
            print("Fetching channel information...")
            # Get the channel ID and current live stream title
            request = self.youtube.channels().list(
                part="id",
                mine=True
            )
            response = request.execute()
            
            if response["items"]:
                self.channel_id = response["items"][0]["id"]
                print(f"Found channel ID: {self.channel_id}")
                
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
                    self._set_status("YouTube API initialized successfully", "success")
                else:
                    self.is_live = False
                    self.current_title = "Not Live"
                    self._set_status("YouTube API initialized (not streaming)", "info")
            else:
                self._set_status("Could not retrieve channel information", "error")
                
        except Exception as e:
            print(f"Error during YouTube API initialization: {str(e)}")
            self._set_status(f"Error initializing YouTube API: {str(e)}", "error")
    
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
        try:
            # Check if file exists and is empty
            if not os.path.exists(self.titles_file) or os.path.getsize(self.titles_file) == 0:
                self.titles = ["Live Stream"]
                self.next_title = "Live Stream"
                with open(self.titles_file, "w") as f:
                    f.write("Live Stream\n")
                return

            with open(self.titles_file, "r") as f:
                content = f.read().strip()
                if not content:
                    self.titles = ["Live Stream"]
                    self.next_title = "Live Stream"
                    with open(self.titles_file, "w") as f:
                        f.write("Live Stream\n")
                    return

                self.titles = [line.strip() for line in content.split('\n') if line.strip()]
                if not self.titles:
                    self.titles = ["Live Stream"]
                    self.next_title = "Live Stream"
                    with open(self.titles_file, "w") as f:
                        f.write("Live Stream\n")
                else:
                    self.next_title = self.titles[0]
                    if self.next_title == "No titles available":
                        self.next_title = "Live Stream"
                        self.titles = ["Live Stream"]
                        with open(self.titles_file, "w") as f:
                            f.write("Live Stream\n")
        except Exception:
            self.titles = ["Live Stream"]
            self.next_title = "Live Stream"
            with open(self.titles_file, "w") as f:
                f.write("Live Stream\n")
    
    def _create_default_titles_file(self) -> None:
        """Create titles file with default title."""
        self.titles = ["Live Stream"]
        self.next_title = "Live Stream"
        with open(self.titles_file, "w") as f:
            f.write("Live Stream\n")
    
    def _archive_title(self, title: str) -> None:
        """Archive a title that has been successfully applied to the stream.
        
        Args:
            title: The title to archive
        """
        try:
            # Remove the title from titles.txt if it exists
            if os.path.exists(self.titles_file):
                with open(self.titles_file, "r") as f:
                    titles = [line.strip() for line in f if line.strip()]
                
                if title in titles:
                    titles.remove(title)
                    
                    with open(self.titles_file, "w") as f:
                        f.write("\n".join(titles) + "\n")
            
            # Add the title to applied-titles.txt with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.applied_titles_file, "a") as f:
                f.write(f"{timestamp} - {title}\n")
            
            # Log to history
            with open(self.history_log, "a") as f:
                f.write(f"{timestamp} - Title updated: {title}\n")
            
            self._set_status(f"Title archived: {title}", "success")
            
        except Exception as e:
            self._set_status(f"Error archiving title: {str(e)}", "error")
            raise
    
    def check_live_status(self) -> None:
        """Check if the channel is currently live streaming."""
        try:
            if not self.youtube or not self.channel_id:
                self._set_status("YouTube API not initialized", "error")
                return
            
            # Only make one API call that includes both the live status and title
            request = self.youtube.search().list(
                part="snippet",
                channelId=self.channel_id,
                eventType="live",
                type="video",
                maxResults=1  # Only need one result
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
            print(f"Error checking live status: {str(e)}")
            self._set_status(f"Error checking live status: {str(e)}", "error")
    
    def _rotate_titles(self) -> None:
        """Rotate to the next title in the list."""
        if not self.titles:
            self.titles = ["Live Stream"]
            self.next_title = "Live Stream"
            with open(self.titles_file, "w") as f:
                f.write("Live Stream\n")
            return None
            
        # Store the current title before rotation
        current = self.titles[0]
        # Rotate the list
        self.titles.append(self.titles.pop(0))
        # Update next_title to the new first title
        self.next_title = self.titles[0]
        if self.next_title == "No titles available":
            self.next_title = "Live Stream"
            self.titles = ["Live Stream"]
            with open(self.titles_file, "w") as f:
                f.write("Live Stream\n")
        return current
    
    def update_title(self) -> None:
        """Update the current live stream title."""
        if not self.youtube:
            self._set_status("YouTube client not initialized", "error")
            return
        
        if not self.is_live:
            self._set_status("No live stream found", "error")
            return
        
        # Check if titles file is empty
        if not os.path.exists(self.titles_file) or os.path.getsize(self.titles_file) == 0:
            self.next_title = "Live Stream"
            self.titles = ["Live Stream"]
            with open(self.titles_file, "w") as f:
                f.write("Live Stream\n")
            self._set_status("Titles file empty, using default: Live Stream", "warning")
        elif not self.next_title or not self.titles or self.next_title == "No titles available":
            self.next_title = "Live Stream"
            self.titles = ["Live Stream"]
            with open(self.titles_file, "w") as f:
                f.write("Live Stream\n")
            self._set_status("No title available, using default: Live Stream", "warning")

        try:
            # Get the current live stream
            request = self.youtube.search().list(
                part="snippet",
                channelId=self.channel_id,
                eventType="live",
                type="video"
            )
            response = request.execute()
            
            if not response.get("items"):
                self._set_status("No live stream found", "error")
                return
            
            video_id = response["items"][0]["id"]["videoId"]
            
            # Get the video details to preserve other fields
            video_request = self.youtube.videos().list(
                part="snippet",
                id=video_id
            )
            video_response = video_request.execute()
            
            if not video_response.get("items"):
                self._set_status("Could not retrieve video details", "error")
                return
            
            # Update the title
            snippet = video_response["items"][0]["snippet"]
            snippet["title"] = self.next_title
            
            update_request = self.youtube.videos().update(
                part="snippet",
                body={
                    "id": video_id,
                    "snippet": snippet
                }
            )
            update_request.execute()
            
            # Log the update
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.history_log, "a") as f:
                f.write(f"{timestamp} - Title updated: {self.next_title}\n")
            
            # Store the title we just used
            used_title = self.next_title
            
            # Update the current title
            self.current_title = self.next_title
            
            # Archive the title and rotate to next
            try:
                # First archive the title
                self._archive_title(used_title)
                # Then rotate to the next title
                self._rotate_titles()
                # Update next_title to the new first title
                if not self.titles:
                    self.titles = ["Live Stream"]
                self.next_title = self.titles[0]
            except Exception as e:
                # Log the error but don't fail the update
                self._set_status(f"Title updated but error archiving: {str(e)}", "warning")
                return
            
            self._set_status(f"Title updated to: {self.next_title}", "success")
            
        except Exception as e:
            self._set_status(f"Error updating title: {str(e)}", "error")
    
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