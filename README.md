# YouTube Live Title Updater

A command-line tool that automatically updates your live stream title when you go live in OBS. Supports both YouTube (via YouTube Data API v3) and Restream (via Restream API, updating all connected platforms at once). Titles are read from a plain text file, rotated after each use, and archived so you never repeat one by accident.

---

## How It Works

1. You maintain a `titles.txt` file with one title per line.
2. When you start streaming in OBS, the tool waits until the broadcast is active (typically 30-60 seconds), applies the first title in the list, then moves it to the end so the next stream gets a fresh title.
3. If `titles.txt` is empty, a default title is generated based on the current date and time (e.g. "Sunday, March 22, 2026 - Divine Liturgy").
4. Every applied title is logged to `applied-titles.txt` and `history.log`.

---

## Installation

### Requirements

- Python 3.9 or later (for building only -- the compiled binary runs standalone)
- [PyInstaller](https://pyinstaller.org) 5.0+

> **Important:** You must build on the same OS you plan to run the binary on.
> PyInstaller does not cross-compile -- a Windows `.exe` must be built on
> Windows, a macOS binary must be built on macOS.

### Building on Windows

Open **Command Prompt** or **PowerShell**:

```bat
:: Clone the repo
git clone https://github.com/wfhanna1/YT-Title-Updater.git
cd YT-Title-Updater

:: Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

:: Install dependencies
pip install -r requirements.txt

:: Build the binary
pyinstaller yt-title-updater.spec
```

Output: `dist\yt-title-updater.exe`

Copy it to a permanent location, for example `C:\Tools\yt-title-updater.exe`.
You can add `C:\Tools` to your system PATH, or point the OBS script directly
to the full path.

### Building on macOS

Open **Terminal**:

```bash
# Clone the repo
git clone https://github.com/wfhanna1/YT-Title-Updater.git
cd YT-Title-Updater

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build the binary
pyinstaller yt-title-updater.spec
```

Output: `dist/yt-title-updater`

Copy it to a permanent location:

```bash
cp dist/yt-title-updater /usr/local/bin/
```

> **macOS Gatekeeper note:** Because the binary is not signed, macOS may block
> it the first time. Go to **System Settings > Privacy & Security** and click
> **Allow Anyway**, or run:
> ```bash
> xattr -d com.apple.quarantine /usr/local/bin/yt-title-updater
> ```

### Verifying the build

After building, confirm the binary works:

```bash
yt-title-updater --help
```

You should see the list of subcommands (`update`, `status`, `auth`, `restream-auth`, `restream-status`, `configure-email`, `test-email`).

---

## First-Time Setup

### YouTube Mode (default)

#### 1. Create YouTube API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **YouTube Data API v3**.
3. Go to **Credentials > Create credentials > OAuth client ID**.
4. Choose **Desktop app**, download the JSON file.
5. Rename it `client_secrets.json`.

#### 2. Place client_secrets.json in the config directory

Run the auth command to find out where the config directory is:

```bash
yt-title-updater auth
```

If `client_secrets.json` is missing, the output will tell you the exact path to copy it to:

```
Config directory: C:\Users\YourName\AppData\Roaming\YTTitleUpdater\YTTitleUpdater
client_secrets.json not found.
Download it from the Google Cloud Console and copy it to:
  C:\Users\YourName\AppData\Roaming\YTTitleUpdater\YTTitleUpdater\client_secrets.json
```

Copy the file there, then run `yt-title-updater auth` again. A browser window will open for you to log in and authorize access to your YouTube account. On success, `token.json` is saved to the same directory and you will not need to repeat this step.

**Config directory locations:**

| OS | Path |
|---|---|
| Windows | `%APPDATA%\YTTitleUpdater\YTTitleUpdater\` |
| macOS | `~/Library/Application Support/YTTitleUpdater/YTTitleUpdater/` |

### Restream Mode

Restream mode updates the stream title across all your connected platforms (YouTube, Facebook, Instagram, etc.) via the Restream API.

#### 1. Create Restream API credentials

1. Go to [Restream Developer Portal](https://developers.restream.io/).
2. Create an application.
3. Note the **Client ID** and **Client Secret**.
4. Set the redirect URI to `http://localhost:9451/callback`.

#### 2. Set environment variables

```bash
# Required for Restream
export RESTREAM_CLIENT_ID="your-client-id"
export RESTREAM_CLIENT_SECRET="your-client-secret"
```

These are required every time you run the tool in Restream mode. The client secret is not stored on disk for security.

#### 3. Authenticate with Restream

```bash
yt-title-updater restream-auth
```

A browser window will open for you to authorize access. On success, `restream_token.json` is saved with restricted permissions (owner-only read/write).

#### 4. Verify connectivity

```bash
# List connected platforms
yt-title-updater restream-status

# Dry run (shows what title would be applied, without making changes)
yt-title-updater update --mode restream --dry-run
```

### Email Notifications (optional)

Configure email alerts for authentication failures. This is useful for headless/OBS-automated runs where you won't see error output.

#### Option A: Environment variables

```bash
export ACS_CONNECTION_STRING="endpoint=https://your-resource.communication.azure.com/;accesskey=..."
export ACS_SENDER="DoNotReply@your-domain.azurecomm.net"
export ACS_RECIPIENTS="admin@example.com;backup@example.com"
```

#### Option B: Interactive configuration

```bash
# Save configuration
yt-title-updater configure-email

# Verify it works
yt-title-updater test-email
```

Email notifications use Azure Communication Services. They are best-effort -- if sending fails, the tool continues normally.

### 3. Add your stream titles

Open `titles.txt` in the config directory and add your planned titles, one per line:

```
Episode 12 - Getting Started With Rust
Episode 13 - Ownership and Borrowing
Episode 14 - Lifetimes Explained
```

The first line is always used next. After each successful update it moves to the end of the file. If `titles.txt` is empty, a default title is generated based on the day and time.

---

## Usage

```bash
# Check if the channel is live and show the next title
yt-title-updater status

# Update the title on YouTube (default mode)
yt-title-updater update

# Update the title on all Restream platforms
yt-title-updater update --mode restream

# Dry run -- show what would happen without making changes
yt-title-updater update --mode restream --dry-run

# Wait up to 90 seconds for the stream to go live, then update
yt-title-updater update --wait
yt-title-updater update --mode restream --wait

# Wait up to 2 minutes
yt-title-updater update --wait --wait-timeout 120

# Run YouTube OAuth setup (first time only)
yt-title-updater auth

# Run Restream OAuth setup (first time only)
yt-title-updater restream-auth

# List connected Restream platforms
yt-title-updater restream-status

# Configure email notifications
yt-title-updater configure-email

# Send a test email
yt-title-updater test-email

# Use a custom config directory
yt-title-updater --config-dir /path/to/config status
```

---

## OBS Integration

The Lua script in `obs_scripts/youtube_title_updater.lua` hooks into OBS and runs the title update automatically when you start streaming.

### Setup

1. In OBS, go to **Tools > Scripts**.
2. Click **+** and select `obs_scripts/youtube_title_updater.lua`.
3. In the script settings:
   - **Mode**: choose **YouTube** (default) or **Restream**.
   - **Binary Path**: full path to `yt-title-updater.exe` (Windows) or `yt-title-updater` (macOS).
   - **Wait Timeout**: seconds to wait for the broadcast to become active (default: 90). Increase if your stream takes longer to appear.
   - **Config Directory**: leave blank to use the default, or enter a custom path if you used `--config-dir` during setup.

### How it fires

When OBS starts streaming (`OBS_FRONTEND_EVENT_STREAMING_STARTED`), the script runs:

```
yt-title-updater update --mode <youtube|restream> --wait --wait-timeout <N>
```

in the background. OBS is not blocked. The tool polls every 10 seconds until the broadcast is active, then applies the next title from your list.

### Restream mode in OBS

For Restream mode, the `RESTREAM_CLIENT_ID` and `RESTREAM_CLIENT_SECRET` environment variables must be set in the environment where OBS runs. On macOS, this means setting them in your shell profile (`~/.zshrc` or `~/.bash_profile`) before launching OBS. On Windows, set them as system environment variables.

---

## Environment Variables

| Variable | Required for | Description |
|---|---|---|
| `RESTREAM_CLIENT_ID` | Restream mode | Restream OAuth client ID |
| `RESTREAM_CLIENT_SECRET` | Restream mode | Restream OAuth client secret (not stored on disk) |
| `ACS_CONNECTION_STRING` | Email notifications | Azure Communication Services connection string |
| `ACS_SENDER` | Email notifications | Sender email address |
| `ACS_RECIPIENTS` | Email notifications | Recipient addresses (semicolon-separated) |

Environment variables take priority over config file values.

---

## File Reference

All files are in the config directory (see paths above).

| File | Purpose |
|---|---|
| `client_secrets.json` | YouTube OAuth credentials (you provide this) |
| `token.json` | YouTube OAuth token (generated by `auth`, do not share) |
| `restream_token.json` | Restream OAuth token (generated by `restream-auth`, do not share) |
| `email_config.json` | Email notification settings (generated by `configure-email`) |
| `titles.txt` | Your upcoming stream titles, one per line |
| `applied-titles.txt` | Titles that have been applied |
| `history.log` | Timestamped log of every title update |

---

## Troubleshooting

**`auth` command opens a browser but shows an error**
Make sure the OAuth client ID type is **Desktop app**, not Web app.

**`update` exits immediately with "Not currently live streaming"**
YouTube's API takes 30-60 seconds to report a new broadcast as active. Use `--wait` to have the tool retry automatically.

**Title is not updating even though the stream is live**
Run `yt-title-updater status` to check whether the YouTube client is initialized. If it prints `not initialized`, `client_secrets.json` is missing or `token.json` is expired -- re-run `yt-title-updater auth`.

**Restream: "RESTREAM_CLIENT_SECRET environment variable is required"**
The client secret is not stored on disk. Set `RESTREAM_CLIENT_SECRET` in your environment before running any Restream commands.

**Restream: "No Restream credentials found"**
Run `yt-title-updater restream-auth` to complete the OAuth flow. Make sure `RESTREAM_CLIENT_ID` and `RESTREAM_CLIENT_SECRET` are set.

**OBS starts streaming but the title does not change**
Check the log file `yt-title-updater.log` in the same directory as the binary. It captures all output from the title update process. Common causes:
- Binary path not set in the OBS script settings.
- Expired or missing credentials -- re-run `yt-title-updater auth` or `restream-auth`.
- `titles.txt` is empty -- add at least one title (or let the default generator create one).
- For Restream mode: `RESTREAM_CLIENT_SECRET` not set in the OBS environment.

**Email: test email goes to spam**
The default Azure managed domain is not trusted by most mail providers. To fix this, configure a custom verified domain in your Azure Communication Services resource.

**`titles.txt` is empty / "No titles available"**
If `titles.txt` is empty, the tool generates a default title based on the current date and time. This is not an error.

**macOS: "yt-title-updater" cannot be opened because the developer cannot be verified**
See the Gatekeeper note in the macOS build instructions above.
