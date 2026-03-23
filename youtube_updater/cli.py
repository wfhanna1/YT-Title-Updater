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
from .exceptions.custom_exceptions import AuthenticationError, RestreamAPIError

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
            mode = getattr(args, "mode", "youtube")
            dry_run = getattr(args, "dry_run", False)
            if mode == "restream":
                if dry_run:
                    return self._handle_update_restream_dry_run()
                return self._handle_update_restream(
                    wait=args.wait, wait_timeout=args.wait_timeout
                )
            return self._handle_update(wait=args.wait, wait_timeout=args.wait_timeout)
        elif args.command == "status":
            return self._handle_status()
        elif args.command == "auth":
            return self._handle_auth()
        elif args.command == "restream-auth":
            return self._handle_restream_auth()
        elif args.command == "restream-status":
            return self._handle_restream_status()
        elif args.command == "configure-email":
            return self._handle_configure_email()
        elif args.command == "test-email":
            return self._handle_test_email()
        return 1

    def _handle_update(self, wait: bool = False, wait_timeout: int = 90) -> int:
        """Handle the update command (YouTube mode).

        Fetches live stream info exactly once via check_live_status() and
        passes the result directly to update_title() to avoid a redundant
        second API call.

        When wait=True, polls every _WAIT_POLL_INTERVAL seconds until the
        stream is live or wait_timeout seconds have elapsed.  Transient API
        errors are printed but retried; persistent errors eventually time out.

        Args:
            wait: When True, retry until live or timeout
            wait_timeout: Maximum seconds to wait before giving up

        Returns:
            int: Exit code (0 success, 1 failure)
        """
        deadline = time.monotonic() + wait_timeout
        last_error: Optional[str] = None

        while True:
            # -- Check live status ----------------------------------------
            try:
                stream_info = self.core.check_live_status()
            except Exception as e:
                last_error = str(e)
                stream_info = None
                # In non-wait mode, fail immediately on API errors.
                if not wait:
                    print(f"Error checking live status: {last_error}", file=sys.stderr)
                    return 1

            # -- No YouTube client (missing credentials) -- fail fast --------
            if stream_info is None and last_error is None:
                print(
                    f"Error: {self.core.status}",
                    file=sys.stderr,
                )
                return 1

            # -- If live, update the title --------------------------------
            if stream_info is not None and self.core.is_live:
                try:
                    self.core.update_title(stream_info=stream_info)
                    print(f"Title updated successfully: {self.core.current_title}")
                    return 0
                except Exception as e:
                    print(f"Error updating title: {str(e)}", file=sys.stderr)
                    return 1

            # -- Not live (or transient error) -- maybe retry --------------
            elapsed = int(wait_timeout - (deadline - time.monotonic()))
            if not wait or time.monotonic() >= deadline:
                if last_error:
                    print(f"Timed out. Last error: {last_error}", file=sys.stderr)
                else:
                    print("Not currently live streaming")
                return 1

            if last_error:
                print(
                    f"Error: {last_error} -- retrying in {_WAIT_POLL_INTERVAL}s"
                    f" ({elapsed}/{wait_timeout}s elapsed)"
                )
                last_error = None
            else:
                print(
                    f"Not live, retrying in {_WAIT_POLL_INTERVAL} seconds..."
                    f" ({elapsed}/{wait_timeout}s elapsed)"
                )
            time.sleep(_WAIT_POLL_INTERVAL)

    def _handle_update_restream_dry_run(self) -> int:
        """Handle update --mode restream --dry-run.

        Authenticates and resolves the next title, but does not PATCH
        or archive. Prints what it would do.

        Returns:
            int: 0 on success, 1 on failure
        """
        if not self.core.config.ensure_restream_token():
            print(
                "Error: No Restream credentials found. "
                "Run `restream-auth` to authenticate.",
                file=sys.stderr,
            )
            return 1

        try:
            self._ensure_restream_client()
        except AuthenticationError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        # Resolve the title that would be used
        next_title = self.core.title_manager.peek_next_title()
        if next_title is None:
            next_title = self.core.title_manager.get_next_title()
            source = "default generator"
        else:
            source = "titles.txt"

        print(f"[DRY RUN] Would update Restream title to: {next_title}")
        print(f"[DRY RUN] Title source: {source}")
        print("[DRY RUN] No changes made.")
        return 0

    def _handle_update_restream(self, wait: bool = False, wait_timeout: int = 90) -> int:
        """Handle the update command in Restream mode.

        Args:
            wait: When True, retry until success or timeout
            wait_timeout: Maximum seconds to wait

        Returns:
            int: Exit code (0 success, 1 failure)
        """
        if not self.core.config.ensure_restream_token():
            msg = "No Restream credentials found. Run `restream-auth` to authenticate."
            print(f"Error: {msg}", file=sys.stderr)
            self._send_auth_failure_email(msg)
            return 1

        # Initialize Restream client
        try:
            self._ensure_restream_client()
        except AuthenticationError as e:
            print(f"Error: {e}", file=sys.stderr)
            self._send_auth_failure_email(str(e))
            return 1

        deadline = time.monotonic() + wait_timeout
        last_error: Optional[str] = None

        while True:
            try:
                self.core.update_title_restream()
                print(f"Restream title updated: {self.core.current_title}")
                return 0
            except (RestreamAPIError, Exception) as e:
                last_error = str(e)
                if not wait:
                    print(f"Error: {last_error}", file=sys.stderr)
                    return 1

            elapsed = int(wait_timeout - (deadline - time.monotonic()))
            if time.monotonic() >= deadline:
                print(f"Timed out. Last error: {last_error}", file=sys.stderr)
                return 1

            print(
                f"Error: {last_error} -- retrying in {_WAIT_POLL_INTERVAL}s"
                f" ({elapsed}/{wait_timeout}s elapsed)"
            )
            last_error = None
            time.sleep(_WAIT_POLL_INTERVAL)

    def _handle_restream_auth(self) -> int:
        """Handle the restream-auth subcommand.

        Reads RESTREAM_CLIENT_ID and RESTREAM_CLIENT_SECRET from env vars
        first, falls back to interactive prompts.

        Returns:
            int: 0 on success, 1 on failure
        """
        import os
        from .core.restream_auth import RestreamAuth

        config = self.core.config
        token_path = config.get_restream_token_path()

        print("Restream OAuth2 Authentication")
        print(f"Token will be saved to: {token_path}")

        client_id = os.environ.get("RESTREAM_CLIENT_ID", "")
        client_secret = os.environ.get("RESTREAM_CLIENT_SECRET", "")

        if client_id and client_secret:
            print("Using credentials from environment variables.")
        else:
            if not client_id:
                client_id = input("Restream Client ID: ").strip()
            if not client_secret:
                client_secret = input("Restream Client Secret: ").strip()

        if not client_id or not client_secret:
            print("Both Client ID and Client Secret are required.", file=sys.stderr)
            return 1

        try:
            auth = RestreamAuth(client_id, client_secret, token_path)
            auth.authenticate()
            print("Restream authentication successful.")
            return 0
        except AuthenticationError as e:
            print(f"Restream authentication failed: {e}", file=sys.stderr)
            return 1

    def _handle_restream_status(self) -> int:
        """Handle the restream-status subcommand.

        Returns:
            int: 0 on success, 1 on failure
        """
        if not self.core.config.ensure_restream_token():
            print(
                "Error: No Restream credentials found. "
                "Run `restream-auth` to authenticate.",
                file=sys.stderr,
            )
            return 1

        try:
            self._ensure_restream_client()
            channels = self.core.restream_client.get_channels()
            PLATFORM_NAMES = {
                1: "twitch", 2: "hitbox", 3: "dailymotion", 4: "custom",
                5: "youtube", 6: "periscope", 7: "smashcast", 8: "mixer",
                9: "picarto", 10: "steam", 15: "vk", 20: "ok",
                37: "facebook", 42: "linkedin", 44: "twitter/x",
                46: "tiktok", 47: "instagram", 48: "kick",
            }
            print(f"Connected platforms: {len(channels)}")
            for ch in channels:
                name = ch.get("displayName", ch.get("name", "unknown"))
                platform_id = ch.get("streamingPlatformId", 0)
                platform = PLATFORM_NAMES.get(platform_id, f"id:{platform_id}")
                enabled = ch.get("enabled", "?")
                print(f"  - {name} ({platform}) [enabled={enabled}]")
            return 0
        except (AuthenticationError, RestreamAPIError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _ensure_restream_client(self) -> None:
        """Initialize the Restream client if not already done.

        Raises:
            AuthenticationError: If token is missing or invalid
        """
        if self.core.restream_client is not None:
            return

        import os
        from .core.restream_auth import RestreamAuth
        from .core.restream_client import RestreamClient

        token_path = self.core.config.get_restream_token_path()

        # Env vars take priority, fall back to token file for client_id
        client_id = os.environ.get("RESTREAM_CLIENT_ID", "")
        client_secret = os.environ.get("RESTREAM_CLIENT_SECRET", "")

        if not client_id:
            auth_tmp = RestreamAuth(client_id="", client_secret="", token_path=token_path)
            token_data = auth_tmp.load_token()
            if token_data is None:
                raise AuthenticationError(
                    "No Restream credentials found. Run `restream-auth` to authenticate."
                )
            client_id = token_data.get("client_id", "")

        if not client_secret:
            raise AuthenticationError(
                "RESTREAM_CLIENT_SECRET environment variable is required for token refresh. "
                "Set it and retry, or run `restream-auth` to re-authenticate."
            )

        auth = RestreamAuth(
            client_id=client_id,
            client_secret=client_secret,
            token_path=token_path,
        )
        access_token = auth.get_valid_token()
        self.core.restream_client = RestreamClient(access_token)

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

    def _handle_configure_email(self) -> int:
        """Handle the configure-email subcommand.

        Prompts for ACS connection string, sender, and recipients,
        then saves to email_config.json.

        Returns:
            int: 0 on success, 1 on failure
        """
        print("Configure email notifications for authentication failures.")

        connection_string = input("ACS Connection String: ").strip()
        sender = input("Sender email address: ").strip()
        recipients_raw = input("Recipient email addresses (semicolon-separated): ").strip()

        if not connection_string or not sender or not recipients_raw:
            print("All fields are required.", file=sys.stderr)
            return 1

        recipients = [r.strip() for r in recipients_raw.split(";") if r.strip()]
        if not recipients:
            print("At least one recipient is required.", file=sys.stderr)
            return 1

        config = {
            "connection_string": connection_string,
            "sender": sender,
            "recipients": recipients,
        }
        self.core.config.save_email_config(config)
        print("Email configuration saved.")
        return 0

    def _handle_test_email(self) -> int:
        """Handle the test-email subcommand.

        Sends a test email using the saved configuration.

        Returns:
            int: 0 on success, 1 on failure
        """
        email_config = self._get_email_config()
        if email_config is None:
            print(
                "Error: Email not configured. Set ACS_CONNECTION_STRING, ACS_SENDER, "
                "ACS_RECIPIENTS env vars, or run `configure-email`.",
                file=sys.stderr,
            )
            return 1

        from .notifications.email_notifier import EmailNotifier
        notifier = EmailNotifier(
            connection_string=email_config["connection_string"],
            sender=email_config["sender"],
            recipients=email_config["recipients"],
        )
        success = notifier.send_error_notification(
            subject="Test Notification",
            body="This is a test email from YT-Title-Updater. If you received this, email notifications are working.",
        )
        if success:
            print("Test email sent successfully.")
            return 0
        else:
            print("Failed to send test email. Check your configuration.", file=sys.stderr)
            return 1

    def _get_email_config(self) -> dict:
        """Get email config from env vars or config file.

        Env vars take priority: ACS_CONNECTION_STRING, ACS_SENDER, ACS_RECIPIENTS.

        Returns:
            Dict with connection_string, sender, recipients, or None
        """
        import os
        conn = os.environ.get("ACS_CONNECTION_STRING", "")
        sender = os.environ.get("ACS_SENDER", "")
        recipients_raw = os.environ.get("ACS_RECIPIENTS", "")

        if conn and sender and recipients_raw:
            return {
                "connection_string": conn,
                "sender": sender,
                "recipients": [r.strip() for r in recipients_raw.split(";") if r.strip()],
            }

        return self.core.config.get_email_config()

    def _send_auth_failure_email(self, error_message: str) -> None:
        """Best-effort email notification on auth failure.

        Checks env vars first, falls back to config file. Never raises.
        """
        try:
            email_config = self._get_email_config()
            if email_config is None:
                return
            from .notifications.email_notifier import EmailNotifier
            notifier = EmailNotifier(
                connection_string=email_config["connection_string"],
                sender=email_config["sender"],
                recipients=email_config["recipients"],
            )
            notifier.send_error_notification(
                subject="Authentication Failure",
                body=f"YT-Title-Updater encountered an authentication failure:\n\n{error_message}",
            )
        except Exception:
            pass

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
        description="Live Stream Title Updater CLI",
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
        "--mode",
        choices=["youtube", "restream"],
        default="youtube",
        help="Which platform to update (default: youtube)"
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
    update_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        dest="dry_run",
        help="Show what would be done without making changes (Restream mode only)"
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

    # Restream auth command
    subparsers.add_parser(
        "restream-auth",
        help="Authenticate with Restream (interactive OAuth2 browser flow)"
    )

    # Restream status command
    subparsers.add_parser(
        "restream-status",
        help="List connected Restream channels"
    )

    # Email configuration command
    subparsers.add_parser(
        "configure-email",
        help="Configure email notifications for authentication failures"
    )

    # Test email command
    subparsers.add_parser(
        "test-email",
        help="Send a test email notification"
    )

    args = parser.parse_args()

    cli = YouTubeUpdaterCLI(args.config_dir)
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
