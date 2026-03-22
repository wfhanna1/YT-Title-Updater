#!/usr/bin/env python3
"""Quick validation script to test Restream API credentials on a free account.

Uses OAuth2 authorization code flow:
1. Opens browser for user to grant access
2. Starts a local server to capture the redirect with the auth code
3. Exchanges the code for an access token
4. Tests API endpoints
"""

import json
import http.server
import threading
import urllib.request
import urllib.error
import urllib.parse
import webbrowser
import getpass

API_BASE = "https://api.restream.io/v2"
OAUTH_AUTHORIZE_URL = "https://api.restream.io/login"
OAUTH_TOKEN_URL = "https://api.restream.io/oauth/token"
REDIRECT_PORT = 9451
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

# Will be set by the callback handler
_auth_code = None
_auth_error = None


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handles the OAuth redirect callback."""

    def do_GET(self):
        global _auth_code, _auth_error
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorization successful!</h2><p>You can close this tab.</p>")
        else:
            _auth_error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<h2>Authorization failed: {_auth_error}</h2>".encode())

    def log_message(self, format, *args):
        pass  # Suppress server logs


def get_access_token_via_browser(client_id, client_secret):
    """Run the OAuth2 authorization code flow via browser."""
    global _auth_code, _auth_error
    _auth_code = None
    _auth_error = None

    # Start local server to receive callback
    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    # Build authorization URL
    auth_params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "state": "validate",
    })
    auth_url = f"{OAUTH_AUTHORIZE_URL}?{auth_params}"

    print(f"  Opening browser for authorization...")
    print(f"  If it doesn't open, visit:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    # Wait for callback
    server_thread.join(timeout=120)
    server.server_close()

    if _auth_error:
        print(f"  Authorization denied: {_auth_error}")
        return None

    if not _auth_code:
        print("  Timed out waiting for authorization (120s).")
        return None

    print(f"  Authorization code received. Exchanging for token...")

    # Exchange code for token
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "code": _auth_code,
    }).encode("utf-8")

    req = urllib.request.Request(OAUTH_TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
            # Check if we got a refresh token (needed for headless mode)
            refresh_token = body.get("refresh_token")
            if refresh_token:
                print(f"  Refresh token received: {refresh_token[:20]}... (headless mode will work!)")
            else:
                print(f"  WARNING: No refresh token returned. Headless mode may not work.")
                print(f"  Full token response keys: {list(body.keys())}")
            return body.get("access_token")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"  Token exchange failed ({e.code}): {error_body}")
        return None


def test_endpoint(token, method, path, label, body=None):
    """Test a single API endpoint and print the result."""
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body else None

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"  OK  {label}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"  FAIL {label} ({e.code}): {error_body[:200]}")
        return None


def main():
    print("=== Restream API Validation ===\n")

    client_id = input("Client ID: ").strip()
    client_secret = getpass.getpass("Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Both Client ID and Client Secret are required.")
        return

    # Step 1: OAuth browser flow
    print("\n1. Authenticating (browser will open)...")
    token = get_access_token_via_browser(client_id, client_secret)
    if not token:
        print("\n   Could not authenticate. Check your credentials.")
        print("   Note: API access may require a paid Restream plan.")
        return
    print(f"   Token obtained: {token[:20]}...")

    # Step 2: Get user profile
    print("\n2. Testing GET /user/profile...")
    profile = test_endpoint(token, "GET", "/user/profile", "User profile")
    if profile:
        print(f"     Account: {profile.get('username', 'N/A')} ({profile.get('email', 'N/A')})")

    # Step 3: List channels (connected platforms)
    print("\n3. Testing GET /user/channel/all...")
    channels = test_endpoint(token, "GET", "/user/channel/all", "List channels")
    if channels and isinstance(channels, list):
        print(f"     Connected platforms: {len(channels)}")
        for ch in channels:
            name = ch.get("displayName") or ch.get("name") or ch.get("platform", "unknown")
            platform = ch.get("platform", "unknown")
            enabled = ch.get("active", ch.get("enabled", "?"))
            print(f"       - {name} ({platform}) [active={enabled}]")
            print(f"         Raw keys: {list(ch.keys())}")
            # Print full channel data for debugging field names
            for key, val in ch.items():
                if not isinstance(val, (dict, list)):
                    print(f"         {key}: {val}")
                else:
                    print(f"         {key}: {json.dumps(val, indent=2)[:300]}")
    elif channels and isinstance(channels, dict):
        print(f"     Response: {json.dumps(channels, indent=2)[:500]}")

    # Step 4: Get stream info
    print("\n4. Testing GET /user/stream...")
    stream = test_endpoint(token, "GET", "/user/stream", "Stream info")
    if stream:
        print(f"     Stream data: {json.dumps(stream, indent=2)[:500]}")

    # Step 5: Summary
    print("\n=== Summary ===")
    results = {
        "Auth": token is not None,
        "Profile": profile is not None,
        "Channels": channels is not None,
        "Stream": stream is not None,
    }
    for name, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    all_passed = all(results.values())
    if all_passed:
        print("\n  All checks passed! Restream API works on your account.")
        print("  The PATCH /user/stream endpoint should let us update titles.")
    elif results["Auth"]:
        print("\n  Auth works but some endpoints failed.")
        print("  This may indicate plan-level restrictions on certain features.")
    else:
        print("\n  Authentication failed. API may not be available on the free plan.")


if __name__ == "__main__":
    main()
