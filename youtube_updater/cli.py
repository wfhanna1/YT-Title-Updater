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
from .core.auth_manager import AuthManager

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
        elif args.command == "auth":
            return self._handle_auth()
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

    def _handle_auth(self) -> int:
        """Handle the auth subcommand.

        Guides the user through placing client_secrets.json in the config
        directory, then runs the OAuth browser flow to produce token.json.

        Returns:
            int: 0 on success, 1 on failure
        """
        config = self.core.config
        config_dir = str(config.config_dir)
        secrets_path = config.get_client_secrets_path()
        print(f"Config directory: {config_dir}")

        if not config.ensure_client_secrets():
            print(
                f"client_secrets.json not found.\n"
                f"Download it from the Google Cloud Console and copy it to:\n"
                f"  {secrets_path}"
            )
            return 1

        try:
            token_path = config.get_file_paths()["token_path"]
            auth = AuthManager(secrets_path, token_path)
            auth.get_credentials()
            print("Authentication successful. token.json saved.")
            return 0
        except Exception as e:
            print(f"Authentication failed: {e}", file=sys.stderr)
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

    # Auth command
    subparsers.add_parser(
        "auth",
        help="Authorise the YouTube account (run once after placing client_secrets.json)"
    )

    args = parser.parse_args()

    cli = YouTubeUpdaterCLI(args.config_dir)
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
