import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_dir)

from youtube_updater.gui import main

if __name__ == "__main__":
    # Set up Windows-specific configurations
    os.environ["QT_QPA_PLATFORM"] = "windows"
    
    # Launch the application
    main() 