"""Unit tests for ComponentFactory."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from youtube_updater.core.factory import ComponentFactory
from youtube_updater.exceptions.custom_exceptions import AuthenticationError


def test_factory_returns_core_without_youtube_client_when_no_secrets(tmp_path):
    """When client_secrets.json is absent the factory must succeed and leave
    youtube_client as None rather than crashing."""
    core = ComponentFactory.create_core(str(tmp_path))
    assert core.youtube_client is None


def test_factory_returns_core_without_youtube_client_when_credentials_invalid(tmp_path):
    """When client_secrets.json exists but is malformed / causes an auth error,
    the factory must not crash -- it should fall back to youtube_client=None."""
    secrets = tmp_path / "client_secrets.json"
    secrets.write_text("{bad json}")  # intentionally malformed

    core = ComponentFactory.create_core(str(tmp_path))
    assert core.youtube_client is None


def test_factory_returns_core_with_youtube_client_when_credentials_valid(tmp_path, mocker):
    """When client_secrets.json exists and credentials are obtained successfully,
    youtube_client should be set."""
    secrets = tmp_path / "client_secrets.json"
    secrets.write_text("{}")

    mock_creds = MagicMock()
    mocker.patch(
        "youtube_updater.core.factory.AuthManager.get_credentials",
        return_value=mock_creds,
    )
    mock_client_cls = mocker.patch("youtube_updater.core.factory.YouTubeClient")

    core = ComponentFactory.create_core(str(tmp_path))
    assert core.youtube_client is not None
