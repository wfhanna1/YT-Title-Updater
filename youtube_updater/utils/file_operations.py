import os
from typing import List, Optional
from pathlib import Path
from datetime import datetime

class FileOperations:
    """Handles all file operations for the application."""
    
    @staticmethod
    def ensure_file_exists(file_path: str) -> None:
        """Ensure a file exists, create it if it doesn't.
        
        Args:
            file_path: Path to the file
        """
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("")
    
    @staticmethod
    def read_lines(file_path: str) -> List[str]:
        """Read non-empty lines from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List[str]: List of non-empty lines
        """
        with open(file_path, "r") as f:
            return [line.strip() for line in f if line.strip()]
    
    @staticmethod
    def write_lines(file_path: str, lines: List[str]) -> None:
        """Write lines to a file.
        
        Args:
            file_path: Path to the file
            lines: List of lines to write
        """
        with open(file_path, "w") as f:
            f.write("\n".join(lines) + "\n" if lines else "")
    
    @staticmethod
    def append_line(file_path: str, line: str) -> None:
        """Append a line to a file.
        
        Args:
            file_path: Path to the file
            line: Line to append
        """
        with open(file_path, "a") as f:
            f.write(f"{line}\n")
    
    @staticmethod
    def create_directory(directory: str) -> None:
        """Create a directory if it doesn't exist.
        
        Args:
            directory: Path to the directory
        """
        os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def get_current_time() -> str:
        """Get the current timestamp as a string.
        
        Returns:
            str: Current timestamp in YYYY-MM-DD HH:MM:SS format
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S") 