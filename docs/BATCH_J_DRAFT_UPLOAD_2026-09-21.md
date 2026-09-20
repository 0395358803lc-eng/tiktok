# Batch J — TikTok Draft Upload Studio

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** CODE PASS / LIVE TIKTOK UPLOAD WAITS FOR `video.upload`

## Goal

Implement the Content Posting API draft workflow for authorized personal TikTok accounts using:

- `video.upload`

## Delivered

- Added `video.upload` to the Dynamic Scope Manager.
- Added migration `0008_draft_uploads`.
- Added local `media_assets` storage metadata.
- Added `tiktok_draft_jobs`.
- Added protected local Media Library for video staging.
- Supported local video MIME types:
  - MP4
  - MOV
  - WebM
- Configured maximum staged video size: 4 GB.
- Media files are stored under `runtime/media` and are excluded from Git.
- Stored media files use generated names and permission 600.
- Added SHA-256 hash for each stored media asset.

## Video draft flow

1. User uploads video into local Media Library.
2. User selects an authorized TikTok account.
3. User queues a Draft Job.
4. DraftWorker initializes TikTok upload at:
   - `/v2/post/publish/inbox/video/init/`
5. TikTok returns `publish_id` and `upload_url`.
6. DraftWorker uploads the file sequentially with Content-Range.
7. DraftWorker polls:
   - `/v2/post/publish/status/fetch/`
8. Job status is persisted in PostgreSQL.
9. When status becomes `SEND_TO_USER_INBOX`, the user is informed to open TikTok and finish editing/posting.

## Chunk behavior

The worker follows TikTok media transfer restrictions:

- video below or equal to 64 MB: one chunk
- larger videos: 64 MB base chunk size
- sequential Content-Range upload
- final chunk can absorb trailing bytes up to TikTok's allowed final-chunk size
- maximum 1000 chunks

## Photo draft flow

Photo upload uses:

- `/v2/post/publish/content/init/`
- `post_mode=MEDIA_UPLOAD`
- `media_type=PHOTO`
- `source=PULL_FROM_URL`

Backend validation:

- 1 to 35 images
- HTTPS URLs only
- cover index must exist
- title maximum 90 characters
- description maximum 4000 characters
- optional AI-generated-content flag

TikTok still requires the image URLs to belong to a verified URL prefix/domain.

## Draft statuses

The system supports local/remote states including:

- `QUEUED`
- `INITIALIZING`
- `UPLOADING`
- `SUBMITTED`
- `PROCESSING_UPLOAD`
- `PROCESSING_DOWNLOAD`
- `SEND_TO_USER_INBOX`
- `PUBLISH_COMPLETE`
- `FAILED`

DraftWorker reduces polling frequency after `SEND_TO_USER_INBOX`.

## API routes

- `GET /api/tiktok/media`
- `POST /api/tiktok/media/video`
- `GET /api/tiktok/drafts`
- `POST /api/tiktok/accounts/{id}/drafts/video`
- `POST /api/tiktok/accounts/{id}/drafts/photo`
- `POST /api/tiktok/drafts/{id}/refresh`

## Runtime

DraftWorker is integrated into:

- start-native
- stop-native
- status-native
- watchdog
- log rotation

Default worker interval:

`DRAFT_WORKER_INTERVAL_SECONDS=30`

## Acceptance evidence

- Alembic: `0008_draft_uploads (head)`
- Backend Ruff: PASS
- Backend Pytest: 23/23 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS
- DraftWorker: UP
- DraftWorker startup cycle: submitted=0, polled=0
- Public admin: HTTP 200
- Current configured scopes: `user.info.basic`
- Current account id 7 scopes: `user.info.basic`
- `video.upload` enabled: false
- Current draft jobs for account id 7: 0
- Current staged test media assets: 0
- No live TikTok upload was attempted without permission

## Validation limitation

The server environment currently does not provide `ffprobe`. Local pre-validation therefore checks MIME type and file size. TikTok remains the authoritative validator for codec, frame rate, resolution and duration during processing.

## Next external action

In TikTok Developer Portal / Sandbox:

1. Add/enable Content Posting API.
2. Request/enable `video.upload`.
3. Apply changes.
4. Update live scopes to include `video.upload`.
5. Reconnect the target account and authorize the new permission.
6. Run one real video draft and confirm `SEND_TO_USER_INBOX`.

## Next engineering batch

Batch K — Direct Post Studio using `video.publish`.
