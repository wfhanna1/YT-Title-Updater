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
