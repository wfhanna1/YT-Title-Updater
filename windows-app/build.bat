@echo off
echo Installing required packages...
pip install pyinstaller

echo Building executable...
pyinstaller youtube_title_updater.spec

echo Done! The executable is in the dist folder.
pause 