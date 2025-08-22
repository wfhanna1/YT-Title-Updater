import os
from typing import List, Optional
from datetime import datetime
from .default_title_generator import DefaultTitleGenerator

class TitleManager:
    """Manages YouTube video titles."""
    
    def __init__(self, titles_file: str, applied_titles_file: str, history_log: str):
        """Initialize the title manager.
        
        Args:
            titles_file: Path to the titles file
            applied_titles_file: Path to the applied titles file
            history_log: Path to the history log file
        """
        self.titles_file = titles_file
        self.applied_titles_file = applied_titles_file
        self.history_log = history_log
        self.titles: List[str] = []
        self.next_title: Optional[str] = None
        
        # Initialize the sophisticated title generator
        self.default_generator = DefaultTitleGenerator()
        
        # Create files if they don't exist
        self._ensure_files_exist()
        self.load_titles()
    
    def _ensure_files_exist(self) -> None:
        """Ensure all required files exist."""
        for file_path in [self.titles_file, self.applied_titles_file, self.history_log]:
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write("")
    
    def load_titles(self) -> None:
        """Load titles from the titles file."""
        try:
            if os.path.exists(self.titles_file):
                with open(self.titles_file, "r") as f:
                    self.titles = [line.strip() for line in f if line.strip()]
                    self.next_title = self.titles[0] if self.titles else None
            else:
                self.titles = []
                self.next_title = None
        except Exception as e:
            print(f"Error loading titles: {str(e)}")
    
    def _read_lines(self, file_path: str) -> List[str]:
        """Read lines from a file."""
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    return [line.strip() for line in f if line.strip()]
            return []
        except Exception:
            return []
    
    def _write_lines(self, file_path: str, lines: List[str]) -> None:
        """Write lines to a file."""
        try:
            with open(file_path, "w") as f:
                f.write("\n".join(lines) + "\n" if lines else "")
        except Exception as e:
            print(f"Error writing to {file_path}: {str(e)}")
    
    def _append_line(self, file_path: str, line: str) -> None:
        """Append a line to a file."""
        try:
            with open(file_path, "a") as f:
                f.write(line + "\n")
        except Exception as e:
            print(f"Error appending to {file_path}: {str(e)}")
    
    def _get_current_time(self) -> str:
        """Get the current time in a formatted string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _generate_default_title(self) -> str:
        """Generate a sophisticated default title based on current time and day."""
        return self.default_generator.generate_title()
    
    def get_next_title(self) -> Optional[str]:
        """Get the next title in the rotation.
        
        Returns:
            Optional[str]: Next title to use, or None if no titles available
        """
        titles = self._read_lines(self.titles_file)
        if not titles:
            return self._generate_default_title()
        
        # Get the first title and move it to the end
        next_title = titles[0]
        titles = titles[1:] + [next_title]
        self._write_lines(self.titles_file, titles)
        return next_title
    
    def rotate_titles(self) -> Optional[str]:
        """Rotate to the next title in the list.
        
        Returns:
            Optional[str]: The title that was just used, or None if no titles available
        """
        titles = self._read_lines(self.titles_file)
        if not titles:
            self.next_title = None
            return None
        
        # Store the current title before rotation
        current = titles[0]
        
        # Rotate the list
        titles = titles[1:] + [titles[0]]
        
        # Update next_title to the new first title
        self.next_title = titles[0]
        
        # Update titles file
        self._write_lines(self.titles_file, titles)
        
        return current
    
    def archive_title(self, title: str) -> None:
        """Archive a used title.
        
        Args:
            title: Title to archive
        """
        self._append_line(self.applied_titles_file, title)
        self._append_line(self.history_log, f"{title} - {self._get_current_time()}")
    
    def add_title(self, title: str) -> None:
        """Add a new title to the list.
        
        Args:
            title: Title to add
        """
        titles = self._read_lines(self.titles_file)
        titles.append(title)
        self._write_lines(self.titles_file, titles) 