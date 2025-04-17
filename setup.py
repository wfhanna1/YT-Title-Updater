from setuptools import setup

APP = ['youtube_menu_bar_app.py']  # Your main script
DATA_FILES = ['titles.txt', 'client_secrets.json', 'token.pickle']  # Optional: include these if needed
OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'rumps',
        'googleapiclient',
        'google_auth_oauthlib',
        'google_auth_httplib2',
    ],
    'plist': {
        'CFBundleName': 'YT Title Updater',
        'CFBundleDisplayName': 'YT Title Updater',
        'CFBundleIdentifier': 'com.yourdomain.yttitle',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0',
    },
}

setup(
    app=APP,
    name='YT Title Updater',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
