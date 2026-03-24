# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for yt-title-updater (macOS and Windows).
#
# Build commands:
#   macOS:   pyinstaller yt-title-updater.spec
#   Windows: pyinstaller yt-title-updater.spec
#
# Output: dist/yt-title-updater  (macOS)
#         dist/yt-title-updater.exe  (Windows)
#
# NOTE: client_secrets.json and token.json are NOT bundled.
# They live in the user data directory (platformdirs) and must be
# set up once with:  yt-title-updater auth

a = Analysis(
    ['youtube_updater/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'googleapiclient.discovery',
        'googleapiclient._helpers',
        'google_auth_oauthlib.flow',
        'google.auth.transport.requests',
        'google.oauth2.credentials',
        'platformdirs',
        'tzdata',
        'charset_normalizer',
        'urllib3',
        'zoneinfo',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6', 'tkinter', 'matplotlib'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='yt-title-updater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,       # CLI tool -- keep console window for log output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
