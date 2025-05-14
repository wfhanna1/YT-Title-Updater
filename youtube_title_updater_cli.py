#!/usr/bin/env python3
"""
YouTube Title Updater CLI

A command-line interface for automatically updating YouTube live stream titles.
"""

import sys
import argparse
from youtube_updater.core import YouTubeTitleUpdater

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='YouTube Title Updater CLI')
    parser.add_argument('--titles-file', type=str, default='titles.txt',
                      help='Path to the file containing titles (default: titles.txt)')
    parser.add_argument('--interval', type=int, default=300,
                      help='Update interval in seconds (default: 300)')
    return parser.parse_args()

def main():
    """Launch the YouTube Title Updater CLI application."""
    args = parse_args()
    
    try:
        updater = YouTubeTitleUpdater(titles_file=args.titles_file)
        updater.start_update_loop(interval=args.interval)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 