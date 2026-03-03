import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from youtube_updater.core.auth_manager import AuthManager


def test_credentials_saved_as_json(mocker, tmp_path):
    token_path = tmp_path / "token.json"
    client_secrets_path = tmp_path / "client_secrets.json"

    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = None
    mock_creds.to_json.return_value = json.dumps({"token": "fake_token"})

    mock_flow = mocker.patch('youtube_updater.core.auth_manager.InstalledAppFlow')
    mock_flow.from_client_secrets_file.return_value.run_local_server.return_value = mock_creds

    client_secrets_path.write_text('{}')

    manager = AuthManager(str(client_secrets_path), str(token_path))
    manager._refresh_or_authenticate(None)

    assert token_path.exists()
    assert token_path.suffix == '.json'
    saved = json.loads(token_path.read_text())
    assert "token" in saved


def test_get_credentials_does_not_double_wrap_auth_error(mocker, tmp_path):
    """When _refresh_or_authenticate raises AuthenticationError, get_credentials
    must re-raise it unchanged rather than wrapping it a second time."""
    from youtube_updater.exceptions.custom_exceptions import AuthenticationError

    token_path = tmp_path / "token.json"
    client_secrets_path = tmp_path / "client_secrets.json"
    client_secrets_path.write_text("{}")

    manager = AuthManager(str(client_secrets_path), str(token_path))
    # Simulate the message _refresh_or_authenticate produces, which already
    # contains "Authentication failed".
    mocker.patch.object(
        manager,
        "_refresh_or_authenticate",
        side_effect=AuthenticationError("Authentication failed: bad json"),
    )

    with pytest.raises(AuthenticationError) as exc_info:
        manager.get_credentials()

    msg = str(exc_info.value)
    assert "bad json" in msg
    # Must not say "Authentication failed" twice.
    assert msg.count("Authentication failed") == 1


def test_credentials_loaded_from_json(mocker, tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps({"token": "fake_token", "scopes": []}))

    mock_from_info = mocker.patch(
        'youtube_updater.core.auth_manager.Credentials.from_authorized_user_info'
    )
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_from_info.return_value = mock_creds

    manager = AuthManager("client_secrets.json", str(token_path))
    result = manager._load_credentials()

    mock_from_info.assert_called_once_with({"token": "fake_token", "scopes": []})
    assert result == mock_creds
