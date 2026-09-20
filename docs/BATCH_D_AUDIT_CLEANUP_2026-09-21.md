# Batch D — OAuth Cleanup & Audit Trail

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** PASS

## Delivered

- Added migration `0004_audit_events`.
- Added append-only `audit_events` table.
- Added protected `GET /api/audit/events` endpoint.
- Added admin UI panel for recent audit activity.
- Added audit events for:
  - `ADMIN_LOGIN`
  - `ADMIN_LOGOUT`
  - `ACCOUNT_CONNECTED`
  - `PROFILE_SYNCED`
  - `TOKEN_REFRESHED`
  - `ACCOUNT_REAUTH_REQUIRED`
  - `ACCOUNT_ERROR`
  - `ACCOUNT_DISCONNECTED`
- Audit records do not contain access tokens, refresh tokens, OAuth codes, state values, passwords or client secrets.
- Added OAuth-session cleanup to the native TokenWorker.
- Expired OAuth states are removed automatically.
- Consumed OAuth states are retained for a bounded period and then cleaned.
- Added `OAUTH_SESSION_RETENTION_SECONDS` with default 86400 seconds.

## Regression protection

- Added audit endpoint authorization test.
- Added OAuth cleanup behavior test.
- Added an autouse test fixture to remove audit/admin-session side effects created by the test suite.
- Verified the test suite no longer leaves fake audit records in the development database.

## Acceptance evidence

- Alembic: `0004_audit_events (head)`
- Backend Ruff: PASS
- Backend Pytest: 11/11 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS
- OAuth cleanup runtime test: expired fixture count 1 -> 0
- TokenWorker log: `OAuth session cleanup removed=1`
- Live profile sync produced a real `PROFILE_SYNCED` audit event for account id 7
- Public frontend: HTTP 200
