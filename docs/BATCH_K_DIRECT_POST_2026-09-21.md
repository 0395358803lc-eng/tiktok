# Batch K — TikTok Direct Post Studio

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** CODE PASS / LIVE DIRECT POST WAITS FOR `video.publish`

## Goal

Implement TikTok Content Posting API Direct Post for authorized personal accounts using:

- `video.publish`

## Delivered

- Added `video.publish` to the Dynamic Scope Manager.
- Added migration `0009_direct_post`.
- Added `tiktok_publish_jobs`.
- Added duration metadata to `media_assets`.
- Added protected Media Library preview endpoint.
- Added Creator Info integration:
  - `POST /v2/post/publish/creator_info/query/`
- Added Direct Post video initialization:
  - `POST /v2/post/publish/video/init/`
- Added Direct Post photo initialization:
  - `POST /v2/post/publish/content/init/`
- Added Direct Post status polling:
  - `POST /v2/post/publish/status/fetch/`
- Added a dedicated PublishWorker.
- PublishWorker is managed by native start/stop/status/watchdog.

## Review-safe Creator Info behavior

Creator Info is queried:

1. when the Direct Post screen is rendered for an authorized account;
2. again on the backend before a post job is queued;
3. again by PublishWorker immediately before TikTok initialization.

The application uses current Creator Info to enforce:

- allowed privacy options;
- comment availability;
- Duet availability;
- Stitch availability;
- maximum video duration.

## User-control requirements implemented

- Privacy has no default value.
- User must manually choose privacy.
- Comment/Duet/Stitch are OFF by default.
- Interactions disabled by TikTok are disabled in the UI and rejected by backend validation.
- Video/photo preview is shown before post.
- Commercial-content disclosure is OFF by default.
- If commercial disclosure is enabled, at least one of:
  - Your brand
  - Branded content
  must be selected.
- Branded content cannot use SELF_ONLY visibility.
- AI-generated-content disclosure is available.
- Music Usage Confirmation consent is mandatory.
- Branded Content Policy consent is mandatory when Branded content is selected.

## Video Direct Post

- Local MP4/MOV/WebM from Media Library.
- Browser extracts video duration at upload time.
- Backend stores duration metadata.
- A video without duration metadata cannot be directly posted.
- Backend rejects videos exceeding Creator Info max duration.
- Caption maximum: 2200 UTF-16 units.
- Optional cover-frame timestamp is validated against video duration.
- TikTok FILE_UPLOAD uses sequential Content-Range upload.

## Photo Direct Post

- 1–35 verified public HTTPS image URLs.
- Cover index validation.
- Title maximum: 90 UTF-16 units.
- Description maximum: 4000 UTF-16 units.
- Optional recommended music.
- Photo post uses:
  - `post_mode=DIRECT_POST`
  - `media_type=PHOTO`
  - `source=PULL_FROM_URL`

## API routes

- `POST /api/tiktok/accounts/{id}/creator-info`
- `GET /api/tiktok/publish-jobs`
- `POST /api/tiktok/accounts/{id}/publish/video`
- `POST /api/tiktok/accounts/{id}/publish/photo`
- `POST /api/tiktok/publish-jobs/{id}/refresh`
- `GET /api/tiktok/media/{id}/content`

## Publish job lifecycle

Local/remote states can include:

- `QUEUED`
- `INITIALIZING`
- `UPLOADING`
- `SUBMITTED`
- TikTok processing states
- `PUBLISH_COMPLETE`
- `FAILED`

Public post IDs returned by TikTok are persisted when available.

## Audit events

- `DIRECT_POST_QUEUED`
- `DIRECT_POST_SUBMITTED`
- `DIRECT_POST_STATUS_CHANGED`
- `DIRECT_POST_COMPLETE`
- `DIRECT_POST_FAILED`

## Acceptance evidence

- Alembic: `0009_direct_post (head)`
- Backend Ruff: PASS
- Backend Pytest: 27/27 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS

Regression tests verify:

- privacy option validation;
- mandatory Music Usage consent;
- branded-content visibility restriction;
- creator interaction restrictions;
- creator max-duration enforcement;
- PublishWorker transition from QUEUED to PUBLISH_COMPLETE using mocked TikTok APIs.

## Current live permission state

The current connected account has not granted `video.publish`.

The application therefore does not attempt a live Direct Post until:

1. Content Posting API Direct Post is enabled in TikTok Developer Portal;
2. `video.publish` is approved/enabled;
3. the account reconnects and authorizes `video.publish`.

## TikTok review note

Unaudited Direct Post clients are subject to TikTok visibility restrictions. Production visibility depends on TikTok audit/review approval.

## Next engineering batch

Batch L — Webhooks / publishing-event ingestion and idempotent event processing.

## Live runtime acceptance

- PostgreSQL: UP
- Cache: UP
- Backend: UP
- Frontend: UP
- TokenWorker: UP
- PublishWorker: UP
- DraftWorker: UP
- AnalyticsWorker: UP
- Ngrok: UP
- Watchdog: UP
- PublishWorker first cycle: submitted=0, polled=0
- Public admin: HTTP 200
- Current account id 7: CONNECTED
- Current account id 7 scopes: user.info.basic
- Current video.publish enabled: false
- Current Direct Post jobs for account id 7: 0
- No live Direct Post request was attempted without permission
- PostgreSQL backup: runtime/backups/th_tiktok_20260920T233426Z.dump
- Backup archive validation: PASS
