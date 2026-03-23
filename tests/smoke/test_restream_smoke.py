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

    def test_restream_client_importable(self):
        result = subprocess.run(
            [sys.executable, "-c", "from youtube_updater.core.restream_client import RestreamClient"],
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


class TestRestreamCLICommands:
    """E2E tests for new Restream CLI commands via subprocess."""

    def test_update_help_shows_mode_flag(self):
        result = subprocess.run(
            [sys.executable, "-m", "youtube_updater", "update", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--mode" in result.stdout
        assert "youtube" in result.stdout
        assert "restream" in result.stdout

    def test_restream_auth_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "youtube_updater", "restream-auth", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_restream_status_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "youtube_updater", "restream-status", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_restream_status_no_creds_exits_1(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "youtube_updater",
             "--config-dir", str(tmp_path), "restream-status"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "restream-auth" in result.stderr

    def test_update_restream_no_creds_exits_1(self, tmp_path):
        result = subprocess.run(
            [sys.executable, "-m", "youtube_updater",
             "--config-dir", str(tmp_path), "update", "--mode", "restream"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "restream-auth" in result.stderr
