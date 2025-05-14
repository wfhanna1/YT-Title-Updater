#!/usr/bin/env python3
"""
YouTube Title Updater Module Entry Point

Supports commands:
    status - Check the current status of the YouTube stream
    update - Update the stream title
"""

import sys
import argparse
from .core import YouTubeUpdaterCore

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='YouTube Title Updater CLI')
    parser.add_argument('--config-dir', type=str, help='Custom configuration directory')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Status command
    status_parser = subparsers.add_parser('status', help='Check stream status')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update stream title')
    
    return parser.parse_args()

def main():
    """Main entry point for the module."""
    args = parse_args()
    
    try:
        updater = YouTubeUpdaterCore(config_dir=args.config_dir)
        
        if args.command == 'status':
            updater.check_live_status()
            print(f"Stream Status: {updater.status}")
            print(f"Current Title: {updater.current_title}")
            print(f"Is Live: {updater.is_live}")
            
        elif args.command == 'update':
            updater.update_title()
            print(f"Title updated. New status: {updater.status}")
            
        else:
            print("Please specify a command: status or update")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 