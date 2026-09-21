# Batch N — Multi-account Operations Dashboard & Production Readiness Gate

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** PASS

## Goal

Create a single operations/control-plane view for all authorized TikTok personal accounts and replace subjective production-readiness judgments with explicit PASS/WARN/FAIL checks.

## Delivered

### Operations Control Center

Added:

- `GET /api/operations/summary`
- `POST /api/operations/bulk`

Per-account operations health includes:

- TikTok account status
- granted scopes
- scopes missing from the currently configured application scope set
- access-token expiry
- refresh-token expiry
- profile-sync age
- stored video count
- scheduled post count
- running post count
- failed Direct Post count
- failed Draft count
- webhook error count
- calculated health:
  - `OK`
  - `WARNING`
  - `ERROR`
- explicit issue list

### Safe bulk actions

The admin may select up to 50 account IDs and explicitly run:

- `REFRESH_TOKENS`
- `SYNC_PROFILE`
- `SYNC_VIDEOS`

Rules:

- actions only run after explicit admin request;
- each account is processed independently;
- one failure does not stop the remaining selected accounts;
- revoked accounts are rejected;
- OAuth failures can mark an account `REAUTH_REQUIRED`;
- per-account success/failure is returned to the UI;
- actions create audit events;
- no bulk action was run against live TikTok during Batch N acceptance.

### Production Readiness Gate

Added:

- `GET /api/operations/production-readiness`

Checks currently include:

1. application environment;
2. TikTok environment;
3. OAuth configuration;
4. HTTPS OAuth redirect;
5. HTTPS frontend origin;
6. all supported personal-account scopes configured;
7. at least one connected TikTok account;
8. account/scope health;
9. all required background workers alive;
10. PostgreSQL backup freshness;
11. database migration version;
12. webhook processing errors/backlog;
13. stuck publish queue;
14. Terms and Privacy pages.

The gate reports:

- `READY` only when there are zero FAIL checks;
- `NOT_READY` when one or more FAIL checks exist.

Warnings do not get silently converted into PASS.

## Admin UI

Added **Operations Control Center**:

- fleet/account summary cards;
- per-account health table;
- checkbox multi-select;
- bulk token refresh;
- bulk profile sync;
- bulk video sync;
- token lifetime visibility;
- profile sync age;
- publishing state;
- expandable issue details.

Added **Production Readiness** panel:

- overall READY / NOT_READY;
- PASS / WARN / FAIL counters;
- every gate item with exact reason.

Both panels refresh from live backend state.

## Current runtime acceptance

Operations summary:

- Accounts: 1
- Connected accounts: 1
- Accounts needing attention relative to currently configured scopes: 0
- Scheduled posts: 0
- Running posts: 0
- Failed posts: 0
- Pending webhooks: 0
- Error webhooks: 0
- Account id 7 health: `OK`

Important distinction:

Account id 7 is healthy relative to the **currently configured scope set**, which is only `user.info.basic`.

The production gate separately checks the project's target of supporting **all personal-account API capabilities** and therefore correctly reports missing advanced scopes.

## Production Gate result

Current result:

- Status: `NOT_READY`
- PASS: 11
- WARN: 0
- FAIL: 3

Current FAIL checks:

1. `APP_ENV=development`
2. `TIKTOK_ENVIRONMENT=sandbox`
3. Missing target scopes:
   - `user.info.profile`
   - `user.info.stats`
   - `video.list`
   - `video.upload`
   - `video.publish`

Current PASS checks include:

- OAuth configuration
- HTTPS redirect URI
- HTTPS frontend origin
- connected TikTok account
- worker processes
- recent PostgreSQL backup
- migration version `0011_publish_scheduler`
- webhook processing state
- publishing queue state
- Terms page
- Privacy page

## Acceptance evidence

- Backend Ruff: PASS
- Backend Pytest: 38/38 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS
- OpenAPI operations routes: present
- Public admin: HTTP 200
- Public Terms: HTTP 200
- Public Privacy: HTTP 200
- PostgreSQL: UP
- Cache: UP
- Backend: UP
- Frontend: UP
- TokenWorker: UP
- SchedulerWorker: UP
- WebhookWorker: UP
- PublishWorker: UP
- DraftWorker: UP
- AnalyticsWorker: UP
- Ngrok: UP
- Watchdog: UP

## Test coverage added

Regression tests verify:

- operations account aggregation;
- missing-scope visibility;
- production gate returns complete detailed checks;
- bulk action dispatch can be mocked without a live TikTok request.

## No schema migration

Batch N does not add a database migration.

It intentionally derives operational state from existing source-of-truth tables instead of duplicating health/status records.

## Remaining production blockers

The application should not be labeled production-ready yet.

External/application configuration still needs to move from:

- development → production
- Sandbox → Production

and TikTok must enable/approve the required personal-account scopes before those features can be tested live.

## Next engineering batch

Batch O — Production Review Package + real-scope E2E acceptance matrix.
