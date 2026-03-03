@echo off
:: update_title.bat
::
:: Trigger a YouTube title update from OBS (Tools > Scripts is not required).
:: This is the simpler alternative to the Lua script: add it as an OBS
:: "Advanced Scene Switcher" action, or just run it manually.
::
:: Usage:
::   update_title.bat                  -- update once (exits 1 if not live)
::   update_title.bat --wait           -- retry until live (90 s timeout)
::   update_title.bat --wait 120       -- retry with a custom timeout
::
:: Set YT_UPDATER_BIN to the full path of your yt-title-updater.exe, e.g.:
::   set YT_UPDATER_BIN=C:\Tools\yt-title-updater.exe
:: or put yt-title-updater.exe in a directory on your PATH and leave it blank.

setlocal

if "%YT_UPDATER_BIN%"=="" (
    set "BIN=yt-title-updater"
) else (
    set "BIN=%YT_UPDATER_BIN%"
)

set "WAIT_FLAG="
set "TIMEOUT_VAL=90"

if /I "%1"=="--wait" (
    set "WAIT_FLAG=--wait"
    if not "%2"=="" set "TIMEOUT_VAL=%2"
)

echo Running YouTube Title Updater...
"%BIN%" update %WAIT_FLAG% --wait-timeout %TIMEOUT_VAL%

if %errorlevel% neq 0 (
    echo Title update failed. Check that you are live and credentials are set up.
    exit /b 1
)

echo Title updated successfully.
exit /b 0
