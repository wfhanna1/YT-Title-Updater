"""Unit tests for StatusManager."""

import pytest
from unittest.mock import MagicMock

from youtube_updater.core.status_manager import StatusManager


class TestStatusManager:
    """Test cases for StatusManager."""

    def test_initial_status(self):
        """Test StatusManager initializes with 'Initializing' and 'info' type."""
        sm = StatusManager()
        assert sm.status == "Initializing"
        assert sm.status_type == "info"

    def test_set_status_updates_status_and_type(self):
        """Test set_status stores the message and status type."""
        sm = StatusManager()
        sm.set_status("Connected", "success")
        assert sm.status == "Connected"
        assert sm.status_type == "success"

    def test_set_status_info_type(self):
        """Test set_status with info type."""
        sm = StatusManager()
        sm.set_status("Ready", "info")
        assert sm.status == "Ready"
        assert sm.status_type == "info"

    def test_set_status_warning_type(self):
        """Test set_status with warning type."""
        sm = StatusManager()
        sm.set_status("Low titles", "warning")
        assert sm.status == "Low titles"
        assert sm.status_type == "warning"

    def test_set_status_error_type(self):
        """Test set_status with error type."""
        sm = StatusManager()
        sm.set_status("API failed", "error")
        assert sm.status == "API failed"
        assert sm.status_type == "error"

    def test_set_status_invalid_type_raises_value_error(self):
        """Test set_status raises ValueError for an invalid status type."""
        sm = StatusManager()
        with pytest.raises(ValueError):
            sm.set_status("Test", "invalid_type")

    def test_set_status_calls_logger_info_for_info_type(self):
        """Test set_status calls logger.info for info status."""
        mock_logger = MagicMock()
        sm = StatusManager(mock_logger)
        sm.set_status("All good", "info")
        mock_logger.info.assert_called_once_with("All good")

    def test_set_status_calls_logger_error_for_error_type(self):
        """Test set_status calls logger.error for error status."""
        mock_logger = MagicMock()
        sm = StatusManager(mock_logger)
        sm.set_status("Error occurred", "error")
        mock_logger.error.assert_called_once_with("Error occurred")

    def test_set_status_calls_logger_warning_for_warning_type(self):
        """Test set_status calls logger.warning for warning status."""
        mock_logger = MagicMock()
        sm = StatusManager(mock_logger)
        sm.set_status("Watch out", "warning")
        mock_logger.warning.assert_called_once_with("Watch out")

    def test_set_status_calls_logger_info_for_success_type(self):
        """Test set_status calls logger.info for success status."""
        mock_logger = MagicMock()
        sm = StatusManager(mock_logger)
        sm.set_status("Done!", "success")
        mock_logger.info.assert_called_once_with("Done!")

    def test_set_status_without_logger_does_not_raise(self):
        """Test set_status works fine when no logger is provided."""
        sm = StatusManager()
        sm.set_status("No logger", "info")
        assert sm.status == "No logger"

    def test_add_status_callback_is_called_on_set_status(self):
        """Test that registered callbacks are invoked when set_status is called."""
        sm = StatusManager()
        callback = MagicMock()
        sm.add_status_callback(callback)

        sm.set_status("Update!", "success")

        callback.assert_called_once_with("Update!", "success")

    def test_multiple_callbacks_all_invoked(self):
        """Test that multiple registered callbacks are all invoked."""
        sm = StatusManager()
        cb1 = MagicMock()
        cb2 = MagicMock()
        sm.add_status_callback(cb1)
        sm.add_status_callback(cb2)

        sm.set_status("Broadcast", "info")

        cb1.assert_called_once_with("Broadcast", "info")
        cb2.assert_called_once_with("Broadcast", "info")
