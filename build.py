#!/usr/bin/env python3
"""
Build script for YouTube Title Updater.
Creates standalone executables for both Windows and macOS.
"""

import os
import sys
import shutil
from pathlib import Path

def build_executable():
    """Build the CLI executable using PyInstaller."""
    current_dir = Path(__file__).parent
    
    # Create spec file content for CLI
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['youtube_updater/cli_main.py'],
    pathex=['{current_dir}'],
    binaries=[],
    datas=[
        ('titles.txt', '.'),
        ('applied-titles.txt', '.'),
        ('history.log', '.'),
        ('client_secrets.json', '.'),
        ('token.pickle', '.'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'google.oauth2.credentials',
        'google_auth_oauthlib.flow',
        'google.auth.transport.requests',
        'googleapiclient.discovery',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    # Write spec file
    spec_file = current_dir / "yt-title-updater.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)
    
    # Run PyInstaller
    os.system(f"pyinstaller {spec_file}")
    
    # Create launcher script
    if sys.platform == "win32":
        launcher_file = current_dir / "dist" / "yt-title-updater.bat"
        launcher_content = "@echo off\n\"%~dp0yt-title-updater\\yt-title-updater.exe\" %*"
    else:
        launcher_file = current_dir / "dist" / "yt-title-updater.sh"
        launcher_content = "#!/bin/bash\n\"$(dirname \"$0\")/yt-title-updater/yt-title-updater\" \"$@\""
    
    # Ensure dist directory exists
    os.makedirs(current_dir / "dist", exist_ok=True)
    
    # Write launcher script
    with open(launcher_file, "w") as f:
        f.write(launcher_content)
    
    # Make launcher script executable on Unix-like systems
    if sys.platform != "win32":
        os.chmod(launcher_file, 0o755)
    
    print("\nBuild completed successfully!")
    print(f"\nExecutable location: {current_dir / 'dist' / 'yt-title-updater'}")
    print(f"Launcher script: {launcher_file}")
    print("\nUsage:")
    print(f"  {launcher_file.name} status  # Check live status")
    print(f"  {launcher_file.name} update  # Update title")

if __name__ == "__main__":
    build_executable() 