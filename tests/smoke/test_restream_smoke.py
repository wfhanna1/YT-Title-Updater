"""Smoke tests for Restream integration."""

import subprocess
import sys


class TestRestreamImports:
    """Verify Restream modules are importable without errors."""

    def test_restream_auth_importable(self):
        result = subprocess.run(
            [sys.executable, "-c", "from youtube_updater.core.restream_auth import RestreamAuth"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"

    def test_restream_api_error_importable(self):
        result = subprocess.run(
            [sys.executable, "-c", "from youtube_updater.exceptions.custom_exceptions import RestreamAPIError"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"

    def test_cli_help_still_works(self):
        """Existing CLI --help continues to work after new modules added."""
        result = subprocess.run(
            [sys.executable, "-m", "youtube_updater", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "YouTube Title Updater" in result.stdout
