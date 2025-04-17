# YouTube Live Title Updater

This app automatically updates your live stream title on YouTube using a list of titles from a file. It provides a user-friendly GUI interface for managing your stream titles and monitoring your live status.

---

## 🖥️ Features

- **Real-time Title Management**
  - View current and next stream titles
  - Edit titles list through the built-in text editor
  - Automatic title rotation after each update
  - Title archiving to track used titles

- **Live Status Monitoring**
  - Real-time detection of live stream status
  - Automatic title updates when going live
  - Manual title update option
  - Status indicators for connection and updates

- **User Interface**
  - Clean, modern GUI design
  - Current and next title display
  - Status messages with color coding
  - Quick access to configuration files
  - Menu bar integration (when built as app)

- **Configuration Management**
  - Easy access to titles file
  - Configurable title rotation
  - Automatic backup of used titles
  - Detailed history logging

---

## ✅ Setup Guide

### 1. **Enable YouTube API & Get Credentials**
- Go to: https://console.developers.google.com/
- Create a project and enable **YouTube Data API v3**
- Go to **Credentials** > Create **OAuth client ID** > Choose **Desktop App**
- Download the JSON file and **replace** the `client_secrets.json` in this folder

### 2. **Authorize Access to Your YouTube**
In Terminal, run:
```bash
cd ~/Documents/yt_title_updater
python3 auth_setup.py
```
- This opens a browser for you to log in and authorize
- It generates `token.pickle` (used for title updates)

### 3. **Edit Your Stream Titles**
Edit `titles.txt` to include your planned stream titles (one per line). The first unused title is used.

### 4. **Run the App**
To test run:
```bash
python3 youtube_title_updater.py
```

To build it into a menu bar app:
```bash
pip3 install py2app
python3 setup.py py2app
```

---

## 📁 File Structure
- `youtube_title_updater.py`: Main application entry point
- `youtube_updater/`: Core application package
  - `core.py`: Core functionality and YouTube API interaction
  - `gui.py`: GUI implementation
- `auth_setup.py`: Authentication handler
- `titles.txt`: Your stream titles
- `applied-titles.txt`: Archive of used titles
- `history.log`: Detailed update history
- `client_secrets.json`: Your YouTube API credentials

---

## 🎯 How It Works

1. **Title Management**
   - Titles are read from `titles.txt`
   - First unused title is selected as next title
   - After updating, used title is moved to `applied-titles.txt`
   - Next title in list becomes current title

2. **Live Detection**
   - App continuously monitors your YouTube channel
   - Automatically detects when you go live
   - Updates status in real-time

3. **Title Updates**
   - Manual update through "Update Title" button
   - Automatic updates when going live
   - All changes logged in `history.log`

4. **Configuration**
   - Access config files through menu options
   - Edit titles directly through built-in editor
   - View history and applied titles

---

## 🛠️ Troubleshooting

If you encounter issues:
1. Check your YouTube API credentials
2. Verify internet connection
3. Ensure you're logged into the correct YouTube account
4. Check the history.log for error messages
5. Verify file permissions in the config directory

---

## 📝 Notes
- The app requires an active internet connection
- YouTube API has rate limits - be mindful of update frequency
- All changes are logged for tracking and debugging
- The app can be run as a regular GUI or menu bar app


