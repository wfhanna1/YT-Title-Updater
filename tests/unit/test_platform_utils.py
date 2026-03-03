import pytest
from youtube_updater.utils.platform_utils import open_path


def test_open_path_macos(mocker):
    mocker.patch('sys.platform', 'darwin')
    mock_run = mocker.patch('subprocess.run')
    open_path('/some/path')
    mock_run.assert_called_once_with(['open', '/some/path'], check=True)


def test_open_path_windows(mocker):
    mocker.patch('sys.platform', 'win32')
    mock_startfile = mocker.patch('os.startfile', create=True)
    open_path('/some/path')
    mock_startfile.assert_called_once_with('/some/path')


def test_open_path_linux(mocker):
    mocker.patch('sys.platform', 'linux')
    mock_run = mocker.patch('subprocess.run')
    open_path('/some/path')
    mock_run.assert_called_once_with(['xdg-open', '/some/path'], check=True)
