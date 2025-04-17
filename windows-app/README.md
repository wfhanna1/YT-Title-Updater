# YouTube Title Updater - Windows Application

This folder contains the necessary files to build a Windows executable for the YouTube Title Updater application.

## Prerequisites

- Python 3.11 or later
- pip (Python package installer)
- Windows operating system

## Building the Executable

1. Open Command Prompt as Administrator
2. Navigate to this directory
3. Run the build script:
   ```
   build.bat
   ```

The executable will be created in the `dist` folder.

## Required Files

Make sure the following files are present in the root directory before building:
- `youtube_gui_app.py`
- `client_secrets.json`
- `token.pickle`
- `titles.txt`
- `icon.ico` (optional, for application icon)

## Using the Executable

1. Navigate to the `dist` folder
2. Run `YouTube Title Updater.exe`
3. The application will create necessary files in your Documents folder:
   - `~/Documents/yt_title_updater/titles.txt`
   - `~/Documents/yt_title_updater/token.pickle`
   - `~/Documents/yt_title_updater/client_secrets.json`

## Troubleshooting

If you encounter any issues:
1. Make sure all required files are present
2. Check that you have the correct Python version installed
3. Ensure you have administrator privileges when building
4. Verify that all dependencies are installed correctly 