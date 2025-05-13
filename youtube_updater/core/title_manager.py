import os
from typing import List, Optional
from datetime import datetime
from ..exceptions.custom_exceptions import TitleManagerError

class TitleManager:
    """Manages YouTube video titles."""
    
    DEFAULT_TITLE = "Live Stream"
    
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
        self.next_title: str = self.DEFAULT_TITLE
        
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
                    if self.titles:
                        self.next_title = self.titles[0]
                    else:
                        self._create_default_titles()
            else:
                self._create_default_titles()
                
        except Exception as e:
            raise TitleManagerError(f"Error loading titles: {str(e)}")
    
    def _create_default_titles(self) -> None:
        """Create titles file with default title."""
        self.titles = [self.DEFAULT_TITLE]
        self.next_title = self.DEFAULT_TITLE
        with open(self.titles_file, "w") as f:
            f.write(f"{self.DEFAULT_TITLE}\n")
    
    def get_next_title(self) -> str:
        """Get the next title in the rotation.
        
        Returns:
            str: Next title to use
        """
        return self.next_title
    
    def rotate_titles(self) -> str:
        """Rotate to the next title in the list.
        
        Returns:
            str: The title that was just used
        """
        if not self.titles:
            self._create_default_titles()
            return self.DEFAULT_TITLE
            
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
        """Archive a title that has been used.
        
        Args:
            title: Title to archive
            
        Raises:
            TitleManagerError: If archiving fails
        """
        try:
            # Add to applied titles file
            with open(self.applied_titles_file, "a") as f:
                f.write(f"{title}\n")
            
            # Add to history log with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.history_log, "a") as f:
                f.write(f"{timestamp}: {title}\n")
            
            # Remove from titles list if it exists
            if title in self.titles:
                self.titles.remove(title)
                # Update titles file
                with open(self.titles_file, "w") as f:
                    f.write("\n".join(self.titles) + "\n" if self.titles else "")
                    
        except Exception as e:
            raise TitleManagerError(f"Error archiving title: {str(e)}")
    
    def add_title(self, title: str) -> None:
        """Add a new title to the list.
        
        Args:
            title: Title to add
            
        Raises:
            TitleManagerError: If adding title fails
        """
        try:
            if title not in self.titles:
                self.titles.append(title)
                with open(self.titles_file, "a") as f:
                    f.write(f"{title}\n")
                    
        except Exception as e:
            raise TitleManagerError(f"Error adding title: {str(e)}") 