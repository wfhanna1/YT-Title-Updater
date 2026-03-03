#!/usr/bin/env python3
"""Main entry point for YouTube Title Updater.

Run with: python -m youtube_updater [command]
"""

import sys
from youtube_updater.cli import main

if __name__ == "__main__":
    sys.exit(main())
