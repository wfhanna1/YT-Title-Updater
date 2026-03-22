# Restream API Integration Plan

## Context

The CLI tool (yt-title-updater) currently updates YouTube live stream titles via the YouTube Data API v3. This plan adds Restream integration so one command can update titles across all connected platforms (YouTube, Facebook, Instagram, etc.) via the Restream API, while keeping existing YouTube-only behavior fully backward compatible.

Additionally, error notifications via Azure Communication Services (ACS) email will alert the user when authentication fails, so headless/OBS-automated runs don't silently break.

A standalone `validate_restream.py` already exists with a working OAuth2 browser flow for Restream. Its patterns (local callback server, token exchange) will be reused in the new `restream_auth.py` module.

---

## Development Methodology

### TDD & ATTD Workflow (per card/phase)

1. Write acceptance tests first (ATTD) -- high-level tests that describe desired behavior. These FAIL initially (red).
2. Write unit tests (TDD) -- fine-grained tests for the module being built. These also FAIL initially (red).
3. Write implementation code -- make the unit tests pass (green).
4. Run acceptance tests -- verify they now pass (green).
5. Refactor if needed -- all tests still green.
6. Code review -- self-review of all changed files for:
   - Correctness: logic errors, edge cases, off-by-one
   - Security: injection, secrets exposure, insecure file permissions
   - Quality: duplication, naming, single-responsibility, dead code
   - Test coverage: are all paths tested? Any missing assertions?
   - Consistency: matches existing codebase patterns and conventions
   - NF4 compliance: no writes to YouTube auth files

### Branching & PR Strategy

| Phase | Branch | PR Target |
|-------|--------|-----------|
| 0 (CI + Plan) | `claude/castr-api-integration-caLjf` | `main` (final) |
| 1 (Foundation) | `claude/phase-1-foundation-caLjf` | `claude/castr-api-integration-caLjf` |
| 2 (Auth) | `claude/phase-2-restream-auth-caLjf` | `claude/castr-api-integration-caLjf` |
| 3 (Client + Core) | `claude/phase-3-restream-client-caLjf` | `claude/castr-api-integration-caLjf` |
| 4 (Email) | `claude/phase-4-email-notifications-caLjf` | `claude/castr-api-integration-caLjf` |
| 5 (OBS) | `claude/phase-5-obs-integration-caLjf` | `claude/castr-api-integration-caLjf` |

Final PR: `claude/castr-api-integration-caLjf` -> `main` once all phases merged.

### Clearing Gates

After each phase PR merges, a clearing gate must be satisfied. Every gate requires E2E tests to pass.

| Gate | Unit Tests | Integration Tests | E2E Tests | Acceptance Tests |
|------|-----------|------------------|-----------|-----------------|
| Gate 0 (CI) | All existing pass | All existing pass | Smoke tests pass | Skeletons exist (xfail) |
| Gate 1 (Foundation) | Config manager tests pass | test_config_restream.py: real file I/O | pytest tests/smoke/ passes. CLI --help works. | NF3, NF4 pass |
| Gate 2 (Auth) | test_restream_auth.py all pass | auth->save->load->refresh cycle | CLI restream-auth mocked exit 0/1 | AC 1.1, 1.2, 1.3, 4.1, 4.2, NF2 pass |
| Gate 3 (Client+Core) | test_restream_client.py, test_core.py, test_cli_restream.py all pass | test_restream_workflow.py: core->update->archive | CLI update --mode restream exit 0, restream-status prints channels, no-creds exit 1 | AC 2.1, 2.2, 3.1-3.5, NF1 pass |
| Gate 4 (Email) | test_email_notifier.py all pass | auth failure->email sent | CLI configure-email + test-email mocked | AC 1.3, 3.5 pass with email verification |
| Gate 5 (OBS) | -- | -- | Lua script parses, grep confirms Mode dropdown | AC 5.1, 5.2 pass |
| Final Gate | pytest tests/unit/ all green | pytest tests/integration/ all green | pytest tests/smoke/ all green | pytest tests/acceptance/ all 18 ACs green |

---

## Acceptance Criteria Traceability

