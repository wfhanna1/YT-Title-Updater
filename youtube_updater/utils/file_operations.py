import os
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from ..core.interfaces import IFileOperations

class FileOperations(IFileOperations):
    """Handles file operations for the application."""
    
    def ensure_file_exists(self, file_path: str, default_content: str = "") -> None:
        """Ensure a file exists, create it with default content if it doesn't.
        
        Args:
            file_path: Path to the file
            default_content: Default content to write if file doesn't exist
        """
        try:
            with open(file_path, "a+") as f:
                if f.tell() == 0:  # File is empty
                    f.write(default_content)
        except Exception as e:
            raise IOError(f"Error ensuring file exists: {str(e)}")
    
    def read_lines(self, file_path: str) -> List[str]:
        """Read lines from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List[str]: List of lines from the file
        """
        try:
            with open(file_path, "r") as f:
                return [line.strip() for line in f.readlines()]
        except Exception as e:
            raise IOError(f"Error reading file: {str(e)}")
    
    def write_lines(self, file_path: str, lines: List[str]) -> None:
        """Write lines to a file.
        
        Args:
            file_path: Path to the file
            lines: List of lines to write
        """
        try:
            with open(file_path, "w") as f:
                f.write("\n".join(lines))
        except Exception as e:
            raise IOError(f"Error writing to file: {str(e)}")
    
    def append_line(self, file_path: str, line: str) -> None:
        """Append a line to a file.
        
        Args:
            file_path: Path to the file
            line: Line to append
        """
        try:
            with open(file_path, "a") as f:
                f.write(f"{line}\n")
        except Exception as e:
            raise IOError(f"Error appending to file: {str(e)}")
    
    def get_current_time(self) -> str:
        """Get the current time in a formatted string.
        
        Returns:
            str: Formatted time string
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def create_directory(directory: str) -> None:
        """Create a directory if it doesn't exist.
        
        Args:
            directory: Path to the directory
        """
        os.makedirs(directory, exist_ok=True) 