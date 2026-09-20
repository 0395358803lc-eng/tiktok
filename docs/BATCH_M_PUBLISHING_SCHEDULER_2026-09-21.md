# Batch M — Publishing Scheduler & Queue Management

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** PASS

## Goal

Add internal scheduling and queue management on top of the existing TikTok Direct Post flow without pretending that TikTok provides an application-side scheduling endpoint.

The application stores schedule state in PostgreSQL and only releases a Direct Post job when its scheduled time is due.

## Delivered

- Added migration `0011_publish_scheduler`.
- Extended `tiktok_publish_jobs` with:
  - `scheduled_at`
  - `schedule_status`
  - `retry_count`
  - `max_retries`
  - `next_attempt_at`
  - `last_attempt_at`
  - `canceled_at`
- Added queue states:
  - `SCHEDULED`
  - `READY`
  - `RUNNING`
  - `COMPLETED`
  - `FAILED`
  - `CANCELED`
- Kept TikTok remote post status separate from internal schedule state.
- Added dedicated SchedulerWorker.
- SchedulerWorker default interval: 10 seconds.
- SchedulerWorker default ready batch size: 50.
- Added internal queue promotion:
  - due `SCHEDULED` job → `READY`
  - PublishWorker consumes only `READY` jobs
  - submitted job → `RUNNING`
  - TikTok completion → `COMPLETED`
  - TikTok failure → `FAILED`
- Webhook completion/failure events also update schedule state.

## Safe retry policy

Automatic retries are deliberately conservative.

Auto-retry is only allowed when Creator Info fails because of a network error **before TikTok publish initialization creates a `publish_id`**.

Retry backoff:

- base: `PUBLISH_RETRY_BASE_SECONDS=300`
- exponential backoff
- capped at 3600 seconds
- per-job `max_retries`: 0–5

Once a job has a TikTok `publish_id`, the application does not automatically initialize a second post. This avoids duplicate publishing.

Manual retry is only allowed when:

- local state is `FAILED`;
- no `publish_id` exists;
- `retry_count < max_retries`.

## Queue management API

- `GET /api/tiktok/publish-schedule?days=7|30`
- `POST /api/tiktok/publish-jobs/{id}/cancel`
- `POST /api/tiktok/publish-jobs/{id}/reschedule`
- `POST /api/tiktok/publish-jobs/{id}/retry`

Cancel and reschedule are rejected after a TikTok `publish_id` exists.

## Direct Post creation

Existing Direct Post video/photo APIs now accept:

- `scheduled_at` — timezone-aware ISO timestamp
- `max_retries` — integer 0–5

No `scheduled_at` means immediate queueing.

A scheduled time must be at least 30 seconds in the future.

## Admin UI

Direct Post Studio now supports:

- Post now
- Schedule
- local date/time picker
- max safe retry selector
- automatic conversion from local browser time to UTC

Added Publishing Schedule panel with:

- 7-day view
- 30-day view
- account filter
- Total / Scheduled / Ready / Running / Completed / Failed / Canceled counters
- scheduled time
- retry time
- queue state
- remote TikTok state
- retry count
- fail reason
- Cancel
- Reschedule
- Retry

The panel refreshes every 15 seconds.

## Worker integration

SchedulerWorker is managed by:

- `start-native.sh`
- `stop-native.sh`
- `status-native.sh`
- `watchdog.sh`

## Acceptance evidence

- Alembic: `0011_publish_scheduler (head)`
- Backend Ruff: PASS
- Backend Pytest: 35/35 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS
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
- SchedulerWorker startup: interval=10s batch=50
- First scheduler cycle: promoted=0
- First PublishWorker cycle after restart: submitted=0 polled=0
- Runtime publish jobs: 0
- Runtime scheduled jobs: 0
- Runtime ready jobs: 0
- Runtime running jobs: 0
- Public admin: HTTP 200

## Regression coverage

Automated tests verify:

- due scheduled job promotion to READY;
- cancel before TikTok submission;
- reschedule before TikTok submission;
- manual retry counting;
- retry limit behavior;
- network failure during Creator Info schedules a safe retry;
- no `publish_id` exists during safe auto-retry.

## Current live account limitation

Current connected account id 7 has not granted `video.publish`.

Therefore the production-like runtime currently contains no live Direct Post schedule and no TikTok publish call was made during Batch M acceptance.

## Next engineering batch

Batch N — Multi-account Operations Dashboard & production-readiness hardening.
