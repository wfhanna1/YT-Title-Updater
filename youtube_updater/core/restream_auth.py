"""Restream OAuth2 authentication manager."""

import http.server
import json
import os
import threading
import time
import urllib.parse
import webbrowser
from typing import Any, Dict, Optional

import requests

from ..exceptions.custom_exceptions import AuthenticationError

OAUTH_AUTHORIZE_URL = "https://api.restream.io/login"
OAUTH_TOKEN_URL = "https://api.restream.io/oauth/token"
REDIRECT_PORT = 9451
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"


class RestreamAuth:
    """Manages Restream OAuth2 authentication.

    Handles browser-based authorization code flow, token persistence
    with 0o600 permissions, and silent refresh via refresh_token.
    """

    def __init__(self, client_id: str, client_secret: str, token_path: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_path = token_path

    def authenticate(self) -> Dict[str, Any]:
        """Run the full OAuth2 authorization code flow.

        Opens a browser for user authorization, exchanges the code
        for tokens, and saves them to disk.

        Returns:
            Dict with access_token, refresh_token, expires_at

        Raises:
            AuthenticationError: If the flow fails
        """
        token_response = self._run_oauth_flow()
        token_data = self._build_token_data(token_response)
        self._save_token(token_data)
        return token_data

    def load_token(self) -> Optional[Dict[str, Any]]:
        """Load token data from disk.

        Returns:
            Token dict, or None if file doesn't exist
        """
        if not os.path.exists(self.token_path):
            return None
        with open(self.token_path, "r") as f:
            return json.load(f)

    def refresh_token(self, refresh_token_value: str) -> Dict[str, Any]:
        """Refresh the access token using the refresh token.

        Args:
            refresh_token_value: The refresh token to use

        Returns:
            Updated token data dict

        Raises:
            AuthenticationError: If refresh fails (e.g. revoked token)
        """
        resp = requests.post(
            OAUTH_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token_value,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if resp.status_code != 200:
            raise AuthenticationError(
                f"Token refresh failed ({resp.status_code}): {resp.text}. "
                "Run `restream-auth` to re-authenticate."
            )

        token_data = self._build_token_data(resp.json())
        self._save_token(token_data)
        return token_data

    def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if needed.

        Returns:
            A valid access token string

        Raises:
            AuthenticationError: If no token exists or refresh fails
        """
        token_data = self.load_token()
        if token_data is None:
            raise AuthenticationError(
                "No Restream credentials found. Run `restream-auth` to authenticate."
            )

        # Check expiration (with 60s buffer)
        expires_at = token_data.get("expires_at", 0)
        if time.time() < expires_at - 60:
            return token_data["access_token"]

        # Token expired, try refresh
        refresh_tok = token_data.get("refresh_token")
        if not refresh_tok:
            raise AuthenticationError(
                "Restream token expired and no refresh token available. "
                "Run `restream-auth` to re-authenticate."
            )

        new_data = self.refresh_token(refresh_tok)
        return new_data["access_token"]

    def _run_oauth_flow(self) -> Dict[str, Any]:
        """Run the browser-based OAuth2 authorization code flow.

        Returns:
            Token response dict from the OAuth server

        Raises:
            AuthenticationError: If the flow fails
        """
        auth_code = None
        auth_error = None

        class CallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                nonlocal auth_code, auth_error
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                if "code" in params:
                    auth_code = params["code"][0]
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<h2>Authorization successful!</h2><p>You can close this tab.</p>")
                else:
                    auth_error = params.get("error", ["unknown"])[0]
                    self.send_response(400)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(f"<h2>Authorization failed: {auth_error}</h2>".encode())

            def log_message(self, format, *args):
                pass

        server = http.server.HTTPServer(("localhost", REDIRECT_PORT), CallbackHandler)
        server_thread = threading.Thread(target=server.handle_request, daemon=True)
        server_thread.start()

        auth_params = urllib.parse.urlencode({
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": REDIRECT_URI,
            "state": "restream_auth",
        })
        auth_url = f"{OAUTH_AUTHORIZE_URL}?{auth_params}"
        webbrowser.open(auth_url)

        server_thread.join(timeout=120)
        server.server_close()

        if auth_error:
            raise AuthenticationError(f"Authorization denied: {auth_error}")
        if not auth_code:
            raise AuthenticationError("Authorization timed out (120s)")

        # Exchange code for token
        resp = requests.post(
            OAUTH_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": REDIRECT_URI,
                "code": auth_code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if resp.status_code != 200:
            raise AuthenticationError(
                f"Token exchange failed ({resp.status_code}): {resp.text}"
            )

        return resp.json()

    def _build_token_data(self, token_response: Dict[str, Any]) -> Dict[str, Any]:
        """Build the token data dict to persist."""
        return {
            "access_token": token_response["access_token"],
            "refresh_token": token_response.get("refresh_token", ""),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "expires_at": time.time() + token_response.get("expires_in", 3600),
        }

    def _save_token(self, token_data: Dict[str, Any]) -> None:
        """Save token data to disk with 0o600 permissions."""
        fd = os.open(self.token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(token_data, f, indent=2)
