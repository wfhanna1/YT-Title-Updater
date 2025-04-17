import os
import time
import rumps
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import urllib3

# Suppress the OpenSSL warning
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

class YouTubeTitleUpdater(rumps.App):
    def __init__(self):
        super(YouTubeTitleUpdater, self).__init__("🎥")
        self.menu = ["Open Titles Folder", None, "Current Title", "Next Title"]
        self.titles_file = os.path.expanduser("~/Documents/yt_title_updater/titles.txt")
        self.token_path = os.path.expanduser("~/Documents/yt_title_updater/token.pickle")
        self.client_secrets_path = os.path.expanduser("~/Documents/yt_title_updater/client_secrets.json")
        self.youtube = None
        self.current_title = "Not Live"
        self.next_title = "No titles available"
        self.setup_youtube()
        self.load_titles()
        self.update_menu()

    def setup_youtube(self):
        creds = None
        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_path, ["https://www.googleapis.com/auth/youtube"]
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, "wb") as token:
                pickle.dump(creds, token)

        self.youtube = build("youtube", "v3", credentials=creds)

    def load_titles(self):
        if os.path.exists(self.titles_file):
            with open(self.titles_file, "r") as f:
                self.titles = [line.strip() for line in f if line.strip()]
        else:
            self.titles = ["Live Stream"]

    def update_menu(self):
        self.menu["Current Title"].title = f"Current Title: {self.current_title}"
        self.menu["Next Title"].title = f"Next Title: {self.next_title}"

    @rumps.clicked("Open Titles Folder")
    def open_titles_folder(self, _):
        os.system(f"open {os.path.dirname(self.titles_file)}")

    @rumps.timer(60)  # Check every minute
    def check_live_status(self, _):
        try:
            # First get the live broadcast
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
                    # Update title if it's different
                    if self.current_title != self.next_title:
                        broadcast["snippet"]["title"] = self.next_title
                        self.youtube.liveBroadcasts().update(
                            part="snippet",
                            body=broadcast
                        ).execute()
                        # Remove used title
                        self.titles.pop(0)
                        self.load_titles()  # Reload titles
                else:
                    self.next_title = "No titles available"
            else:
                self.current_title = "Not Live"
                self.next_title = "No titles available"
            
            self.update_menu()
        except Exception as e:
            print(f"Error: {e}")
            self.current_title = "Error"
            self.next_title = "Error"

if __name__ == "__main__":
    YouTubeTitleUpdater().run()
