#!/usr/bin/env python3
"""Quick validation script to test Restream API credentials on a free account."""

import base64
import json
import urllib.request
import urllib.error
import urllib.parse
import getpass

API_BASE = "https://api.restream.io/v2"


def get_access_token(client_id, client_secret):
    """Get an OAuth access token using client credentials flow."""
    url = "https://api.restream.io/oauth/token"

    # Client credentials grant (form-encoded as required by Restream)
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read())
            return body.get("access_token")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"  Auth failed ({e.code}): {error_body}")
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

    # Step 1: Get access token
    print("\n1. Authenticating...")
    token = get_access_token(client_id, client_secret)
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
