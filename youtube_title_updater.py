#!/usr/bin/env python3
"""
YouTube Title Updater

A GUI application for automatically updating YouTube live stream titles.
"""

import sys
from PyQt6.QtWidgets import QApplication
from youtube_updater import YouTubeUpdaterGUI

def main():
    """Launch the YouTube Title Updater application."""
    app = QApplication(sys.argv)
    window = YouTubeUpdaterGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 