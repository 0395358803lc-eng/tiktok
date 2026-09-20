# Batch L — TikTok Webhooks & Realtime Publishing Events

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** PASS

## Goal

Replace polling-only state tracking with secure, idempotent TikTok webhook ingestion for authorization and Content Posting events.

## Delivered

- Added migration `0010_tiktok_webhooks`.
- Added `tiktok_webhook_events` table.
- Added public HTTPS callback:
  - `POST /api/tiktok/webhooks`
- Added protected admin history endpoint:
  - `GET /api/tiktok/webhook-events`
- Added dedicated WebhookWorker.
- WebhookWorker is integrated into:
  - start-native
  - stop-native
  - status-native
  - watchdog
  - log rotation

## Security

Every incoming webhook is checked before persistence:

1. `TikTok-Signature` header must be present.
2. Header timestamp is parsed.
3. HMAC-SHA256 is recomputed using the active TikTok client secret.
4. Signature is compared with constant-time comparison.
5. Timestamp must be inside the configured replay window.
6. Payload `client_key` must match the active app client key.
7. Invalid requests are rejected before event processing.

Defaults:

- `WEBHOOK_SIGNATURE_TOLERANCE_SECONDS=300`
- `WEBHOOK_WORKER_INTERVAL_SECONDS=5`

Raw access tokens, refresh tokens and client secrets are not stored in webhook records.

## Idempotency

TikTok webhook delivery is treated as at-least-once.

The application computes a SHA-256 digest of the raw webhook body and stores it under a unique constraint.

A duplicate delivery:

- returns HTTP 200;
- reuses the existing record;
- is not processed twice.

## Events handled

### Authorization

`authorization.removed`

Behavior:

- find account by `user_openid`;
- mark account `REVOKED`;
- stop active Draft/Direct Post jobs by setting them to `FAILED`;
- store audit event.

### Content Posting

Handled event names:

- `post.publish.failed`
- `post.publish.complete`
- `post.publish.inbox_delivered`
- `post.publish.publicly_available`
- `post.publish.no_longer_publicaly_available`

Behavior:

- match local job by TikTok `publish_id`;
- update Draft or Direct Post state;
- persist fail reason;
- persist/remove public post IDs;
- create audit trail.

Unknown webhook event types are retained and marked `IGNORED`.

## Retry behavior

Webhook ingestion returns quickly.

Processing occurs asynchronously in WebhookWorker.

Each failed internal processing event is retried up to 5 times before being marked `ERROR`.

## Admin UI

Added Webhook panel with:

- exact callback URL;
- Copy URL action;
- HMAC / replay / idempotency security summary;
- automatic event refresh;
- event status;
- attempt count;
- received / processed times;
- error detail.

## Acceptance evidence

- Alembic: `0010_tiktok_webhooks (head)`
- Backend Ruff: PASS
- Backend Pytest: 31/31 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS
- PostgreSQL: UP
- Cache: UP
- Backend: UP
- Frontend: UP
- TokenWorker: UP
- WebhookWorker: UP
- PublishWorker: UP
- DraftWorker: UP
- AnalyticsWorker: UP
- Ngrok: UP
- Watchdog: UP
- WebhookWorker startup: interval=5s
- Initial webhook cycle: processed=0 failed=0
- Unsigned public webhook request: HTTP 401
- Test-suite webhook records remaining in runtime DB: 0

## Regression coverage

Automated tests verify:

- valid TikTok HMAC signature;
- invalid signature rejection;
- signed endpoint acceptance;
- duplicate delivery idempotency;
- `authorization.removed` account revocation;
- `post.publish.inbox_delivered` job update;
- `post.publish.complete` job update.

## TikTok Developer Portal action

Configure this callback URL under Development configuration → Webhooks:

`https://ditzy-dares-evaporate.ngrok-free.dev/api/tiktok/webhooks`

Then use TikTok's **Test URL** action.

The application should receive the test event and display it in Admin → Realtime TikTok events.

## Next engineering batch

Batch M — Publishing Scheduler & Queue Management.
