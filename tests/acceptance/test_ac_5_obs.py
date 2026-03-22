"""Acceptance tests for OBS integration (AC 5.1, 5.2)."""

from pathlib import Path

import pytest


@pytest.mark.xfail(reason="Phase 5: not yet implemented")
def test_ac_5_1_obs_script_has_mode_dropdown(project_root):
    """AC 5.1: OBS script adds Mode dropdown (youtube/restream).

    Given: The OBS Lua script exists
    When: We inspect the script source
    Then: It contains a Mode dropdown property with youtube and restream options
    """
    lua_path = project_root / "obs_scripts" / "youtube_title_updater.lua"
    content = lua_path.read_text()
    assert "mode" in content.lower()
    assert "youtube" in content.lower()
    assert "restream" in content.lower()


@pytest.mark.xfail(reason="Phase 5: not yet implemented")
def test_ac_5_2_restream_mode_passes_flag(project_root):
    """AC 5.2: Restream mode passes --mode restream to CLI.

    Given: The OBS Lua script exists
    When: Mode is set to restream
    Then: The command includes --mode restream
    """
    lua_path = project_root / "obs_scripts" / "youtube_title_updater.lua"
    content = lua_path.read_text()
    assert "--mode" in content
