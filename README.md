# YouTube Live Title Updater (Mac Menu Bar App)

This app automatically updates your live stream title on YouTube using a list of titles from a file.

---

## ✅ What You Need to Do (Quick Recap)

### 1. **Enable YouTube API & Get Credentials**
- Go to: https://console.developers.google.com/
- Create a project and enable **YouTube Data API v3**
- Go to **Credentials** > Create **OAuth client ID** > Choose **Desktop App**
- Download the JSON file and **replace** the `client_secrets.json` in this folder

---

### 2. **Authorize Access to Your YouTube**
In Terminal, run:
```bash
cd ~/Documents/yt_title_updater
python3 auth_setup.py
```
- This opens a browser for you to log in and authorize
- It generates `token.pickle` (used for title updates)

---

### 3. **Edit Your Stream Titles**
Edit `titles.txt` to include your planned stream titles (one per line). The first unused title is used.

---

### 4. **Run the App**
To test run:
```bash
python3 youtube_menu_bar_app.py
```

To build it into a menu bar app:
```bash
pip3 install py2app
python3 setup.py py2app
```

---

## 📁 What's in the Zip
- `youtube_menu_bar_app.py`: Main app (menu bar GUI)
- `auth_setup.py`: Auth handler with refresh token support
- `titles.txt`: Your stream titles
- `history.log`: Log of updates
- `client_secrets.json`: Sample file (replace with your own from Google)

---

## 🧠 Behavior Summary
- Auto-detects your current YouTube Live stream
- Updates the stream title using the next available title from `titles.txt`
- Logs what was changed in `history.log`
- If `titles.txt` is empty, defaults to **Live Stream**
- App preview shows the current and next title
- Menu option: **Open Titles Folder** (to quickly update your titles)

Let me know if you need a version that syncs from Google Sheets, Dropbox, or an `.app` installer.

—Built for Mac Mini local streaming setup 🎬
