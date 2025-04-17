import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
from .core import YouTubeUpdaterCore

class YouTubeUpdaterGUI:
    """GUI implementation for YouTube Title Updater."""
    
    def __init__(self, root, core=None):
        """
        Initialize the GUI.
        
        Args:
            root: tkinter root window
            core (YouTubeUpdaterCore, optional): Core functionality instance.
                                               If None, creates a new instance.
        """
        self.root = root
        self.root.title("YouTube Title Updater")
        self.root.geometry("600x400")  # Made window larger
        
        # Initialize core functionality
        self.core = core if core is not None else YouTubeUpdaterCore()
        
        # Create GUI elements
        self.create_menu()
        self.create_main_frame()
        self.create_title_labels()
        self.create_buttons()
        
        # Update display immediately
        self.update_display()
    
    def create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Config Folder", command=self.core.open_config_dir)
        file_menu.add_command(label="Open Titles File", command=self.core.open_titles_file)
        file_menu.add_separator()
        file_menu.add_command(label="Check Now", command=self.check_status)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
    
    def create_main_frame(self):
        """Create the main frame for the GUI."""
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
    
    def create_title_labels(self):
        """Create labels for displaying current and next titles."""
        # Current Title
        ttk.Label(self.main_frame, text="Current Title:", 
                 font=('Arial', 12, 'bold')).grid(row=0, column=0, 
                                                sticky=tk.W, pady=5)
        self.current_title_label = ttk.Label(self.main_frame, 
                                           text=self.core.current_title,
                                           font=('Arial', 12),
                                           wraplength=550)  # Added wraplength
        self.current_title_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Next Title
        ttk.Label(self.main_frame, text="Next Title:", 
                 font=('Arial', 12, 'bold')).grid(row=2, column=0, 
                                                sticky=tk.W, pady=5)
        self.next_title_label = ttk.Label(self.main_frame, 
                                        text=self.core.next_title,
                                        font=('Arial', 12),
                                        wraplength=550)  # Added wraplength
        self.next_title_label.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Status
        self.status_label = ttk.Label(self.main_frame, text=self.core.status,
                                    font=('Arial', 10),
                                    wraplength=550)  # Added wraplength
        self.status_label.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
    
    def create_buttons(self):
        """Create action buttons."""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Update Title Button
        self.update_button = ttk.Button(button_frame, text="Update Title",
                                      command=self.update_title)
        self.update_button.pack(side=tk.LEFT, padx=5)
        
        # Open Titles Button
        self.open_titles_button = ttk.Button(button_frame, text="Open Titles File",
                                           command=self.core.open_titles_file)
        self.open_titles_button.pack(side=tk.LEFT, padx=5)
    
    def update_display(self):
        """Update the display with current information."""
        self.current_title_label.config(text=self.core.current_title)
        self.next_title_label.config(text=self.core.next_title)
        
        # Update status label with color based on status type
        colors = {
            "success": "green",
            "error": "red",
            "warning": "orange",
            "info": "black"
        }
        status_text = self.core.status
        if self.core.status_type != "error":
            status_text += f" (Last updated: {time.strftime('%H:%M:%S')})"
        
        self.status_label.config(
            text=status_text,
            foreground=colors.get(self.core.status_type, "black")
        )
        
        # If there's an error, show it in a message box
        if self.core.status_type == "error":
            messagebox.showerror("Error", self.core.status)
    
    def check_status(self):
        """Check live status and update display."""
        self.core.check_live_status()
        self.update_display()
    
    def update_title(self):
        """Update the current live stream title."""
        # First check if we're live
        self.core.check_live_status()
        if self.core.is_live:
            self.core.update_title()
        self.update_display() 