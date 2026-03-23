# Testing Gaps & Hardening Plan

Created after 4 bugs were found during Windows deployment that our 239 tests missed.

## Root Cause

Our tests mocked too aggressively. Unit tests mocked `ComponentFactory.create_core()`, `_ensure_restream_client()`, and `EmailClient` -- so they never exercised the real wiring between components. The smoke tests only checked `--help` and "no creds" scenarios via subprocess, never the actual happy path with env vars and config files.

---

## Priority 1: CRITICAL (blocks deployment)

### P1.1: Windows file permissions are silently broken
`os.open(..., 0o600)` is ignored on Windows. `restream_token.json` and `email_config.json` are world-readable.

**Fix:** On Windows, use `icacls` or skip permission enforcement and document the limitation.
**Test:** Platform-conditional test that verifies the file is not world-readable.

### P1.2: No real subprocess E2E tests with env vars
Every Restream CLI command is only tested with mocks. The actual flow of "env var -> _ensure_restream_client -> RestreamAuth -> load token -> get_valid_token" was never exercised via subprocess.

**Fix:** Add subprocess tests that set env vars, create a fake token file, and run the CLI.
**Tests to add:**
- `restream-status` with env vars + valid token file -> exit 0
- `update --mode restream --dry-run` with env vars + valid token file -> exit 0
- `update --mode restream` with no env vars, no token -> exit 1 with clear error
- `test-email` with ACS env vars set (mocked at HTTP level, not Python level)

### P1.3: CRLF line endings in titles.txt (Windows)
`FileOperations.read_lines()` uses `.strip()` which handles CRLF, but this is untested.

**Fix:** Add test with `"Title One\r\nTitle Two\r\n"` content.
**Test:** Write CRLF file, verify `get_next_title()` returns clean titles without `\r`.

---

## Priority 2: HIGH (user-facing failures)

### P2.1: Paths with spaces
Windows paths like `C:\Users\St Mary\AppData\...` are common. No test uses paths with spaces.

**Fix:** Add tests using `tmp_path / "path with spaces" / "config"`.
**Tests to add:** ConfigManager, TitleManager, RestreamAuth all work with spaced paths.

### P2.2: Unicode in titles
Titles with non-ASCII characters (Coptic, Arabic, emoji) are never tested.

**Fix:** Add test with `"Sunday Liturgy - القداس الإلهي"` and similar.
**Tests to add:** Write, read, rotate, archive, and PATCH with Unicode titles.

### P2.3: Port 9451 already in use
`restream-auth` binds to port 9451. If something else is using it, the error is unclear.

**Fix:** Catch `OSError` on bind and print a helpful message.
**Test:** Mock `HTTPServer.__init__` to raise `OSError`, verify error message.

### P2.4: test-email gives no actionable error
Fixed in the bug fix commit (raise_on_error=True), but the underlying `except Exception: return False` in `send_error_notification` still swallows errors for background sends. Background sends should at least log the error.

**Fix:** Add logging to the except block in `send_error_notification`.
**Test:** Verify that a failed background send logs the error (even if it doesn't raise).

---

## Priority 3: MEDIUM (edge cases)

### P3.1: ComponentFactory never tested
All tests mock `ComponentFactory.create_core()`. The actual wiring (config -> auth -> client -> core) is never exercised.

**Fix:** Add an integration test that calls `ComponentFactory.create_core(tmp_dir)` with a real temp dir (no credentials) and verifies the core is created correctly with None youtube_client.

### P3.2: Token file corruption
If `restream_token.json` is truncated (disk full, crash during write), `load_token()` now raises `AuthenticationError` (fixed in Phase 2 review). But `email_config.json` corruption is handled by `ConfigManager.get_email_config()`. Neither is tested via CLI subprocess.

**Fix:** Add subprocess tests with corrupted files.

### P3.3: Network timeout handling
All API calls use `requests.get/post/patch` without explicit timeout. A hanging connection blocks forever.

**Fix:** Add `timeout=30` to all `requests.*` calls in `restream_client.py` and `restream_auth.py`.
**Test:** Mock `requests.post` to raise `requests.Timeout`, verify RestreamAPIError.

### P3.4: Unknown platform IDs in restream-status
Only platform IDs 5 (youtube) and 37 (facebook) are tested. The `PLATFORM_NAMES` dict has 18 entries but an unknown ID shows `id:NNN`.

**Fix:** Test with unknown platform ID, verify output.

### P3.5: Concurrent execution
Two OBS instances or a manual run + OBS trigger could cause simultaneous title updates, double-rotating titles.txt.

**Fix:** File locking (flock/lockfile) on titles.txt during rotation. Out of scope for immediate fix, document as known limitation.

---

## Priority 4: LOW (documentation / defense in depth)

### P4.1: OBS Lua script not functionally testable
The Lua script can only be tested inside OBS. Our tests do string matching only.

**Action:** Document manual OBS testing procedure in docs/.

### P4.2: Document Windows 0o600 limitation
If we can't fix file permissions on Windows, document it clearly.

### P4.3: Stale PLATFORM_NAMES dict
Restream may add new platforms. The hardcoded dict will show `id:NNN` for new ones.

**Action:** Consider fetching platform names from the API, or document how to add new ones.

---

## Implementation Plan

| Phase | Scope | Tests Added | Effort |
|-------|-------|-------------|--------|
| A | P1.2 + P1.3: Subprocess E2E + CRLF | ~10 tests | Small |
| B | P2.1 + P2.2: Paths with spaces + Unicode | ~8 tests | Small |
| C | P1.1 + P2.3 + P2.4: Windows perms + port + logging | ~5 tests + code fixes | Medium |
| D | P3.1 + P3.2 + P3.3: Factory + corruption + timeouts | ~8 tests + code fixes | Medium |
| E | P3.4 + P3.5 + P4.*: Edge cases + documentation | ~4 tests + docs | Small |

Estimated total: ~35 new tests, 5 code fixes.

---

## How These Bugs Would Have Been Caught

| Bug | What would have caught it |
|-----|--------------------------|
| titles.txt not read | Subprocess E2E test with real config dir + titles file (Phase A) |
| README quotes for Windows set | Manual Windows deployment checklist (not testable in CI) |
| restream-status requires secret | Subprocess test: valid token + no secret -> should succeed (Phase A) |
| test-email silent failure | Subprocess test: bad ACS creds -> should show error, not "Failed" (Phase A) |