| AC | Summary | Acceptance Test | Unit Test | Implemented In |
|----|---------|----------------|-----------|---------------|
| 1.1 | restream-auth opens browser, saves restream_token.json (0o600) | test_ac_1_auth.py::test_ac_1_1 | test_restream_auth.py | restream_auth.py + CLI |
| 1.2 | If refresh token exists, refresh silently without browser | test_ac_1_auth.py::test_ac_1_2 | test_restream_auth.py | restream_auth.py |
| 1.3 | Auth failure -> clear error + email notification + exit 1 | test_ac_1_auth.py::test_ac_1_3 | test_cli_restream.py | CLI + email_notifier.py |
| 2.1 | restream-status lists connected channels | test_ac_2_status.py::test_ac_2_1 | test_restream_client.py | CLI + restream_client.py |
| 2.2 | Missing credentials -> error directing to restream-auth | test_ac_2_status.py::test_ac_2_2 | test_cli_restream.py | CLI |
| 3.1 | update --mode restream -> PATCH title -> archive -> exit 0 | test_ac_3_update.py::test_ac_3_1 | test_restream_client.py, test_core.py | CLI + Core |
| 3.2 | update --mode youtube preserves existing behavior | test_ac_3_update.py::test_ac_3_2 | existing test_cli.py | CLI (no changes) |
| 3.3 | update (no flag) defaults to youtube | test_ac_3_update.py::test_ac_3_3 | test_cli_restream.py | CLI |
| 3.4 | Restream mode + --wait polls until stream data available | test_ac_3_update.py::test_ac_3_4 | test_cli_restream.py | CLI |
| 3.5 | Missing/expired Restream creds -> clear error + email + exit 1 | test_ac_3_update.py::test_ac_3_5 | test_cli_restream.py | CLI + email_notifier.py |
| 4.1 | Expired access token -> silent refresh via refresh_token | test_ac_4_token.py::test_ac_4_1 | test_restream_auth.py | restream_auth.py |
| 4.2 | Invalid refresh token -> error directing to re-run restream-auth | test_ac_4_token.py::test_ac_4_2 | test_restream_auth.py | restream_auth.py |
| 5.1 | OBS script adds Mode dropdown (youtube/restream) | test_ac_5_obs.py::test_ac_5_1 | -- | youtube_title_updater.lua |
| 5.2 | Restream mode passes --mode restream to CLI | test_ac_5_obs.py::test_ac_5_2 | -- | youtube_title_updater.lua |
| NF1 | No changes to existing YouTube-only behavior | test_nf.py::test_nf1 | existing tests | All phases |
| NF2 | Restream credentials stored with 0o600 permissions | test_nf.py::test_nf2 | test_restream_auth.py | restream_auth.py |
| NF3 | requests library added to requirements.txt | test_nf.py::test_nf3 | -- | requirements.txt |
| NF4 | Never modify token.json, credentials.json, pickle.json | test_nf.py::test_nf4 | test_nf4_safeguard.py | All phases |

---

## Phase 0: CI, Plan, and Test Infrastructure

**Branch:** `claude/castr-api-integration-caLjf` (direct commit)

**Work items:**
1. Create `docs/plan.md` (this file)
2. Create `.github/workflows/ci.yml`
3. Create `tests/acceptance/__init__.py`
4. Create `tests/acceptance/conftest.py` with shared fixtures
5. Create skeleton acceptance test files (all `@pytest.mark.xfail`):
   - `tests/acceptance/test_ac_1_auth.py`
   - `tests/acceptance/test_ac_2_status.py`
   - `tests/acceptance/test_ac_3_update.py`
   - `tests/acceptance/test_ac_4_token.py`
   - `tests/acceptance/test_ac_5_obs.py`
   - `tests/acceptance/test_nf.py`
6. Update `pytest.ini` to include acceptance test path
7. Create GitHub issues (epic + 6 phases + 18 ACs)

**Gate 0 exit criteria:**
- [ ] CI workflow file exists and is valid YAML
- [ ] All existing tests pass: `pytest tests/unit/ tests/integration/ tests/smoke/ -v`
- [ ] Acceptance test skeletons exist and are all xfail: `pytest tests/acceptance/ -v`
- [ ] `pytest tests/ -v` -- full suite green (xfails count as green)

