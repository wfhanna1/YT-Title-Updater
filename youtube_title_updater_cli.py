#!/usr/bin/env python3
"""
YouTube Title Updater CLI

A command-line interface for automatically updating YouTube live stream titles.
"""

import sys
import argparse
from youtube_updater.core import ComponentFactory
from youtube_updater.core.default_title_generator import DefaultTitleGenerator

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='YouTube Title Updater CLI')
    parser.add_argument('--config-dir', type=str,
                      help='Custom configuration directory')
    parser.add_argument('--status', action='store_true',
                      help='Check current stream status and exit')
    parser.add_argument('--update', action='store_true',
                      help='Update the stream title once and exit')
    return parser.parse_args()

def main():
    """Launch the YouTube Title Updater CLI application."""
    args = parse_args()
    
    try:
        # Use the factory to create the core updater
        updater = ComponentFactory.create_core(config_dir=args.config_dir)
        title_generator = DefaultTitleGenerator()
        
        if args.status:
            updater.check_live_status()
            print(f"Stream Status: {updater.status}")
            print(f"Current Title: {updater.current_title}")
            print(f"Is Live: {updater.is_live}")
            return
        
        if args.update:
            updater.check_live_status()
            if updater.is_live:
                # If no titles are available, use the default title generator
                if not updater.get_next_title():
                    updater.add_title(title_generator.generate_title())
                updater.update_title()
                print(f"Title updated. Status: {updater.status}")
            else:
                print(f"Not live. Status: {updater.status}")
            return
        
        print("Please specify --status or --update.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 