#!/usr/bin/env python3
"""
Main entry point for YouTube Title Updater.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, Union

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from youtube_updater.gui import YouTubeUpdaterGUI
from youtube_updater.cli import main as cli_main

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="YouTube Title Updater")
    parser.add_argument("--config-dir", type=str, help="Custom configuration directory")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("command", nargs="?", choices=["status", "update"], help="CLI command to run")
    return parser.parse_args()

def main(config_dir: Optional[Union[str, Path]] = None):
    """Main entry point for the application."""
    args = parse_arguments()
    
    if args.headless or args.command:
        # Run in CLI mode
        cli_main()
    else:
        # Run in GUI mode
        from PyQt6.QtWidgets import QApplication
        app = QApplication([])
        window = YouTubeUpdaterGUI(config_dir=config_dir)
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main() 