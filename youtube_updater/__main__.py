import tkinter as tk
from .gui import YouTubeUpdaterGUI

def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = YouTubeUpdaterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 