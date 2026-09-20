# Batch H — TikTok Video Library

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** CODE PASS / video.list PENDING TIKTOK PORTAL ENABLEMENT

## Goal

Add a personal-account Video Library using TikTok Display API scope:

- `video.list`

## Delivered

- Added `video.list` to the Dynamic Scope Manager.
- Added migration `0006_tiktok_videos`.
- Added PostgreSQL table `tiktok_videos`.
- Added support for TikTok v2:
  - `POST /v2/video/list/`
  - `POST /v2/video/query/`
- Added local metadata persistence for:
  - video id
  - create time
  - cover image URL
  - share URL
  - description
  - duration
  - dimensions
  - title
  - embed link
  - like count
  - comment count
  - share count
  - view count
  - AI-generated-content flag
  - sync timestamp
- Added pagination support using TikTok cursor.
- Added maximum 20 videos per TikTok API request.
- Added metadata refresh by up to 20 video IDs.
- Added audit events:
  - `VIDEOS_SYNCED`
  - `VIDEOS_REFRESHED`
- Added protected API routes:
  - `GET /api/tiktok/accounts/{id}/videos`
  - `POST /api/tiktok/accounts/{id}/videos/sync`
  - `POST /api/tiktok/accounts/{id}/videos/refresh`
- Added admin Video Library UI.
- Added account selector.
- Added Sync latest.
- Added cursor-based Sync older.
- Added Refresh metadata.
- Added views/likes/comments/shares display.
- Added links to TikTok share/embed URLs.
- Added explicit UI notice when `video.list` has not been granted.

## Permission behavior

The application never calls TikTok's video APIs unless the selected account actually granted:

`video.list`

The local video library remains readable even when the account no longer has the scope.

## Acceptance evidence

- Alembic: `0006_tiktok_videos (head)`
- Backend Ruff: PASS
- Backend Pytest: 18/18 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS
- Runtime services: UP
- Public admin: HTTP 200
- Current `video.list` capability: Not enabled
- Local library for account id 7: HTTP 200, 0 stored videos
- Sync without `video.list`: HTTP 409
- No unauthorized TikTok video API call was performed

## TikTok API behavior accounted for

- `/v2/video/list/` returns public videos for the authorized account.
- Maximum page size: 20.
- Cursor pagination is supported.
- Cover image URLs are temporary and can expire.
- `/v2/video/query/` is used to refresh stored video metadata/cover URLs.

## Next external action

In TikTok Developer Portal / Sandbox, enable and apply:

`video.list`

Then update the live environment to include it:

`TIKTOK_SCOPES=user.info.basic,video.list`

or, after the advanced profile scopes are also approved:

`TIKTOK_SCOPES=user.info.basic,user.info.profile,user.info.stats,video.list`

Reconnect the account and approve the new permission before running Video Library sync.

## Next engineering batch

Batch I — Analytics snapshots and 7/30/90-day reporting.
