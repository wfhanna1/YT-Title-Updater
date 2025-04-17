import os
import sys
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import urllib3
import shutil

# Suppress the OpenSSL warning
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

class YouTubeUpdaterCore:
    """Core functionality for YouTube title updating."""
    
    def __init__(self, config_dir=None):
        """
        Initialize the YouTube updater core.
        
        Args:
            config_dir (str, optional): Directory for configuration files.
                                      Defaults to ~/Documents/yt_title_updater/
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/Documents/yt_title_updater")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Set up paths
        self.config_dir = config_dir
        self.titles_file = os.path.join(config_dir, "titles.txt")
        self.token_path = os.path.join(config_dir, "token.pickle")
        self.client_secrets_path = os.path.join(config_dir, "client_secrets.json")
        
        # Initialize state
        self.youtube = None
        self.current_title = "Not Live"
        self.next_title = "No titles available"
        self.titles = []
        self._status = "Initializing"
        self._status_type = "info"  # Can be: info, success, error, warning
        
        # Check for client secrets file
        if not os.path.exists(self.client_secrets_path):
            self._set_status("Client secrets file not found. Please copy it to: " + self.client_secrets_path, "error")
            return
        
        # Initialize YouTube API
        self.setup_youtube()
        self.load_titles()
    
    @property
    def status(self):
        """Get the current status message."""
        return self._status
    
    @property
    def status_type(self):
        """Get the current status type."""
        return self._status_type
    
    def _set_status(self, message, status_type="info"):
        """
        Set status message and type.
        
        Args:
            message (str): Status message
            status_type (str): One of: info, success, error, warning
        """
        self._status = message
        self._status_type = status_type
        print(f"Status: {message} ({status_type})")  # Add logging for debugging
    
    def setup_youtube(self):
        """Set up YouTube API client."""
        try:
            if not os.path.exists(self.client_secrets_path):
                self._set_status("Client secrets file not found. Please copy it to: " + self.client_secrets_path, "error")
                return
            
            creds = None
            if os.path.exists(self.token_path):
                with open(self.token_path, "rb") as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        self._set_status(f"Error refreshing credentials: {str(e)}", "error")
                        return
                else:
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.client_secrets_path,
                            ["https://www.googleapis.com/auth/youtube"]
                        )
                        creds = flow.run_local_server(port=0)
                    except Exception as e:
                        self._set_status(f"Error during authentication: {str(e)}", "error")
                        return
                
                with open(self.token_path, "wb") as token:
                    pickle.dump(creds, token)

            self.youtube = build("youtube", "v3", credentials=creds)
            self._set_status("Connected to YouTube API", "success")
        
        except Exception as e:
            self._set_status(f"Error connecting to YouTube API: {str(e)}", "error")
    
    def load_titles(self):
        """Load titles from the titles file."""
        try:
            if os.path.exists(self.titles_file):
                with open(self.titles_file, "r") as f:
                    self.titles = [line.strip() for line in f if line.strip()]
                if self.titles:
                    self.next_title = self.titles[0]
            else:
                self.titles = ["Live Stream"]
                self.next_title = self.titles[0]
                # Create the file with default title
                with open(self.titles_file, "w") as f:
                    f.write("Live Stream\n")
            
            self._set_status("Titles loaded successfully", "success")
        
        except Exception as e:
            self._set_status(f"Error loading titles: {str(e)}", "error")
    
    def check_live_status(self):
        """
        Check live broadcast status and update title if needed.
        
        Returns:
            tuple: (current_title, next_title, status_message, status_type)
        """
        try:
            if not self.youtube:
                self._set_status("YouTube API not initialized. Please check client secrets file.", "error")
                return self.current_title, self.next_title, self.status, self.status_type
            
            request = self.youtube.liveBroadcasts().list(
                part="snippet",
                broadcastStatus="active",
                broadcastType="all"
            )
            response = request.execute()
            
            if response["items"]:
                broadcast = response["items"][0]
                self.current_title = broadcast["snippet"]["title"]
                
                if self.titles:
                    self.next_title = self.titles[0]
                    if self.current_title != self.next_title:
                        broadcast["snippet"]["title"] = self.next_title
                        self.youtube.liveBroadcasts().update(
                            part="snippet",
                            body=broadcast
                        ).execute()
                        self.titles.pop(0)
                        self.load_titles()
                else:
                    self.next_title = "No titles available"
            else:
                self.current_title = "Not Live"
                self.next_title = "No titles available"
            
            self._set_status("Status updated successfully", "success")
        
        except Exception as e:
            self._set_status(f"Error checking live status: {str(e)}", "error")
        
        return self.current_title, self.next_title, self.status, self.status_type
    
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