---

## Phase 1: Foundation

**Branch:** `claude/phase-1-foundation-caLjf` off `claude/castr-api-integration-caLjf`

### ATTD: Acceptance tests (red)
- `test_nf.py::test_nf3` -- assert `requests` is in requirements.txt
- `test_nf.py::test_nf4` -- assert Restream/email operations never touch YouTube auth files
- Remove xfail from NF3, NF4 tests

### TDD: Unit tests (red)
- `tests/unit/test_config_manager.py` -- new tests for `ensure_restream_token()`, `get_email_config()`, `save_email_config()`
- `tests/unit/test_nf4_safeguard.py` -- snapshot YouTube auth file mtimes, run config operations, assert unchanged

### Implementation
- `requirements.txt` -- add `requests>=2.28.0`, `azure-communication-email>=1.0.0`
- `youtube_updater/exceptions/custom_exceptions.py` -- add `RestreamAPIError`
- `youtube_updater/core/config_manager.py` -- add Restream + email file paths and methods

### Integration test
- `tests/integration/test_config_restream.py` -- real file I/O: create temp dir, save email config, read it back, verify Restream token path resolution

### E2E test
- `pytest tests/smoke/` -- existing smoke tests still pass
- CLI `--help` via subprocess -- verify no import errors

### Gate 1 exit criteria:
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `pytest tests/unit/test_config_manager.py` -- new methods pass
- [ ] `pytest tests/unit/test_nf4_safeguard.py` -- NF4 verified
- [ ] `pytest tests/integration/test_config_restream.py` -- real file I/O pass
- [ ] `pytest tests/smoke/` -- existing E2E still pass
- [ ] `pytest tests/acceptance/test_nf.py::test_nf3` -- pass
- [ ] `pytest tests/acceptance/test_nf.py::test_nf4` -- pass
- [ ] `pytest tests/ -v` -- full suite green, no regressions
- [ ] CI green

**PR:** `claude/phase-1-foundation-caLjf` -> `claude/castr-api-integration-caLjf`

---

## Phase 2: Restream Auth (AC 1.1, 1.2, 1.3, 4.1, 4.2)

**Branch:** `claude/phase-2-restream-auth-caLjf` off `claude/castr-api-integration-caLjf`

### ATTD: Acceptance tests (red)
- `test_ac_1_auth.py::test_ac_1_1` -- restream-auth triggers OAuth flow, saves token with 0o600
- `test_ac_1_auth.py::test_ac_1_2` -- with existing valid refresh token, no browser opened
- `test_ac_1_auth.py::test_ac_1_3` -- auth failure prints error, sends email, exits 1
- `test_ac_4_token.py::test_ac_4_1` -- expired access token triggers silent refresh
- `test_ac_4_token.py::test_ac_4_2` -- invalid refresh token -> error + reauth message
- `test_nf.py::test_nf2` -- token file has 0o600 permissions

### TDD: Unit tests (red)
- `tests/unit/test_restream_auth.py`:
  - `test_authenticate_opens_browser` -- mock webbrowser.open, verify called
  - `test_authenticate_saves_token_0600` -- verify file permissions
  - `test_load_token_returns_dict` -- valid file -> dict
  - `test_load_token_returns_none` -- missing file -> None
  - `test_refresh_token_success` -- mock requests.post -> new token saved
  - `test_refresh_token_failure_401` -- raises AuthenticationError
  - `test_get_valid_token_not_expired` -- returns cached token
  - `test_get_valid_token_expired_refreshes` -- calls refresh
  - `test_get_valid_token_no_file` -- raises AuthenticationError

### Implementation
- Create `youtube_updater/core/restream_auth.py` (~120 lines)
  - Class `RestreamAuth` with `authenticate()`, `load_token()`, `refresh_token()`, `get_valid_token()`
  - Reuses patterns from `validate_restream.py`
  - Token file: `{"access_token", "refresh_token", "client_id", "client_secret", "expires_at"}`
  - Saves with 0o600 permissions (NF2)

