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
            List of channel dicts with displayName, platform, active keys

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
        """Update the stream title across all connected platforms.

        Args:
            title: New stream title

        Raises:
            RestreamAPIError: On API failures
        """
        resp = requests.patch(
            f"{API_BASE}/user/stream",
            json={"title": title},
            headers=self._headers,
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code not in (200, 204):
            raise RestreamAPIError(
                f"Failed to update stream title ({resp.status_code}): {resp.text}"
            )
