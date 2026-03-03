#!/usr/bin/env python3
"""
CLI interface for YouTube Title Updater.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional, Union

from .core.factory import ComponentFactory

# Polling interval used by the --wait retry loop (seconds).
_WAIT_POLL_INTERVAL = 10


class YouTubeUpdaterCLI:
    """Command-line interface for YouTube Title Updater."""

    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
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
            return self._handle_update(wait=args.wait, wait_timeout=args.wait_timeout)
        elif args.command == "status":
            return self._handle_status()
        return 1

    def _handle_update(self, wait: bool = False, wait_timeout: int = 90) -> int:
        """Handle the update command.

        Fetches live stream info exactly once via check_live_status() and
        passes the result directly to update_title() to avoid a redundant
        second API call.

        When wait=True, polls every _WAIT_POLL_INTERVAL seconds until the
        stream is live or wait_timeout seconds have elapsed.

        Args:
            wait: When True, retry until live or timeout
            wait_timeout: Maximum seconds to wait before giving up

        Returns:
            int: Exit code (0 success, 1 failure)
        """
        try:
            deadline = time.monotonic() + wait_timeout

            while True:
                stream_info = self.core.check_live_status()
                if self.core.is_live:
                    # Pass the already-fetched stream_info to skip the second
                    # get_live_stream_info() call inside update_title().
                    self.core.update_title(stream_info=stream_info)
                    print(f"Title updated successfully: {self.core.current_title}")
                    return 0

                elapsed = int(wait_timeout - (deadline - time.monotonic()))
                if not wait or time.monotonic() >= deadline:
                    print("Not currently live streaming")
                    return 1

                print(
                    f"Not live, retrying in {_WAIT_POLL_INTERVAL} seconds..."
                    f" ({elapsed}/{wait_timeout}s elapsed)"
                )
                time.sleep(_WAIT_POLL_INTERVAL)

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
    update_parser.add_argument(
        "--wait",
        action="store_true",
        default=False,
        help=(
            "Poll until the channel is live before updating. "
            "Retries every 10 seconds up to --wait-timeout seconds."
        )
    )
    update_parser.add_argument(
        "--wait-timeout",
        type=int,
        default=90,
        dest="wait_timeout",
        metavar="N",
        help="Maximum seconds to wait for the stream to go live (default: 90)"
    )

    # Status command
    subparsers.add_parser(
        "status",
        help="Check the current live stream status"
    )

    args = parser.parse_args()

    cli = YouTubeUpdaterCLI(args.config_dir)
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
