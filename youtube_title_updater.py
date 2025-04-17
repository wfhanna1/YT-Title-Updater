#!/usr/bin/env python3
"""
YouTube Title Updater

A GUI application for automatically updating YouTube live stream titles.
"""

from youtube_updater import YouTubeUpdaterGUI
import tkinter as tk

def main():
    """Launch the YouTube Title Updater application."""
    root = tk.Tk()
    app = YouTubeUpdaterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 