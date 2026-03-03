import os
import subprocess
import sys
from pathlib import Path
from typing import Union


def open_path(path: Union[str, Path]) -> None:
    """Open a file or directory in the OS default handler.

    Args:
        path: The file or directory path to open.
    """
    path_str = str(path)
    if sys.platform == 'darwin':
        subprocess.run(['open', path_str], check=True)
    elif sys.platform == 'win32':
        os.startfile(path_str)
    else:
        subprocess.run(['xdg-open', path_str], check=True)