### Integration test
- `tests/integration/test_restream_auth_integration.py`:
  - Full cycle: authenticate (mocked HTTP) -> save token -> load token -> refresh -> verify file state
  - Verify token file permissions are preserved across operations

### E2E test
- `tests/smoke/test_restream_smoke.py`:
  - CLI restream-auth with mocked OAuth server -> exit 0, token file created
  - CLI restream-auth with simulated failure -> exit 1, error on stderr

### Gate 2 exit criteria:
- [ ] `pytest tests/unit/test_restream_auth.py` -- all 9 tests pass
- [ ] `pytest tests/integration/test_restream_auth_integration.py` -- full auth cycle pass
- [ ] `pytest tests/smoke/test_restream_smoke.py` -- E2E CLI auth pass
- [ ] `pytest tests/acceptance/test_ac_1_auth.py` -- AC 1.1, 1.2, 1.3 pass
- [ ] `pytest tests/acceptance/test_ac_4_token.py` -- AC 4.1, 4.2 pass
- [ ] `pytest tests/acceptance/test_nf.py::test_nf2` -- 0o600 permissions pass
- [ ] `pytest tests/ -v` -- full suite green, no regressions
- [ ] CI green

**PR:** `claude/phase-2-restream-auth-caLjf` -> `claude/castr-api-integration-caLjf`

---

## Phase 3: Restream Client + Core Integration (AC 2.1, 2.2, 3.1-3.5)

**Branch:** `claude/phase-3-restream-client-caLjf` off `claude/castr-api-integration-caLjf`

### ATTD: Acceptance tests (red)
- `test_ac_2_status.py::test_ac_2_1` -- restream-status lists connected channels
- `test_ac_2_status.py::test_ac_2_2` -- missing creds -> error directing to restream-auth
- `test_ac_3_update.py::test_ac_3_1` -- update --mode restream PATCHes title, archives, exits 0
- `test_ac_3_update.py::test_ac_3_2` -- update --mode youtube same as existing behavior
- `test_ac_3_update.py::test_ac_3_3` -- update (no flag) defaults to youtube
- `test_ac_3_update.py::test_ac_3_4` -- --wait polls until stream data available
- `test_ac_3_update.py::test_ac_3_5` -- missing/expired creds -> error + email + exit 1
- `test_nf.py::test_nf1` -- existing YouTube tests still pass (regression gate)

### TDD: Unit tests (red)
- `tests/unit/test_restream_client.py`:
  - `test_get_channels_success` -- mock GET /user/channel/all
  - `test_get_channels_auth_error` -- 401 -> RestreamAPIError
  - `test_get_stream_info_success` -- mock GET /user/stream
  - `test_get_stream_info_not_streaming` -- 404 -> None
  - `test_update_stream_title_success` -- mock PATCH /user/stream
  - `test_update_stream_title_failure` -- 500 -> RestreamAPIError

- `tests/unit/test_core.py` (additions):
  - `test_update_title_restream_success` -- title updated, archived
  - `test_update_title_restream_no_client` -- raises error
  - `test_update_title_restream_no_titles` -- raises error

- `tests/unit/test_cli_restream.py`:
  - `test_restream_status_lists_channels` -- mock client, verify output
  - `test_restream_status_no_creds` -- exit 1 with message
  - `test_update_mode_restream` -- routes to restream handler
  - `test_update_mode_youtube_default` -- routes to existing handler
  - `test_update_mode_restream_wait` -- polls then updates
  - `test_update_mode_restream_no_creds_sends_email` -- exit 1 + email

### Implementation
- Create `youtube_updater/core/restream_client.py` (~80 lines)
  - Class `RestreamClient` with `get_channels()`, `get_stream_info()`, `update_stream_title()`
- Modify `youtube_updater/core/__init__.py` -- add `restream_client`, `email_notifier`, `update_title_restream()`
- Modify `youtube_updater/core/factory.py` -- wire Restream + email into core
- Modify `youtube_updater/cli.py` -- add `restream-auth`, `restream-status`, `--mode` flag, `_handle_auth_failure()`

