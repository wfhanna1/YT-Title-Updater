import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_dir)

from youtube_updater.gui import YouTubeUpdaterGUI, QApplication
from youtube_updater.core import YouTubeUpdaterCore

if __name__ == "__main__":
    # Set up Windows-specific configurations
    os.environ["QT_QPA_PLATFORM"] = "windows"

    # Determine application directory (works for both bundled and script runs)
    if getattr(sys, 'frozen', False):
        application_path = Path(sys._MEIPASS)
    else:
        application_path = Path(__file__).parent.parent

    # Launch the application using the application directory as config
    app = QApplication([])
    core = YouTubeUpdaterCore(config_dir=str(application_path))
    window = YouTubeUpdaterGUI(core=core)
    window.show()
    app.exec()