#!/usr/bin/env python3
"""
CLI interface for YouTube Title Updater.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .core.factory import ComponentFactory

class YouTubeUpdaterCLI:
    """Command-line interface for YouTube Title Updater."""
    
    def __init__(self, config_dir: Optional[str | Path] = None):
        """Initialize the CLI interface.
        
        Args:
            config_dir: Optional custom config directory path
        """
        self.core = ComponentFactory.create_core(config_dir)
    
    def run(self, args: argparse.Namespace) -> int:
        """Run the CLI command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        if args.command == "update":
            return self._handle_update()
        elif args.command == "status":
            return self._handle_status()
        return 1
    
    def _handle_update(self) -> int:
        """Handle the update command.
        
        Returns:
            int: Exit code
        """
        try:
            self.core.check_live_status()
            if self.core.is_live:
                self.core.update_title()
                print(f"Title updated successfully: {self.core.current_title}")
                return 0
            else:
                print("Not currently live streaming")
                return 1
        except Exception as e:
            print(f"Error updating title: {str(e)}", file=sys.stderr)
            return 1
    
    def _handle_status(self) -> int:
        """Handle the status command.
        
        Returns:
            int: Exit code
        """
        try:
            self.core.check_live_status()
            print(f"Live Status: {'Live' if self.core.is_live else 'Not Live'}")
            print(f"Current Title: {self.core.current_title}")
            print(f"Next Title: {self.core.next_title}")
            print(f"Status: {self.core.status} ({self.core.status_type})")
            return 0
        except Exception as e:
            print(f"Error getting status: {str(e)}", file=sys.stderr)
            return 1

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="YouTube Title Updater CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--config-dir",
        type=str,
        help="Custom configuration directory path"
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Update command
    update_parser = subparsers.add_parser(
        "update",
        help="Update the current live stream title"
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Check the current live stream status"
    )
    
    args = parser.parse_args()
    
    cli = YouTubeUpdaterCLI(args.config_dir)
    return cli.run(args)

if __name__ == "__main__":
    sys.exit(main()) 