### Integration test
- `tests/integration/test_restream_workflow.py`:
  - Core with mock Restream client -> update title -> verify archive
  - CLI integration: subprocess call with --mode restream (mocked API)

### E2E test
- `tests/smoke/test_restream_smoke.py`:
  - CLI update --mode restream with mocked HTTP -> exit 0
  - CLI restream-status with mocked HTTP -> channel listing
  - CLI update --mode restream without creds -> exit 1

### Gate 3 exit criteria:
- [ ] `pytest tests/unit/test_restream_client.py` -- all 6 tests pass
- [ ] `pytest tests/unit/test_cli_restream.py` -- all 6 tests pass
- [ ] `pytest tests/unit/test_core.py` -- new restream tests + existing pass
- [ ] `pytest tests/integration/test_restream_workflow.py` -- core->update->archive pass
- [ ] `pytest tests/smoke/test_restream_smoke.py` -- E2E pass
- [ ] `pytest tests/acceptance/test_ac_2_status.py` -- AC 2.1, 2.2 pass
- [ ] `pytest tests/acceptance/test_ac_3_update.py` -- AC 3.1-3.5 pass
- [ ] `pytest tests/acceptance/test_nf.py::test_nf1` -- no regression
- [ ] `pytest tests/ -v` -- full suite green
- [ ] CI green

**PR:** `claude/phase-3-restream-client-caLjf` -> `claude/castr-api-integration-caLjf`

---

## Phase 4: Email Notifications (AC 1.3, 3.5 -- email paths)

**Branch:** `claude/phase-4-email-notifications-caLjf` off `claude/castr-api-integration-caLjf`

### ATTD: Acceptance tests
- Verify `test_ac_1_auth.py::test_ac_1_3` exercises email sending path
- Verify `test_ac_3_update.py::test_ac_3_5` exercises email sending path

### TDD: Unit tests (red)
- `tests/unit/test_email_notifier.py`:
  - `test_send_error_notification_success` -- mock ACS EmailClient, verify message sent
  - `test_send_error_notification_failure_no_raise` -- ACS throws, returns False, no exception
  - `test_send_error_notification_returns_true` -- success returns True

- `tests/unit/test_cli_restream.py` (additions):
  - `test_configure_email_saves_config` -- verify file written
  - `test_test_email_sends_test_message` -- verify email sent

### Implementation
- Create `youtube_updater/notifications/__init__.py`
- Create `youtube_updater/notifications/email_notifier.py` (~50 lines)
- Modify `youtube_updater/cli.py` -- add `configure-email`, `test-email` subcommands

### Integration test
- `tests/integration/test_email_integration.py`:
  - Auth failure -> `_handle_auth_failure()` -> `email_notifier.send` called
  - configure-email -> file written -> test-email -> notifier invoked

### E2E test
- `tests/smoke/test_restream_smoke.py`:
  - CLI configure-email -> file written -> test-email (mocked ACS) -> exit 0
  - CLI auth failure (mocked) -> email_notifier.send called

### Gate 4 exit criteria:
- [ ] `pytest tests/unit/test_email_notifier.py` -- all 3 tests pass
- [ ] `pytest tests/unit/test_cli_restream.py` -- email CLI tests pass
- [ ] `pytest tests/integration/test_email_integration.py` -- auth failure->email cycle pass
- [ ] `pytest tests/smoke/test_restream_smoke.py` -- E2E pass
- [ ] `pytest tests/acceptance/test_ac_1_auth.py::test_ac_1_3` -- pass with email verification
- [ ] `pytest tests/acceptance/test_ac_3_update.py::test_ac_3_5` -- pass with email verification
- [ ] `pytest tests/ -v` -- full suite green
- [ ] CI green

**PR:** `claude/phase-4-email-notifications-caLjf` -> `claude/castr-api-integration-caLjf`

---

## Phase 5: OBS Integration (AC 5.1, 5.2)

**Branch:** `claude/phase-5-obs-integration-caLjf` off `claude/castr-api-integration-caLjf`

### ATTD: Acceptance tests (red)
- `test_ac_5_obs.py::test_ac_5_1` -- Lua script contains Mode dropdown property
- `test_ac_5_obs.py::test_ac_5_2` -- Lua script appends --mode flag to command

