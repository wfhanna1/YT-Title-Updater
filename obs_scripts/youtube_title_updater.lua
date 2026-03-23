--[[
  youtube_title_updater.lua -- OBS Studio script

  Automatically updates the live stream title when streaming starts.
  Supports both YouTube (default) and Restream modes.
  Requires the yt-title-updater binary to be built and installed first.

  Setup:
    1. Build: pyinstaller yt-title-updater.spec
    2. Copy dist/yt-title-updater (macOS) or dist/yt-title-updater.exe (Windows)
       to a permanent location.
    3. In OBS: Tools > Scripts > + > select this file.
    4. Set the Binary Path in the script settings to the binary location.
    5. Run: yt-title-updater auth  (once, to authorise the YouTube account)
    6. For Restream: set Mode to "Restream" and run: yt-title-updater restream-auth

  The script fires on OBS_FRONTEND_EVENT_STREAMING_STARTED and runs the binary
  with --wait so it keeps retrying until the broadcast is live
  (typically 30-60 seconds after OBS starts pushing).
--]]

obs = obslua

-- ── State ─────────────────────────────────────────────────────────────────────

local binary_path  = ""
local wait_timeout = 90
local config_dir   = ""
local mode         = "youtube"

-- ── Helpers ───────────────────────────────────────────────────────────────────

local function is_windows()
    -- package.config's first line is the directory separator
    return package.config:sub(1, 1) == "\\"
end

local function get_log_path()
    -- Place the log next to the binary so it is easy to find.
    if binary_path == "" then return nil end

    local dir = binary_path:match("^(.*)[/\\]")  -- parent directory
    if dir then
        return dir .. (is_windows() and "\\" or "/") .. "yt-title-updater.log"
    end
    return nil
end

local function run_updater()
    if binary_path == "" then
        obs.script_log(obs.LOG_WARNING,
            "Binary path is not set. Open Tools > Scripts and set it.")
        return
    end

    -- Build the command.
    local cmd = '"' .. binary_path .. '"'
    cmd = cmd .. " update"
    cmd = cmd .. " --mode " .. mode
    cmd = cmd .. " --wait"
    cmd = cmd .. " --wait-timeout " .. tostring(wait_timeout)
    if config_dir ~= "" then
        cmd = cmd .. ' --config-dir "' .. config_dir .. '"'
    end

    obs.script_log(obs.LOG_INFO, "Running: " .. cmd)

    local log_path = get_log_path()

    -- Launch non-blocking so OBS is not frozen.
    -- Redirect stdout+stderr to a log file for diagnostics.
    if is_windows() then
        if log_path then
            os.execute('start /B "" ' .. cmd .. ' >> "' .. log_path .. '" 2>&1')
        else
            os.execute('start /B "" ' .. cmd)
        end
    else
        if log_path then
            os.execute(cmd .. ' >> "' .. log_path .. '" 2>&1 &')
        else
            os.execute(cmd .. " &")
        end
    end
end

-- ── OBS event callback ────────────────────────────────────────────────────────

local function on_event(event)
    if event == obs.OBS_FRONTEND_EVENT_STREAMING_STARTED then
        obs.script_log(obs.LOG_INFO, "Streaming started -- triggering title update")
        run_updater()
    end
end

-- ── Script lifecycle ──────────────────────────────────────────────────────────

function script_description()
    return [[
<h3>YouTube Title Updater</h3>
<p>Automatically updates your live stream title when you go live.<br>
Uses the <b>yt-title-updater</b> binary and your pre-configured title list.</p>
<p><b>Mode:</b> YouTube (default) updates via YouTube Data API.<br>
Restream updates all connected platforms via the Restream API.</p>
]]
end

function script_properties()
    local props = obs.obs_properties_create()

    -- Mode dropdown: YouTube or Restream
    local mode_list = obs.obs_properties_add_list(
        props,
        "mode",
        "Mode",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )
    obs.obs_property_list_add_string(mode_list, "YouTube", "youtube")
    obs.obs_property_list_add_string(mode_list, "Restream", "restream")

    obs.obs_properties_add_path(
        props,
        "binary_path",
        "Binary Path",
        obs.OBS_PATH_FILE,
        -- File filter: show the binary for the current OS
        is_windows() and "Executable (*.exe)" or "All files (*)",
        nil
    )

    obs.obs_properties_add_int(
        props,
        "wait_timeout",
        "Wait Timeout (seconds)",
        10,    -- minimum
        300,   -- maximum
        5      -- step
    )

    obs.obs_properties_add_path(
        props,
        "config_dir",
        "Config Directory (leave blank for default)",
        obs.OBS_PATH_DIRECTORY,
        nil,
        nil
    )

    return props
end

function script_defaults(settings)
    obs.obs_data_set_default_int(settings, "wait_timeout", 90)
    obs.obs_data_set_default_string(settings, "mode", "youtube")
end

function script_update(settings)
    binary_path  = obs.obs_data_get_string(settings, "binary_path")
    wait_timeout = obs.obs_data_get_int(settings, "wait_timeout")
    config_dir   = obs.obs_data_get_string(settings, "config_dir")
    mode         = obs.obs_data_get_string(settings, "mode")
end

function script_load(settings)
    script_update(settings)
    obs.obs_frontend_add_event_callback(on_event)
    obs.script_log(obs.LOG_INFO, "YouTube Title Updater script loaded")
end

function script_unload()
    obs.script_log(obs.LOG_INFO, "YouTube Title Updater script unloaded")
end
