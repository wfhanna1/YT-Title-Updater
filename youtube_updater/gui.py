import os
import time
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLabel, QMenuBar, QMenu, QStatusBar,
                           QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .core import YouTubeUpdaterCore
from pathlib import Path
from typing import Optional, Union

class YouTubeUpdaterGUI(QMainWindow):
    """GUI implementation for YouTube Title Updater."""
    
    def __init__(self, core=None):
        """Initialize the GUI.
        
        Args:
            core (YouTubeUpdaterCore, optional): Core functionality instance.
                                               If None, creates a new instance.
        """
        super().__init__()
        self.setWindowTitle("YouTube Title Updater")
        self.setGeometry(100, 100, 600, 400)
        
        # Initialize core functionality
        self.core = core if core is not None else YouTubeUpdaterCore()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        
        # Create GUI elements
        self.create_menu()
        self.create_title_labels()
        self.create_buttons()
        self.create_status_bar()
        
        # Update display immediately
        self.update_display()
    
    def create_menu(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.setObjectName("File")
        
        # Add menu actions
        open_config_action = file_menu.addAction("Open Config Folder")
        open_config_action.triggered.connect(self.core.open_config_dir)
        
        open_titles_action = file_menu.addAction("Open Titles File")
        open_titles_action.triggered.connect(self.core.open_titles_file)
        
        file_menu.addSeparator()
        
        check_now_action = file_menu.addAction("Check Now")
        check_now_action.triggered.connect(self.check_status)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
    
    def create_title_labels(self):
        """Create labels for displaying current and next titles."""
        # Current Title
        current_title_header = QLabel("Current Title:")
        current_title_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.layout.addWidget(current_title_header)
        
        self.current_title_display = QLabel(self.core.current_title)
        self.current_title_display.setFont(QFont("Arial", 12))
        self.current_title_display.setWordWrap(True)
        self.layout.addWidget(self.current_title_display)
        
        # Next Title
        next_title_header = QLabel("Next Title:")
        next_title_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.layout.addWidget(next_title_header)
        
        self.next_title_display = QLabel(self.core.next_title)
        self.next_title_display.setFont(QFont("Arial", 12))
        self.next_title_display.setWordWrap(True)
        self.layout.addWidget(self.next_title_display)
    
    def create_buttons(self):
        """Create action buttons."""
        button_layout = QHBoxLayout()
        
        # Update Title Button
        self.update_button = QPushButton("Update Title")
        self.update_button.clicked.connect(self.update_title)
        button_layout.addWidget(self.update_button)
        
        # Open Titles Button
        self.open_titles_button = QPushButton("Open Titles File")
        self.open_titles_button.clicked.connect(self.core.open_titles_file)
        button_layout.addWidget(self.open_titles_button)
        
        self.layout.addLayout(button_layout)
    
    def create_status_bar(self):
        """Create the status bar."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.update_status()
    
    def update_status(self):
        """Update the status bar with current status."""
        status_text = self.core.status
        if self.core.status_type != "error" and not hasattr(self.core, "_test_mode"):
            status_text += f" (Last updated: {time.strftime('%H:%M:%S')})"
        
        # Set status bar color based on status type
        colors = {
            "success": "green",
            "error": "red",
            "warning": "orange",
            "info": "black"
        }
        color = colors.get(self.core.status_type, "black")
        self.statusBar.setStyleSheet(f"color: {color};")
        self.statusBar.showMessage(status_text)
    
    def update_display(self):
        """Update the display with current information."""
        self.current_title_display.setText(self.core.current_title)
        self.next_title_display.setText(self.core.next_title)
        self.update_status()
    
    def check_status(self):
        """Check live status and update display."""
        self.core.check_live_status()
        self.update_display()
    
    def update_title(self):
        """Update the current live stream title."""
        self.core.check_live_status()
        if self.core.is_live:
            self.core.update_title()
        self.update_display()

def main(config_dir: Optional[Union[str, Path]] = None):
    """Main entry point for the application.
    
    Args:
        config_dir: Optional directory for configuration files.
                   Can be a string path or Path object.
    """
    app = QApplication([])
    core = YouTubeUpdaterCore(config_dir=config_dir)
    window = YouTubeUpdaterGUI(core=core)
    window.show()
    app.exec() 