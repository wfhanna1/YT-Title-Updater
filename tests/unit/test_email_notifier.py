"""Unit tests for EmailNotifier."""

from unittest.mock import patch, MagicMock

import pytest

from youtube_updater.notifications.email_notifier import EmailNotifier

PATCH_TARGET = "youtube_updater.notifications.email_notifier.EmailClient"


def _make_notifier():
    return EmailNotifier(
        connection_string="endpoint=https://fake.com/;accesskey=fakekey",
        sender="noreply@test.azurecomm.net",
        recipients=["admin@example.com"],
    )


def _mock_email_client():
    mock_client = MagicMock()
    mock_poller = MagicMock()
    mock_poller.result.return_value = MagicMock(status="Succeeded")
    mock_client.begin_send.return_value = mock_poller
    return mock_client


class TestSendErrorNotification:
    def test_send_error_notification_success(self):
        """Successful send returns True."""
        notifier = _make_notifier()
        mock_client = _mock_email_client()

        with patch(PATCH_TARGET) as MockEmailClient:
            MockEmailClient.from_connection_string.return_value = mock_client
            result = notifier.send_error_notification("Auth Failed", "Details")

        assert result is True
        mock_client.begin_send.assert_called_once()

    def test_send_error_notification_failure_no_raise(self):
        """ACS failure returns False, does not raise."""
        notifier = _make_notifier()

        with patch(PATCH_TARGET) as MockEmailClient:
            MockEmailClient.from_connection_string.side_effect = Exception("ACS down")
            result = notifier.send_error_notification("Auth Failed", "Details")

        assert result is False

    def test_send_error_notification_returns_true(self):
        """Verify return value is explicitly True on success."""
        notifier = _make_notifier()
        mock_client = _mock_email_client()

        with patch(PATCH_TARGET) as MockEmailClient:
            MockEmailClient.from_connection_string.return_value = mock_client
            result = notifier.send_error_notification("Test", "Body")

        assert result is True

    def test_send_to_multiple_recipients(self):
        """Email sent to all configured recipients."""
        notifier = EmailNotifier(
            connection_string="endpoint=https://fake.com/;accesskey=fakekey",
            sender="noreply@test.azurecomm.net",
            recipients=["wasim@example.com", "nader@example.com"],
        )
        mock_client = _mock_email_client()

        with patch(PATCH_TARGET) as MockEmailClient:
            MockEmailClient.from_connection_string.return_value = mock_client
            result = notifier.send_error_notification("Test", "Body")

        assert result is True
        call_args = mock_client.begin_send.call_args
        message = call_args[0][0]
        to_addresses = message["recipients"]["to"]
        assert len(to_addresses) == 2
        assert to_addresses[0]["address"] == "wasim@example.com"
        assert to_addresses[1]["address"] == "nader@example.com"
