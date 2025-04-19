import sys
import os
from pathlib import Path

# Get the project root directory (parent of macos-app)
project_root = Path(__file__).parent.parent

# Add the src directory to the Python path if it exists
src_dir = project_root / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

from youtube_updater.gui import YouTubeUpdaterGUI, QApplication
from youtube_updater.core import YouTubeUpdaterCore

if __name__ == "__main__":
    # Set up macOS-specific configurations
    os.environ["QT_QPA_PLATFORM"] = "cocoa"
    
    # Get the application directory
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (pyinstaller)
        application_path = Path(sys._MEIPASS)
    else:
        # If the application is run as a script
        application_path = project_root  # Use project root instead of macos-app directory
    
    # Create and run the application
    app = QApplication([])
    core = YouTubeUpdaterCore(config_dir=str(application_path))  # Convert Path to string
    window = YouTubeUpdaterGUI(core=core)
    window.show()
    app.exec() 