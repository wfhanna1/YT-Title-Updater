"""Real E2E subprocess tests for Restream CLI commands.

These tests create actual config files and token files on disk, set real
env vars, and invoke the CLI via subprocess. No Python-level mocking.
"""

import json
import os
import subprocess
import sys
import time


def _run_cli(*args, env_extra=None, config_dir=None):
    """Run the CLI via subprocess with optional env vars and config dir."""
    cmd = [sys.executable, "-m", "youtube_updater"]
    if config_dir:
        cmd.extend(["--config-dir", str(config_dir)])
    cmd.extend(args)

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    # Clear any inherited Restream/ACS env vars to avoid test pollution
    for key in ["RESTREAM_CLIENT_ID", "RESTREAM_CLIENT_SECRET",
                "ACS_CONNECTION_STRING", "ACS_SENDER", "ACS_RECIPIENTS"]:
        if key not in (env_extra or {}):
            env.pop(key, None)

    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)


def _write_restream_token(config_dir, expired=False):
    """Write a fake restream_token.json to the config dir."""
    token = {
        "access_token": "fake_access_token",
        "refresh_token": "fake_refresh_token",
        "client_id": "fake_client_id",
        "expires_at": time.time() + (-100 if expired else 3600),
    }
    token_path = config_dir / "restream_token.json"
    token_path.write_text(json.dumps(token))
    return token_path


class TestRestreamStatusE2E:
    """E2E tests for restream-status via subprocess."""

    def test_no_token_file_exits_1(self, tmp_path):
        r = _run_cli("restream-status", config_dir=tmp_path)
        assert r.returncode == 1
        assert "restream-auth" in r.stderr

    def test_valid_token_no_secret_succeeds_or_fails_gracefully(self, tmp_path):
        """With a valid (non-expired) token and no secret, should attempt API call."""
        _write_restream_token(tmp_path, expired=False)
        r = _run_cli("restream-status", config_dir=tmp_path)
        # Should NOT fail with "RESTREAM_CLIENT_SECRET" error
        assert "RESTREAM_CLIENT_SECRET" not in r.stderr

    def test_expired_token_no_secret_shows_secret_error(self, tmp_path):
        """With expired token and no secret, should say secret is needed."""
        _write_restream_token(tmp_path, expired=True)
        r = _run_cli("restream-status", config_dir=tmp_path)
        assert r.returncode == 1
        assert "RESTREAM_CLIENT_SECRET" in r.stderr


class TestUpdateRestreamE2E:
    """E2E tests for update --mode restream via subprocess."""

    def test_no_creds_exits_1_with_clear_error(self, tmp_path):
        r = _run_cli("update", "--mode", "restream", config_dir=tmp_path)
        assert r.returncode == 1
        assert "restream-auth" in r.stderr

    def test_dry_run_with_valid_token_shows_title(self, tmp_path):
        """Dry run with valid token and env vars shows the title."""
        _write_restream_token(tmp_path, expired=False)
        (tmp_path / "titles.txt").write_text("E2E Test Title\nSecond Title\n")

        r = _run_cli(
            "update", "--mode", "restream", "--dry-run",
            config_dir=tmp_path,
            env_extra={"RESTREAM_CLIENT_SECRET": "fake_secret"},
        )
        assert r.returncode == 0
        assert "E2E Test Title" in r.stdout
        assert "DRY RUN" in r.stdout

    def test_dry_run_empty_titles_uses_default_generator(self, tmp_path):
        """Dry run with empty titles.txt shows default generated title."""
        _write_restream_token(tmp_path, expired=False)

        r = _run_cli(
            "update", "--mode", "restream", "--dry-run",
            config_dir=tmp_path,
            env_extra={"RESTREAM_CLIENT_SECRET": "fake_secret"},
        )
        assert r.returncode == 0
        assert "DRY RUN" in r.stdout
        # Default title contains a day name
        output = r.stdout
        assert any(day in output for day in [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ])

    def test_dry_run_does_not_modify_files(self, tmp_path):
        """Dry run must not rotate titles or write to applied-titles.txt."""
        _write_restream_token(tmp_path, expired=False)
        titles_content = "Title A\nTitle B\n"
        (tmp_path / "titles.txt").write_text(titles_content)

        r = _run_cli(
            "update", "--mode", "restream", "--dry-run",
            config_dir=tmp_path,
            env_extra={"RESTREAM_CLIENT_SECRET": "fake_secret"},
        )
        assert r.returncode == 0
        # titles.txt unchanged
        assert (tmp_path / "titles.txt").read_text() == titles_content
        # applied-titles.txt empty or not created
        applied = tmp_path / "applied-titles.txt"
        if applied.exists():
            assert applied.read_text().strip() == ""

    def test_dry_run_without_secret_env_var_valid_token(self, tmp_path):
        """Dry run with valid token should work without RESTREAM_CLIENT_SECRET."""
        _write_restream_token(tmp_path, expired=False)
        (tmp_path / "titles.txt").write_text("No Secret Title\n")

        r = _run_cli(
            "update", "--mode", "restream", "--dry-run",
            config_dir=tmp_path,
        )
        assert r.returncode == 0
        assert "No Secret Title" in r.stdout

    def test_mode_youtube_default(self, tmp_path):
        """update without --mode defaults to youtube (not restream)."""
        r = _run_cli("update", config_dir=tmp_path)
        # Should fail with YouTube error, not Restream error
        assert "restream-auth" not in r.stderr


class TestEmailE2E:
    """E2E tests for email commands via subprocess."""

    def test_test_email_no_config_exits_1(self, tmp_path):
        r = _run_cli("test-email", config_dir=tmp_path)
        assert r.returncode == 1
        assert "configure-email" in r.stderr or "ACS_CONNECTION_STRING" in r.stderr

    def test_test_email_bad_creds_shows_error(self, tmp_path):
        """test-email with bad credentials should show the actual error, not generic message."""
        r = _run_cli(
            "test-email",
            config_dir=tmp_path,
            env_extra={
                "ACS_CONNECTION_STRING": "endpoint=https://fake.invalid/;accesskey=badkey",
                "ACS_SENDER": "noreply@fake.azurecomm.net",
                "ACS_RECIPIENTS": "test@example.com",
            },
        )
        assert r.returncode == 1
        # Should show actual error, not just "Failed to send"
        assert len(r.stderr) > 20  # More than a generic message

    def test_test_email_with_env_vars_attempts_send(self, tmp_path):
        """test-email picks up ACS env vars (will fail with fake creds but should try)."""
        r = _run_cli(
            "test-email",
            config_dir=tmp_path,
            env_extra={
                "ACS_CONNECTION_STRING": "endpoint=https://fake.invalid/;accesskey=badkey",
                "ACS_SENDER": "noreply@fake.azurecomm.net",
                "ACS_RECIPIENTS": "test@example.com",
            },
        )
        # Should attempt to send (exit 1 because fake creds, but NOT "not configured")
        assert "configure-email" not in r.stderr


class TestCLIHelpE2E:
    """Verify all commands appear in help and new flags are present."""

    def test_all_commands_in_help(self):
        r = _run_cli("--help")
        assert r.returncode == 0
        for cmd in ["update", "status", "auth", "restream-auth",
                     "restream-status", "configure-email", "test-email"]:
            assert cmd in r.stdout, f"Command '{cmd}' missing from --help"

    def test_update_has_all_flags(self):
        r = _run_cli("update", "--help")
        assert r.returncode == 0
        for flag in ["--mode", "--wait", "--wait-timeout", "--dry-run"]:
            assert flag in r.stdout, f"Flag '{flag}' missing from update --help"
