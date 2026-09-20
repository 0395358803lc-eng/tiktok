# Batch I — Personal Analytics Engine

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** CODE PASS / LIVE DATA WAITS FOR TIKTOK SCOPES

## Goal

Build real historical analytics for authorized personal TikTok accounts without simulated metrics.

## Delivered

- Added migration `0007_analytics_snapshots`.
- Added `account_stat_snapshots`.
- Added `video_metric_snapshots`.
- Account snapshots store:
  - follower count
  - following count
  - likes count
  - video count
  - capture timestamp
- Video snapshots store:
  - views
  - likes
  - comments
  - shares
  - capture timestamp
- Profile sync automatically snapshots real account statistics when available.
- Video sync/refresh automatically snapshots real video metrics when available.
- Added a five-minute deduplication window for unchanged metrics.
- Added historical report ranges:
  - 7 days
  - 30 days
  - 90 days
- Added account growth deltas.
- Added per-video metric deltas.
- Added top-video ranking by view growth.
- Added protected endpoint:
  - `GET /api/tiktok/accounts/{id}/analytics?days=7|30|90`
- Added AnalyticsWorker.
- AnalyticsWorker default interval: 21600 seconds (6 hours).
- AnalyticsWorker default video refresh cap: 100 stored videos per cycle.
- Worker only uses scopes actually granted by the account.
- Added watchdog/start/stop/status integration for AnalyticsWorker.
- Added admin Analytics panel with:
  - account selector
  - 7/30/90-day range selector
  - follower/following/likes/video deltas
  - follower history line
  - top video growth
  - explicit no-data state when real history does not exist

## No fake data policy

The analytics engine never invents historical observations.

If `user.info.stats` is not granted, account-stat snapshots are not created.

If `video.list` is not granted, video-metric snapshots are not created.

A chart requires at least two real observations.

## Acceptance evidence

- Alembic: `0007_analytics_snapshots (head)`
- Backend Ruff: PASS
- Backend Pytest: 20/20 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS
- Analytics API 7 days: HTTP 200
- Analytics API 30 days: HTTP 200
- Analytics API 90 days: HTTP 200
- Current account id 7 account snapshots: 0
- Current account id 7 video snapshots: 0
- This zero state is expected because the account currently has only `user.info.basic`.
- Public admin: HTTP 200

## Regression evidence

Automated tests verify:

- account delta calculation from two real snapshots
- video view/like/comment/share delta calculation
- snapshot persistence
- no fabricated values

## Scope dependency

For account growth history:

`user.info.stats`

For video performance history:

`video.list`

Once these scopes are enabled in TikTok Developer Portal and the account reauthorizes them, AnalyticsWorker will begin building the 7/30/90-day history automatically.

## Next engineering batch

Batch J — Content Upload / Draft workflow using `video.upload`.
