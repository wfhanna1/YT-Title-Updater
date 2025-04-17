import os
import time
import pickle
import tkinter as tk
from tkinter import ttk, messagebox
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import urllib3

# Suppress the OpenSSL warning
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

class YouTubeTitleUpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Title Updater")
        self.root.geometry("400x300")
        
        # Set up paths
        self.titles_file = os.path.expanduser("~/Documents/yt_title_updater/titles.txt")
        self.token_path = os.path.expanduser("~/Documents/yt_title_updater/token.pickle")
        self.client_secrets_path = os.path.expanduser("~/Documents/yt_title_updater/client_secrets.json")
        
        # Initialize variables
        self.youtube = None
        self.current_title = "Not Live"
        self.next_title = "No titles available"
        self.titles = []
        
        # Create menu bar
        self.create_menu()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create title labels
        self.create_title_labels()
        
        # Set up YouTube API
        self.setup_youtube()
        self.load_titles()
        self.update_display()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Titles Folder", command=self.open_titles_folder)
        file_menu.add_command(label="Check Now", command=self.check_live_status)
    
    def create_title_labels(self):
        # Current Title
        ttk.Label(self.main_frame, text="Current Title:", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.current_title_label = ttk.Label(self.main_frame, text=self.current_title, font=('Arial', 12))
        self.current_title_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Next Title
        ttk.Label(self.main_frame, text="Next Title:", font=('Arial', 12, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.next_title_label = ttk.Label(self.main_frame, text=self.next_title, font=('Arial', 12))
        self.next_title_label.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        # Status
        self.status_label = ttk.Label(self.main_frame, text="", font=('Arial', 10))
        self.status_label.grid(row=4, column=0, sticky=tk.W, pady=5)
        
        # Check Now Button
        self.check_button = ttk.Button(self.main_frame, text="Check Now", command=self.check_live_status)
        self.check_button.grid(row=5, column=0, sticky=tk.W, pady=10)
        
        # Open Titles File Button
        self.open_titles_button = ttk.Button(self.main_frame, text="Open Titles File", command=self.open_titles_file)
        self.open_titles_button.grid(row=5, column=1, sticky=tk.W, pady=10)
    
    def setup_youtube(self):
        try:
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
            self.status_label.config(text="Connected to YouTube API", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Error connecting to YouTube API: {str(e)}", foreground="red")
    
    def load_titles(self):
        try:
            if os.path.exists(self.titles_file):
                with open(self.titles_file, "r") as f:
                    self.titles = [line.strip() for line in f if line.strip()]
            else:
                self.titles = ["Live Stream"]
            self.status_label.config(text="Titles loaded successfully", foreground="green")
        except Exception as e:
            self.status_label.config(text=f"Error loading titles: {str(e)}", foreground="red")
    
    def update_display(self):
        self.current_title_label.config(text=self.current_title)
        self.next_title_label.config(text=self.next_title)
    
    def open_titles_folder(self):
        try:
            os.system(f"open {os.path.dirname(self.titles_file)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open titles folder: {str(e)}")
    
    def open_titles_file(self):
        try:
            if os.path.exists(self.titles_file):
                os.system(f"open {self.titles_file}")
            else:
                messagebox.showwarning("Warning", "titles.txt file does not exist yet.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open titles file: {str(e)}")
    
    def check_live_status(self):
        try:
            if self.youtube:
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
                
                self.update_display()
                self.status_label.config(text="Last checked: " + time.strftime("%H:%M:%S"), foreground="black")
        except Exception as e:
            self.status_label.config(text=f"Error checking live status: {str(e)}", foreground="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeTitleUpdaterGUI(root)
    root.mainloop() 