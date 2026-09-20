# Batch C — TikTok Profile Sync

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** PASS

## Delivered

- Added migration `0003_tiktok_profile`.
- Added profile fields to `tiktok_accounts`:
  - `union_id`
  - `display_name`
  - `avatar_url`
  - `profile_synced_at`
- Added TikTok User Info API client using `GET /v2/user/info/`.
- Added server-side profile synchronization service.
- Added `POST /api/tiktok/accounts/{id}/sync-profile`.
- Extended account API responses with profile metadata.
- Updated frontend account cards to display avatar + display name.
- Added **Sync profile** action.
- Added regression test for profile synchronization.

## P0 hardening completed in the same batch

- Disabled raw Uvicorn access logging.
- Added sanitized request logging that records path only and never query strings.
- Verified OAuth `code` and `state` do not appear in backend logs.
- Isolated OAuth configuration test from live `.env`.
- Deduplicated `FRONTEND_ORIGIN` in `.env`.

## Live acceptance evidence

- PostgreSQL: UP
- Cache: UP
- Backend: UP
- Frontend: UP
- TokenWorker: UP
- Ngrok: UP
- Alembic: `0003_tiktok_profile (head)`
- Backend Ruff: PASS
- Backend Pytest: 9/9 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS
- Public frontend: HTTP 200

## Live TikTok account

Account `id=7`:
- status: `CONNECTED`
- scope: `user.info.basic`
- profile sync: PASS
- display name received from TikTok
- avatar received from TikTok
- union id received from TikTok
- manual token refresh: PASS
- last token refresh timestamp stored

Raw access tokens, refresh tokens, authorization codes, state values and client secrets are not written to application logs or UI.
