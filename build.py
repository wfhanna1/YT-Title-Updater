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
    """Build the executable using PyInstaller."""
    current_dir = Path(__file__).parent.absolute()
    
    # Create spec file content for CLI version
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    [r'{current_dir / "youtube_updater" / "cli_main.py"}'],
    pathex=[r'{current_dir}'],
    binaries=[],
    datas=[
        (r'{current_dir / "titles.txt"}', '.'),
        (r'{current_dir / "applied-titles.txt"}', '.'),
        (r'{current_dir / "history.log"}', '.'),
        (r'{current_dir / "client_secrets.json"}', '.'),
        (r'{current_dir / "token.pickle"}', '.'),
        (r'{current_dir / "README.md"}', '.'),
        (r'{current_dir / "LICENSE"}', '.'),
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
    name='yt-title-updater-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True for CLI application
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    # Write spec file
    spec_file = current_dir / "yt-title-updater-cli.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)
    
    # Run PyInstaller with proper path handling
    pyinstaller_cmd = f'pyinstaller "{spec_file}"'
    os.system(pyinstaller_cmd)
    
    # Create a batch file for easy running from anywhere
    batch_content = """@echo off
set SCRIPT_DIR=%~dp0
"%SCRIPT_DIR%yt-title-updater-cli\\yt-title-updater-cli.exe" %*
"""
    
    batch_file = current_dir / "dist" / "yt-title-updater.bat"
    with open(batch_file, "w") as f:
        f.write(batch_content)
    
    print("\nBuild completed successfully!")
    print(f"\nExecutable location: {current_dir / 'dist' / 'yt-title-updater-cli'}")
    print(f"Batch file location: {batch_file}")
    print("\nTo use the CLI from anywhere:")
    print("1. Copy the 'yt-title-updater-cli' folder and 'yt-title-updater.bat' from the dist folder")
    print("2. Add the folder containing the batch file to your system PATH")
    print("3. Run commands like:")
    print("   yt-title-updater status")
    print("   yt-title-updater update")

if __name__ == "__main__":
    build_executable() 