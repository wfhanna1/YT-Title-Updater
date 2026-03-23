"""Email notifications via Azure Communication Services."""

from typing import List

from azure.communication.email import EmailClient


class EmailNotifier:
    """Best-effort email notifications for authentication failures.

    Never raises exceptions, never blocks the caller. If sending fails,
    it returns False and the caller continues normally.
    """

    def __init__(self, connection_string: str, sender: str, recipients: List[str]):
        self.connection_string = connection_string
        self.sender = sender
        self.recipients = recipients

    def send_error_notification(self, subject: str, body: str) -> bool:
        """Send an error notification email.

        Args:
            subject: Email subject line
            body: Email body text

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            client = EmailClient.from_connection_string(self.connection_string)
            message = {
                "senderAddress": self.sender,
                "recipients": {
                    "to": [{"address": addr} for addr in self.recipients],
                },
                "content": {
                    "subject": f"[YT-Title-Updater] {subject}",
                    "plainText": body,
                },
            }
            poller = client.begin_send(message)
            poller.result()
            return True
        except Exception:
            return False
