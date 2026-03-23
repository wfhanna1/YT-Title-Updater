"""Restream API client for managing stream titles."""

import logging
from typing import Any, Dict, List, Optional

import requests

from ..exceptions.custom_exceptions import RestreamAPIError

API_BASE = "https://api.restream.io/v2"
REQUEST_TIMEOUT = 30  # seconds

logger = logging.getLogger("youtube_updater")


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
        """Update the stream title across all enabled channels.

        Uses the /user/channel-meta/{id} endpoint which controls the
        broadcast title on each platform. Only patches enabled channels.

        Args:
            title: New stream title

        Raises:
            RestreamAPIError: On API failures
        """
        channels = self.get_channels()
        if not channels:
            raise RestreamAPIError("No channels found on Restream account.")

        enabled_channels = [ch for ch in channels if ch.get("enabled")]
        if not enabled_channels:
            raise RestreamAPIError("No enabled channels found on Restream account.")

        logger.info(
            "Found %d channel(s) (%d enabled)", len(channels), len(enabled_channels)
        )

        errors = []
        updated = 0
        for ch in enabled_channels:
            channel_id = ch["id"]
            name = ch.get("displayName", "unknown")
            platform_id = ch.get("streamingPlatformId", "?")

            logger.info(
                "PATCHing channel-meta %s (id=%s, platform=%s)",
                name, channel_id, platform_id,
            )

            resp = requests.patch(
                f"{API_BASE}/user/channel-meta/{channel_id}",
                json={"title": title},
                headers=self._headers,
                timeout=REQUEST_TIMEOUT,
            )

            logger.info(
                "Channel %s response: status=%d, body=%s",
                name, resp.status_code, resp.text[:500],
            )

            if resp.status_code in (200, 204):
                updated += 1
            else:
                errors.append(f"{name}: {resp.status_code} {resp.text[:200]}")

        if updated == 0:
            raise RestreamAPIError(
                f"Failed to update any channels. Errors: {'; '.join(errors)}"
            )

        logger.info("Updated %d/%d enabled channel(s)", updated, len(enabled_channels))
