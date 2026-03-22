"""NF4 safeguard: verify that config operations never touch YouTube auth files."""

import time

import pytest

from youtube_updater.core.config_manager import ConfigManager


YOUTUBE_AUTH_FILES = ["token.json", "credentials.json", "token.pickle"]


class TestNF4Safeguard:
    """Verify that ConfigManager Restream/email methods never modify YouTube auth files."""

    def test_get_restream_token_path_does_not_touch_yt_auth(self, tmp_path):
        """get_restream_token_path() must not modify any YouTube auth file."""
        for name in YOUTUBE_AUTH_FILES:
            (tmp_path / name).write_text("sentinel")
        before = {n: (tmp_path / n).stat().st_mtime for n in YOUTUBE_AUTH_FILES}
        time.sleep(0.05)

        cm = ConfigManager(str(tmp_path))
        cm.get_restream_token_path()

        for name in YOUTUBE_AUTH_FILES:
            assert (tmp_path / name).stat().st_mtime == before[name]

    def test_save_email_config_does_not_touch_yt_auth(self, tmp_path):
        """save_email_config() must not modify any YouTube auth file."""
        for name in YOUTUBE_AUTH_FILES:
            (tmp_path / name).write_text("sentinel")
        before = {n: (tmp_path / n).stat().st_mtime for n in YOUTUBE_AUTH_FILES}
        time.sleep(0.05)

        cm = ConfigManager(str(tmp_path))
        cm.save_email_config({
            "connection_string": "test",
            "sender": "a@b.com",
            "recipient": "c@d.com",
        })

        for name in YOUTUBE_AUTH_FILES:
            assert (tmp_path / name).stat().st_mtime == before[name]

    def test_get_email_config_does_not_touch_yt_auth(self, tmp_path):
        """get_email_config() must not modify any YouTube auth file."""
        for name in YOUTUBE_AUTH_FILES:
            (tmp_path / name).write_text("sentinel")
        before = {n: (tmp_path / n).stat().st_mtime for n in YOUTUBE_AUTH_FILES}
        time.sleep(0.05)

        cm = ConfigManager(str(tmp_path))
        cm.get_email_config()

        for name in YOUTUBE_AUTH_FILES:
            assert (tmp_path / name).stat().st_mtime == before[name]

    def test_restream_token_path_is_not_yt_auth_file(self, tmp_path):
        """The Restream token path must not collide with YouTube auth file names."""
        cm = ConfigManager(str(tmp_path))
        restream_path = cm.get_restream_token_path()
        filename = restream_path.split("/")[-1] if "/" in restream_path else restream_path.split("\\")[-1]
        assert filename not in YOUTUBE_AUTH_FILES, (
            f"Restream token filename '{filename}' collides with YouTube auth file"
        )
