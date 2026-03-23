"""Restream API client for managing stream titles."""

from typing import Any, Dict, List, Optional

import requests

from ..exceptions.custom_exceptions import RestreamAPIError

API_BASE = "https://api.restream.io/v2"
REQUEST_TIMEOUT = 30  # seconds


class RestreamClient:
    """Client for the Restream REST API.

    Wraps the Restream v2 API endpoints for channel listing,
    stream info retrieval, and title updates.
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def get_channels(self) -> List[Dict[str, Any]]:
        """List all connected channels/platforms.

        Returns:
            List of channel dicts with id, displayName, streamingPlatformId, enabled

        Raises:
            RestreamAPIError: On API failures
        """
        resp = requests.get(
            f"{API_BASE}/user/channel/all", headers=self._headers, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 401:
            raise RestreamAPIError(
                "Restream authentication failed (401). "
                "Run `restream-auth` to re-authenticate."
            )
        if resp.status_code != 200:
            raise RestreamAPIError(
                f"Failed to list channels ({resp.status_code}): {resp.text}"
            )
        return resp.json()

    def get_stream_info(self) -> Optional[Dict[str, Any]]:
        """Get current stream information.

        Returns:
            Stream info dict, or None if not currently streaming

        Raises:
            RestreamAPIError: On API failures (except 404)
        """
        resp = requests.get(
            f"{API_BASE}/user/stream", headers=self._headers, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 404:
            return None
        if resp.status_code == 401:
            raise RestreamAPIError(
                "Restream authentication failed (401). "
                "Run `restream-auth` to re-authenticate."
            )
        if resp.status_code != 200:
            raise RestreamAPIError(
                f"Failed to get stream info ({resp.status_code}): {resp.text}"
            )
        return resp.json()

    def update_stream_title(self, title: str) -> None:
        """Update the stream title across all connected channels.

        Iterates over all channels and PATCHes each one with the new title.

        Args:
            title: New stream title

        Raises:
            RestreamAPIError: On API failures
        """
        channels = self.get_channels()
        if not channels:
            raise RestreamAPIError("No channels found on Restream account.")

        errors = []
        updated = 0
        for ch in channels:
            channel_id = ch.get("id")
            name = ch.get("displayName", "unknown")
            if not channel_id:
                continue
            resp = requests.patch(
                f"{API_BASE}/user/channel/{channel_id}",
                json={"active": True, "title": title},
                headers=self._headers,
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code in (200, 204):
                updated += 1
            else:
                errors.append(f"{name}: {resp.status_code} {resp.text[:100]}")

        if updated == 0:
            raise RestreamAPIError(
                f"Failed to update any channels. Errors: {'; '.join(errors)}"
            )
