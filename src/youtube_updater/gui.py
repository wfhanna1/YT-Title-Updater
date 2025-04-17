import sys
import time
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMenuBar, QMenu, QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon
from .core import YouTubeUpdaterCore

class YouTubeUpdaterGUI(QMainWindow):
    """GUI implementation for YouTube Title Updater using PyQt6."""
    
    def __init__(self, core: Optional[YouTubeUpdaterCore] = None):
        """Initialize the GUI.
        
        Args:
            core: Core functionality instance. If None, creates a new instance.
        """
        super().__init__()
        self.core = core if core is not None else YouTubeUpdaterCore()
        
        # Set window properties
        self.setWindowTitle("YouTube Title Updater")
        self.setMinimumSize(600, 400)
        
        # Create UI elements
        self.create_menu()
        self.create_main_widget()
        self.create_status_bar()
        
        # Set up update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_status)
        self.update_timer.start(30000)  # Update every 30 seconds
        
        # Initial update
        self.check_status()
    
    def create_menu(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_config_action = QAction("Open Config Folder", self)
        open_config_action.triggered.connect(self.core.open_config_dir)
        file_menu.addAction(open_config_action)
        
        open_titles_action = QAction("Open Titles File", self)
        open_titles_action.triggered.connect(self.core.open_titles_file)
        file_menu.addAction(open_titles_action)
        
        file_menu.addSeparator()
        
        check_now_action = QAction("Check Now", self)
        check_now_action.triggered.connect(self.check_status)
        file_menu.addAction(check_now_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
    
    def create_main_widget(self):
        """Create the main widget and its contents."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Current Title
        current_title_label = QLabel("Current Title:")
        current_title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(current_title_label)
        
        self.current_title_display = QLabel(self.core.current_title)
        self.current_title_display.setWordWrap(True)
        layout.addWidget(self.current_title_display)
        
        # Next Title
        next_title_label = QLabel("Next Title:")
        next_title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(next_title_label)
        
        self.next_title_display = QLabel(self.core.next_title)
        self.next_title_display.setWordWrap(True)
        layout.addWidget(self.next_title_display)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.update_button = QPushButton("Update Title")
        self.update_button.clicked.connect(self.update_title)
        button_layout.addWidget(self.update_button)
        
        self.open_titles_button = QPushButton("Open Titles File")
        self.open_titles_button.clicked.connect(self.core.open_titles_file)
        button_layout.addWidget(self.open_titles_button)
        
        layout.addLayout(button_layout)
    
    def create_status_bar(self):
        """Create the status bar."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.update_status()
    
    def update_status(self):
        """Update the status bar with current information."""
        colors = {
            "success": "green",
            "error": "red",
            "warning": "orange",
            "info": "black"
        }
        
        status_text = self.core.status
        if self.core.status_type != "error":
            status_text += f" (Last updated: {time.strftime('%H:%M:%S')})"
        
        self.statusBar.showMessage(status_text)
        
        # If there's an error, show it in a message box
        if self.core.status_type == "error":
            QMessageBox.critical(self, "Error", self.core.status)
    
    def check_status(self):
        """Check live status and update display."""
        self.core.check_live_status()
        self.update_display()
    
    def update_display(self):
        """Update the display with current information."""
        self.current_title_display.setText(self.core.current_title)
        self.next_title_display.setText(self.core.next_title)
        self.update_status()
    
    def update_title(self):
        """Update the current live stream title."""
        self.core.update_title()
        self.update_display()

def main():
    """Launch the YouTube Title Updater application."""
    app = QApplication(sys.argv)
    window = YouTubeUpdaterGUI()
    window.show()
    sys.exit(app.exec()) 