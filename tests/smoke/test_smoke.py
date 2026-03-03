"""Smoke test harness for YT-Title-Updater.

These tests verify the most critical paths after any change:
  - CLI entry point launches, accepts subcommands, and exits cleanly
  - Title file operations (add, rotate, peek, archive) work end-to-end
  - ConfigManager creates the expected directory structure
  - All public modules import without error

No YouTube API calls are made. Tests use real temp files via tmp_path.

Run with:
    pytest tests/smoke/ -v
    pytest tests/smoke/ -v --tb=short   # concise tracebacks
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Invoke the same interpreter that is running the tests.
_PY = sys.executable
_MOD = "youtube_updater"
_ROOT = Path(__file__).parent.parent.parent


def _run(*args, config_dir=None):
    """Run `python -m youtube_updater [args]` and return CompletedProcess."""
    cmd = [_PY, "-m", _MOD]
    if config_dir is not None:
        cmd += ["--config-dir", str(config_dir)]
    cmd += list(args)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(_ROOT))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

class TestCLIEntryPoint:
    """The CLI must launch, accept known subcommands, and produce useful output."""

    def test_top_level_help_exits_zero(self):
        r = _run("--help")
        assert r.returncode == 0
        assert "update" in r.stdout
        assert "status" in r.stdout
        assert "auth" in r.stdout

    def test_update_help_exits_zero(self):
        r = _run("update", "--help")
        assert r.returncode == 0
        assert "--wait" in r.stdout
        assert "--wait-timeout" in r.stdout

    def test_status_help_exits_zero(self):
        r = _run("status", "--help")
        assert r.returncode == 0

    def test_auth_help_exits_zero(self):
        r = _run("auth", "--help")
        assert r.returncode == 0

    def test_auth_without_client_secrets_exits_nonzero(self, tmp_path):
        r = _run("auth", config_dir=tmp_path)
        assert r.returncode != 0
        assert "client_secrets.json" in r.stdout

    def test_no_subcommand_exits_nonzero(self):
        r = _run()
        assert r.returncode != 0

    def test_unknown_subcommand_exits_nonzero(self):
        r = _run("bogus-command")
        assert r.returncode != 0


# ---------------------------------------------------------------------------
# Behaviour without YouTube credentials
# ---------------------------------------------------------------------------

class TestCLINoCredentials:
    """CLI must degrade gracefully when client_secrets.json is absent.

    The factory skips YouTube client initialisation when client_secrets.json
    is missing, so `status` exits 0 and reports the error via the status
    line; `update` exits 1 because the stream is not live.
    """

    def test_status_without_credentials_exits_zero(self, tmp_path):
        r = _run("status", config_dir=tmp_path)
        assert r.returncode == 0
        assert "Not Live" in r.stdout or "not initialized" in r.stdout.lower()

    def test_update_without_credentials_exits_nonzero(self, tmp_path):
        r = _run("update", config_dir=tmp_path)
        assert r.returncode != 0

    def test_update_wait_flag_without_credentials_exits_nonzero(self, tmp_path):
        # --wait-timeout 5 keeps the test fast; 5 s is the maximum wait.
        r = _run("update", "--wait", "--wait-timeout", "5", config_dir=tmp_path)
        assert r.returncode != 0

    def test_status_output_contains_key_fields(self, tmp_path):
        r = _run("status", config_dir=tmp_path)
        assert "Live Status:" in r.stdout
        assert "Current Title:" in r.stdout
        assert "Next Title:" in r.stdout


# ---------------------------------------------------------------------------
# ConfigManager -- filesystem behaviour
# ---------------------------------------------------------------------------

class TestConfigManagerFileSystem:
    """ConfigManager must create the expected directory and file structure."""

    def _make(self, path):
        from youtube_updater.core.config_manager import ConfigManager
        return ConfigManager(str(path))

    def test_creates_config_dir_on_first_use(self, tmp_path):
        config_dir = tmp_path / "app_config"
        self._make(config_dir)
        assert config_dir.exists()

    def test_creates_required_files(self, tmp_path):
        cm = self._make(tmp_path)
        paths = cm.get_file_paths()
        assert Path(paths["titles_file"]).exists()
        assert Path(paths["applied_titles_file"]).exists()
        assert Path(paths["history_log"]).exists()

    def test_all_paths_are_under_config_dir(self, tmp_path):
        cm = self._make(tmp_path)
        for key, path in cm.get_file_paths().items():
            assert str(tmp_path) in path, f"{key} ({path}) is not under config_dir"

    def test_token_path_uses_json_extension(self, tmp_path):
        cm = self._make(tmp_path)
        assert cm.get_file_paths()["token_path"].endswith(".json")

    def test_no_client_secrets_returns_false(self, tmp_path):
        cm = self._make(tmp_path)
        assert cm.ensure_client_secrets() is False

    def test_explicit_config_dir_is_resolved(self, tmp_path):
        # A path with .. components must be resolved, not stored raw.
        resolved = str(tmp_path)
        cm = self._make(tmp_path / "sub" / "..")
        assert str(cm.config_dir) == resolved


# ---------------------------------------------------------------------------
# TitleManager -- file-based operations
# ---------------------------------------------------------------------------

class TestTitleManagerFileOperations:
    """TitleManager must read/write/rotate/peek titles correctly."""

    @pytest.fixture
    def mgr(self, tmp_path):
        from youtube_updater.core.title_manager import TitleManager
        return TitleManager(
            titles_file=str(tmp_path / "titles.txt"),
            applied_titles_file=str(tmp_path / "applied-titles.txt"),
            history_log=str(tmp_path / "history.log"),
        )

    def test_add_then_get_next(self, mgr):
        mgr.add_title("Alpha")
        assert mgr.get_next_title() == "Alpha"

    def test_get_next_rotates_to_end(self, mgr, tmp_path):
        (tmp_path / "titles.txt").write_text("A\nB\nC\n")
        mgr.load_titles()
        assert mgr.get_next_title() == "A"
        assert mgr.get_next_title() == "B"
        assert mgr.get_next_title() == "C"
        # Full rotation -- A is back at the front
        assert mgr.get_next_title() == "A"

    def test_peek_does_not_advance(self, mgr, tmp_path):
        (tmp_path / "titles.txt").write_text("X\nY\n")
        mgr.load_titles()
        assert mgr.peek_next_title() == "X"
        assert mgr.peek_next_title() == "X"
        # get_next also returns X (peek did not rotate)
        assert mgr.get_next_title() == "X"
        # Now Y is next
        assert mgr.peek_next_title() == "Y"

    def test_archive_writes_to_both_files(self, mgr, tmp_path):
        mgr.archive_title("My Title")
        assert "My Title" in (tmp_path / "applied-titles.txt").read_text()
        assert "My Title" in (tmp_path / "history.log").read_text()

    def test_empty_file_falls_back_to_default_generator(self, mgr):
        result = mgr.get_next_title()
        assert result is not None
        assert len(result) > 0

    def test_peek_empty_file_returns_none(self, mgr):
        assert mgr.peek_next_title() is None


# ---------------------------------------------------------------------------
# platform_utils
# ---------------------------------------------------------------------------

class TestPlatformUtils:
    """open_path must dispatch to the correct OS command."""

    def test_open_path_is_importable(self):
        from youtube_updater.utils.platform_utils import open_path
        assert callable(open_path)

    def test_open_path_macos(self, mocker):
        mocker.patch("sys.platform", "darwin")
        mock_run = mocker.patch("subprocess.run")
        from youtube_updater.utils.platform_utils import open_path
        open_path("/tmp/test")
        mock_run.assert_called_once_with(["open", "/tmp/test"], check=True)

    def test_open_path_windows(self, mocker):
        mocker.patch("sys.platform", "win32")
        mock_startfile = mocker.patch("os.startfile", create=True)
        from youtube_updater.utils.platform_utils import open_path
        open_path("/tmp/test")
        mock_startfile.assert_called_once_with("/tmp/test")

    def test_open_path_linux(self, mocker):
        mocker.patch("sys.platform", "linux")
        mock_run = mocker.patch("subprocess.run")
        from youtube_updater.utils.platform_utils import open_path
        open_path("/tmp/test")
        mock_run.assert_called_once_with(["xdg-open", "/tmp/test"], check=True)


# ---------------------------------------------------------------------------
# Import smoke
# ---------------------------------------------------------------------------

class TestImports:
    """Every public module must import without raising."""

    def test_package_has_version(self):
        import youtube_updater
        assert youtube_updater.__version__

    def test_core_public_api(self):
        from youtube_updater.core import (
            YouTubeUpdaterCore,
            TitleManager,
            ConfigManager,
            AuthManager,
            StatusManager,
            ComponentFactory,
        )

    def test_cli_importable(self):
        from youtube_updater.cli import YouTubeUpdaterCLI, main
        assert callable(main)

    def test_interfaces_importable(self):
        from youtube_updater.core.interfaces import (
            IYouTubeClient,
            IAuthManager,
            ITitleManager,
            IConfigManager,
        )

    def test_exceptions_importable(self):
        from youtube_updater.exceptions.custom_exceptions import (
            YouTubeUpdaterError,
            AuthenticationError,
        )
