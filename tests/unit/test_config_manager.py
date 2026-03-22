import pytest
from youtube_updater.core.config_manager import ConfigManager


def test_default_config_dir_uses_platformdirs(mocker, tmp_path):
    mock_user_data = mocker.patch('platformdirs.user_data_dir', return_value=str(tmp_path))
    cm = ConfigManager()
    mock_user_data.assert_called_once_with("YTTitleUpdater", "YTTitleUpdater")
    assert cm.config_dir == tmp_path


def test_explicit_config_dir_overrides_platformdirs(mocker, tmp_path):
    mock_user_data = mocker.patch('platformdirs.user_data_dir')
    cm = ConfigManager(str(tmp_path))
    mock_user_data.assert_not_called()
    assert str(cm.config_dir) == str(tmp_path)


def test_config_dir_is_created_if_not_exists(tmp_path):
    custom = tmp_path / "custom_config"
    cm = ConfigManager(str(custom))
    assert custom.exists()


def test_get_file_paths_returns_correct_keys(tmp_path):
    cm = ConfigManager(str(tmp_path))
    paths = cm.get_file_paths()
    assert "titles_file" in paths
    assert "applied_titles_file" in paths
    assert "token_path" in paths
    assert "client_secrets_path" in paths
    assert "history_log" in paths


# --- Phase 1: Restream + email config methods ---


def test_get_restream_token_path_returns_path_under_config_dir(tmp_path):
    cm = ConfigManager(str(tmp_path))
    path = cm.get_restream_token_path()
    assert str(tmp_path) in path
    assert "restream_token.json" in path


def test_get_restream_token_path_is_stable(tmp_path):
    cm = ConfigManager(str(tmp_path))
    assert cm.get_restream_token_path() == cm.get_restream_token_path()


def test_ensure_restream_token_returns_false_when_missing(tmp_path):
    cm = ConfigManager(str(tmp_path))
    assert cm.ensure_restream_token() is False


def test_ensure_restream_token_returns_true_when_exists(tmp_path):
    cm = ConfigManager(str(tmp_path))
    token_path = cm.get_restream_token_path()
    with open(token_path, "w") as f:
        f.write("{}")
    assert cm.ensure_restream_token() is True


def test_save_email_config_writes_file(tmp_path):
    cm = ConfigManager(str(tmp_path))
    config = {
        "connection_string": "endpoint=...",
        "sender": "noreply@example.com",
        "recipient": "admin@example.com",
    }
    cm.save_email_config(config)
    assert (tmp_path / "email_config.json").exists()


def test_get_email_config_returns_none_when_missing(tmp_path):
    cm = ConfigManager(str(tmp_path))
    assert cm.get_email_config() is None


def test_get_email_config_returns_saved_data(tmp_path):
    cm = ConfigManager(str(tmp_path))
    config = {
        "connection_string": "endpoint=...",
        "sender": "noreply@example.com",
        "recipient": "admin@example.com",
    }
    cm.save_email_config(config)
    loaded = cm.get_email_config()
    assert loaded == config


def test_get_file_paths_includes_restream_token(tmp_path):
    cm = ConfigManager(str(tmp_path))
    paths = cm.get_file_paths()
    assert "restream_token_path" in paths


def test_save_email_config_sets_0o600_permissions(tmp_path):
    import os
    import stat
    cm = ConfigManager(str(tmp_path))
    cm.save_email_config({"connection_string": "secret", "sender": "a", "recipient": "b"})
    email_path = tmp_path / "email_config.json"
    mode = stat.S_IMODE(os.stat(email_path).st_mode)
    assert mode == 0o600, f"Expected 0o600 but got {oct(mode)}"


def test_save_email_config_raises_on_tampered_path(tmp_path):
    from youtube_updater.exceptions.custom_exceptions import ConfigError
    cm = ConfigManager(str(tmp_path))
    cm.email_config_path = str(tmp_path / "token.json")
    with pytest.raises(ConfigError):
        cm.save_email_config({"connection_string": "x", "sender": "a", "recipient": "b"})


def test_get_email_config_raises_on_corrupt_json(tmp_path):
    from youtube_updater.exceptions.custom_exceptions import ConfigError
    cm = ConfigManager(str(tmp_path))
    with open(tmp_path / "email_config.json", "w") as f:
        f.write("{corrupt json")
    with pytest.raises(ConfigError, match="corrupt"):
        cm.get_email_config()


def test_get_file_paths_includes_email_config(tmp_path):
    cm = ConfigManager(str(tmp_path))
    paths = cm.get_file_paths()
    assert "email_config_path" in paths
