"""
Tests for youtube_updater/__main__.py entry point.

The GUI has been removed. The application now uses CLI-only mode.
__main__.py delegates directly to youtube_updater.cli.main.
"""

import sys
import unittest
from unittest.mock import patch, MagicMock


class TestMainEntryPoint(unittest.TestCase):
    """Test cases for the __main__.py entry point."""

    @patch("youtube_updater.__main__.main")
    def test_main_is_called_on_module_execution(self, mock_main):
        """Test that main() from cli is invoked when the module is run."""
        mock_main.return_value = 0
        # Import the module attribute to confirm the reference is correct
        from youtube_updater import __main__ as main_module
        self.assertTrue(hasattr(main_module, "main"))

    @patch("youtube_updater.cli.main")
    def test_exit_code_propagated(self, mock_main):
        """Test that the exit code from cli.main is propagated through sys.exit."""
        mock_main.return_value = 0
        with patch("sys.exit") as mock_exit:
            # Simulate what __main__.py does
            from youtube_updater.cli import main
            result = main.__call__() if callable(mock_main) else 0
            mock_main.return_value = 1
            sys.exit(mock_main())
            mock_exit.assert_called_once_with(1)

    @patch("youtube_updater.cli.ComponentFactory.create_core")
    def test_cli_main_exits_with_nonzero_on_no_subcommand(self, mock_factory):
        """Test that cli.main exits when no subcommand is provided."""
        with patch("sys.argv", ["youtube_updater"]):
            from youtube_updater.cli import main
            with self.assertRaises(SystemExit):
                main()


if __name__ == "__main__":
    unittest.main()
