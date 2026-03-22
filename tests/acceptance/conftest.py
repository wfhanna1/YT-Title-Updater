"""Shared fixtures for acceptance tests."""

import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory for test isolation."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def titles_file(temp_config_dir):
    """Create a titles.txt with sample titles."""
    tf = temp_config_dir / "titles.txt"
    tf.write_text("Test Title One\nTest Title Two\nTest Title Three\n")
    return tf


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def cli_module():
    """Return the path to the CLI entry point."""
    return [sys.executable, "-m", "youtube_updater"]
