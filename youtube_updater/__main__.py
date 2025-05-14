#!/usr/bin/env python3
"""
Main entry point for YouTube Title Updater.
"""

import sys
from PyQt6.QtWidgets import QApplication

from .gui import YouTubeUpdaterGUI
from .cli import main as cli_main

def main():
    """Launch the YouTube Title Updater application."""
    if len(sys.argv) > 1:
        # Run in CLI mode if arguments are provided
        sys.exit(cli_main())
    else:
        # Run in GUI mode if no arguments are provided
        app = QApplication(sys.argv)
        window = YouTubeUpdaterGUI()
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main() 