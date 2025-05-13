import os
from typing import List, Optional
from datetime import datetime
from ..exceptions.custom_exceptions import TitleManagerError
from .interfaces import ITitleManager
from .default_title_generator import DefaultTitleGenerator
from ..utils.file_operations import FileOperations

class TitleManager(ITitleManager):
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
        self.file_ops = FileOperations()
        self.default_generator = DefaultTitleGenerator()
        self.titles: List[str] = []
        self.next_title: Optional[str] = None
        
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
        """Load titles from the titles file.
        
        Raises:
            TitleManagerError: If titles cannot be loaded
        """
        try:
            if os.path.exists(self.titles_file):
                with open(self.titles_file, "r") as f:
                    self.titles = [line.strip() for line in f if line.strip()]
                    self.next_title = self.titles[0] if self.titles else None
            else:
                self.titles = []
                self.next_title = None
        except Exception as e:
            raise TitleManagerError(f"Error loading titles: {str(e)}")
    
    def get_next_title(self) -> Optional[str]:
        """Get the next title in the rotation.
        
        Returns:
            Optional[str]: Next title to use, or None if no titles available
        """
        titles = self.file_ops.read_lines(self.titles_file)
        if not titles:
            return self.default_generator.generate_title()
        
        # Get the first title and move it to the end
        next_title = titles[0]
        titles = titles[1:] + [next_title]
        self.file_ops.write_lines(self.titles_file, titles)
        return next_title
    
    def rotate_titles(self) -> Optional[str]:
        """Rotate to the next title in the list.
        
        Returns:
            Optional[str]: The title that was just used, or None if no titles available
        """
        if not self.titles:
            self.next_title = None
            return None
        # Store the current title before rotation
        current = self.titles[0]
        
        # Rotate the list
        self.titles.append(self.titles.pop(0))
        
        # Update next_title to the new first title
        self.next_title = self.titles[0]
        
        # Update titles file
        with open(self.titles_file, "w") as f:
            f.write("\n".join(self.titles) + "\n" if self.titles else "")
            
        return current
    
    def archive_title(self, title: str) -> None:
        """Archive a used title.
        
        Args:
            title: Title to archive
        """
        self.file_ops.append_line(self.applied_titles_file, title)
        self.file_ops.append_line(self.history_log, f"{title} - {self.file_ops.get_current_time()}")
    
    def add_title(self, title: str) -> None:
        """Add a new title to the list.
        
        Args:
            title: Title to add
        """
        titles = self.file_ops.read_lines(self.titles_file)
        titles.append(title)
        self.file_ops.write_lines(self.titles_file, titles) 