### Implementation
- Modify `obs_scripts/youtube_title_updater.lua` -- add Mode dropdown, pass --mode flag

### Gate 5 exit criteria:
- [ ] `pytest tests/acceptance/test_ac_5_obs.py` -- AC 5.1, 5.2 pass
- [ ] Lua script contains `obs_properties_add_list` with "mode" property (grep verified)
- [ ] Lua script contains `--mode` flag in command construction (grep verified)
- [ ] `pytest tests/ -v` -- full suite green
- [ ] CI green

**PR:** `claude/phase-5-obs-integration-caLjf` -> `claude/castr-api-integration-caLjf`

---

## Final Gate: Full Integration PR

**PR:** `claude/castr-api-integration-caLjf` -> `main`

**Exit criteria:**
- [ ] All 18 acceptance criteria (AC 1.1-5.2, NF1-NF4) have passing tests
- [ ] All unit tests pass: `pytest tests/unit/`
- [ ] All integration tests pass: `pytest tests/integration/`
- [ ] All smoke/E2E tests pass: `pytest tests/smoke/`
- [ ] All acceptance tests pass: `pytest tests/acceptance/`
- [ ] Full suite with coverage: `pytest tests/ --cov=youtube_updater`
- [ ] GitHub Actions CI green on all matrix
- [ ] No regressions in existing YouTube-only functionality
- [ ] `docs/plan.md` committed and up-to-date

---

## NF4 Safeguard: Protecting YouTube Auth Files

No phase reads or writes `token.json`, `credentials.json`, or `pickle.json`. Specifically:
- `RestreamAuth` writes only to `restream_token.json`
- `EmailNotifier` config writes only to `email_config.json`
- `ConfigManager.save_email_config()` includes an assertion that the target filename is `email_config.json`
- Existing `AuthManager` code is not modified at all

Acceptance test `test_nf.py::test_nf4` verifies: snapshot file mtimes of YouTube auth files before and after Restream/email operations, assert unchanged.

---

## Files Summary

| Action | File | Phase | ACs |
|--------|------|-------|-----|
| Create | `docs/plan.md` | 0 | -- |
| Create | `.github/workflows/ci.yml` | 0 | -- |
| Create | `tests/acceptance/` (6 test files + conftest) | 0-5 | All |
| Modify | `requirements.txt` | 1 | NF3 |
| Modify | `youtube_updater/exceptions/custom_exceptions.py` | 1 | -- |
| Modify | `youtube_updater/core/config_manager.py` | 1 | NF4 |
| Create | `youtube_updater/core/restream_auth.py` | 2 | 1.1, 1.2, 4.1, 4.2 |
| Create | `youtube_updater/core/restream_client.py` | 3 | 2.1, 3.1 |
| Modify | `youtube_updater/core/__init__.py` | 3 | 3.1 |
| Modify | `youtube_updater/core/factory.py` | 3 | -- |
| Modify | `youtube_updater/cli.py` | 3, 4 | All CLI |
| Create | `youtube_updater/notifications/__init__.py` | 4 | -- |
| Create | `youtube_updater/notifications/email_notifier.py` | 4 | 1.3, 3.5 |
| Modify | `obs_scripts/youtube_title_updater.lua` | 5 | 5.1, 5.2 |
| Create | `tests/integration/test_config_restream.py` | 1 | -- |
| Create | `tests/integration/test_restream_auth_integration.py` | 2 | -- |
| Create | `tests/integration/test_restream_workflow.py` | 3 | -- |
| Create | `tests/integration/test_email_integration.py` | 4 | -- |
| Create | `tests/smoke/test_restream_smoke.py` | 3 | -- |
| Create | `tests/unit/test_restream_auth.py` | 2 | -- |
| Create | `tests/unit/test_restream_client.py` | 3 | -- |
| Create | `tests/unit/test_email_notifier.py` | 4 | -- |
| Create | `tests/unit/test_cli_restream.py` | 3, 4 | -- |
| Create | `tests/unit/test_nf4_safeguard.py` | 1 | NF4 |
