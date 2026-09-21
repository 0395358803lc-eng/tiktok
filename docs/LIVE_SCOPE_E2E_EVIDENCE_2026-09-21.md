# Live Scope E2E Evidence — 2026-09-21

## Environment

- TikTok environment: `sandbox`
- Connected account: internal account id `7`
- Current granted scope set: `user.info.basic`
- Raw access/refresh token values are intentionally excluded from this document.

## Real API acceptance — user.info.basic

A real TikTok User Info synchronization was executed using the currently connected Sandbox account.

Observed evidence:

- account status: `CONNECTED`
- account open_id matched the TikTok User Info response
- display name returned: present
- avatar URL returned: present
- profile synchronization timestamp advanced from:
  - `2026-09-20 22:58:48.746405+00:00`
  - to `2026-09-21 00:20:57.666021+00:00`
- `PROFILE_SYNCED` audit events after the test: `3`
- username/extended-profile field: absent, as expected without `user.info.profile`
- statistics fields: absent, as expected without `user.info.stats`

Result:

`user.info.basic = LIVE PASS`

This result used the real TikTok API and was not generated from mocked responses.

## Advanced-scope preflight

The application-side scope preflight was executed after the live basic-profile sync.

Current configuration:

`user.info.basic`

Results:

| Scope | Result | Detail |
|---|---|---|
| `user.info.basic` | PASS | OAuth requestable |
| `user.info.profile` | BLOCKED | Scope is not enabled for this app |
| `user.info.stats` | BLOCKED | Scope is not enabled for this app |
| `video.list` | BLOCKED | Scope is not enabled for this app |
| `video.upload` | BLOCKED | Scope is not enabled for this app |
| `video.publish` | BLOCKED | Scope is not enabled for this app |

Summary:

- configured: `1`
- supported by application code: `6`
- blocked by current app configuration: `5`

## Interpretation

The five advanced scopes are not marked as failures of the application implementation.

They remain blocked because they are not yet enabled in the current TikTok Developer Portal app configuration and therefore cannot be requested in OAuth or granted by the Sandbox user.

The application intentionally prevents requesting scopes that are not configured for the app.

## Next live acceptance sequence

After each intended scope is enabled in TikTok Developer Portal:

1. update `TIKTOK_SCOPES` on the server to include only scopes that are actually enabled in the Portal;
2. restart the application;
3. run `./scripts/scope-e2e-preflight.sh`;
4. reconnect the Sandbox target account;
5. confirm TikTok authorization includes the new scope;
6. run the matching real API workflow;
7. retain UI, DB, audit and webhook evidence;
8. update the Review Package gate.

Do not mark an advanced scope PASS until TikTok grants it to the connected account and the real endpoint/workflow succeeds.
