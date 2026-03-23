"""Integration tests for email notifications."""

import json
from unittest.mock import patch, MagicMock
import argparse

from youtube_updater.core.config_manager import ConfigManager
from youtube_updater.notifications.email_notifier import EmailNotifier

PATCH_TARGET = "youtube_updater.notifications.email_notifier.EmailClient"


class TestEmailIntegration:
    """Integration tests: configure -> save -> load -> send cycle."""

    def test_configure_save_load_send_cycle(self, tmp_path):
        """Full cycle: save email config, load it, create notifier, send."""
        cm = ConfigManager(str(tmp_path))
        config = {
            "connection_string": "endpoint=https://fake.com/;accesskey=key",
            "sender": "noreply@test.azurecomm.net",
            "recipients": ["admin@example.com"],
        }
        cm.save_email_config(config)

        loaded = cm.get_email_config()
        assert loaded is not None

        notifier = EmailNotifier(
            connection_string=loaded["connection_string"],
            sender=loaded["sender"],
            recipients=loaded["recipients"],
        )

        mock_client = MagicMock()
        mock_poller = MagicMock()
        mock_poller.result.return_value = MagicMock(status="Succeeded")
        mock_client.begin_send.return_value = mock_poller

        with patch(PATCH_TARGET) as MockEmailClient:
            MockEmailClient.from_connection_string.return_value = mock_client
            result = notifier.send_error_notification("Test", "Integration test")

        assert result is True
        mock_client.begin_send.assert_called_once()

    def test_auth_failure_triggers_email_send(self, tmp_path):
        """Restream auth failure calls _send_auth_failure_email which sends."""
        from youtube_updater.cli import YouTubeUpdaterCLI

        cm = ConfigManager(str(tmp_path))
        cm.save_email_config({
            "connection_string": "endpoint=https://fake.com/;accesskey=key",
            "sender": "noreply@test.azurecomm.net",
            "recipients": ["admin@example.com"],
        })

        with patch("youtube_updater.core.factory.ComponentFactory.create_core") as mock_factory:
            mock_core = MagicMock()
            mock_core.config = cm
            mock_core.config.ensure_restream_token = MagicMock(return_value=False)
            mock_core.restream_client = None
            mock_factory.return_value = mock_core

            cli = YouTubeUpdaterCLI(str(tmp_path))

            args = argparse.Namespace(
                command="update", mode="restream", wait=False, wait_timeout=90,
                dry_run=False,
            )

            mock_client = MagicMock()
            mock_poller = MagicMock()
            mock_poller.result.return_value = MagicMock(status="Succeeded")
            mock_client.begin_send.return_value = mock_poller

            with patch(PATCH_TARGET) as MockEmailClient:
                MockEmailClient.from_connection_string.return_value = mock_client
                result = cli.run(args)

            assert result == 1
            # Email should have been sent
            mock_client.begin_send.assert_called_once()
