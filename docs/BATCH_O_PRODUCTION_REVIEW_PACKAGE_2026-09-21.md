# Batch O — Production Review Package & Real-Scope E2E Matrix

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** APPLICATION PACKAGE PASS / REVIEW BLOCKERS REMAIN

## Goal

Turn TikTok review preparation into a verifiable application feature rather than a manual checklist.

The application now distinguishes:

- code implemented;
- scope configured in the app;
- scope actually granted by a connected TikTok account;
- live Sandbox evidence;
- Developer Portal/manual review actions.

## Delivered

### Review Package API

Added:

- `GET /api/operations/review-package`

The endpoint returns:

- review status;
- public URLs;
- product list;
- personal-scope matrix;
- code-route evidence;
- configured/granted status;
- live-evidence status;
- review checks;
- maximum-five-video demo plan.

### Scope matrix

Tracked personal-account scopes:

- `user.info.basic`
- `user.info.profile`
- `user.info.stats`
- `video.list`
- `video.upload`
- `video.publish`

Every scope maps to concrete implemented backend routes.

A scope reaches `PASS` only when:

1. the feature routes exist;
2. the scope is configured for the app;
3. at least one connected account actually granted the scope.

Code implementation alone is not sufficient.

### Review-specific gate

Added checks for:

- externally facing HTTPS website;
- Terms and Privacy availability;
- public app-name review compatibility;
- non-private/non-personal-only product positioning;
- URL verification artifact;
- Developer Portal property verification;
- first-review Sandbox usage;
- live E2E evidence for every requested scope;
- Developer Portal Webhook Test URL evidence;
- recorded demo-video evidence;
- Direct Post unaudited-client restrictions.

Manual Developer Portal facts are marked `MANUAL`, not guessed as PASS.

### Admin UI

Added **Production Review Package** panel with:

- READY_FOR_REVIEW / NOT_READY_FOR_REVIEW status;
- Website/Terms/Privacy/OAuth/Webhook URLs with Copy action;
- product list;
- real-scope acceptance matrix;
- code/config/grant/evidence state;
- route evidence;
- review checks;
- five-video demo plan.

### Public website/legal alignment

Updated public Website, Terms, and Privacy disclosures so they accurately describe implemented optional capabilities:

- extended profile/statistics;
- public-video synchronization;
- historical analytics;
- draft upload;
- Direct Post;
- scheduling;
- webhook processing;
- operations/audit state.

These capabilities are described as permission-dependent and are not represented as enabled when TikTok has not granted the required scope.

## Review documentation

Created:

- `docs/TIKTOK_PRODUCTION_REVIEW_PACKAGE_2026-09-21.md`
- `docs/REAL_SCOPE_E2E_MATRIX_2026-09-21.md`
- `docs/TIKTOK_REVIEW_DEMO_VIDEO_SCRIPT_2026-09-21.md`

The package includes copy-ready product/scope explanations, but explicitly instructs the operator not to claim public availability or live scope support unless true.

## TikTok requirements reflected

The package reflects current TikTok guidance that:

- an app name should not reference social-media companies;
- apps for private/personal use are not approved;
- only necessary scopes should be requested;
- first-time review should demonstrate the Sandbox integration;
- every selected product/scope must be shown in the demo;
- up to five demo videos may be uploaded, each up to 50 MB;
- web review video domain must match the submitted Website URL;
- URL properties required by the app/Content Posting API must be verified;
- unaudited Direct Post clients are restricted to private/SELF_ONLY posting behavior.

## Live acceptance result

Review status:

`NOT_READY_FOR_REVIEW`

### Scope evidence

- `user.info.basic`
  - code: PASS
  - configured: true
  - connected accounts granting scope: 1
  - live evidence: PASS

- `user.info.profile`
  - code: PASS
  - configured: false
  - granted: 0
  - result: NOT_CONFIGURED

- `user.info.stats`
  - code: PASS
  - configured: false
  - granted: 0
  - result: NOT_CONFIGURED

- `video.list`
  - code: PASS
  - configured: false
  - granted: 0
  - result: NOT_CONFIGURED

- `video.upload`
  - code: PASS
  - configured: false
  - granted: 0
  - result: NOT_CONFIGURED

- `video.publish`
  - code: PASS
  - configured: false
  - granted: 0
  - result: NOT_CONFIGURED

### Review checks

PASS:

- Website HTTPS
- Terms and Privacy source/routes
- TikTok URL verification artifact exists
- current environment is Sandbox for first-review demo

FAIL:

- current public brand includes `TikTok`
- not all requested target scopes can be demonstrated live yet
- no Developer Portal webhook Test URL event has been retained
- no review MP4/MOV evidence exists yet

MANUAL:

- confirm genuine non-private user-facing use case
- confirm Developer Portal URL/property verification
- acknowledge/follow unaudited Direct Post restrictions during review

Counts:

- PASS: 4
- WARN: 0
- FAIL: 4
- MANUAL: 3

## Acceptance suite

- Backend Ruff: PASS
- Backend Pytest: 41/41 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS
- Review Package OpenAPI route: present
- Website: HTTP 200
- Admin: HTTP 200
- Terms: HTTP 200
- Privacy: HTTP 200
- all runtime services: UP

## No database migration

Batch O adds no database schema.

Review state is derived from:

- source routes;
- current settings;
- connected-account granted scopes;
- persisted webhook evidence;
- local review-media evidence;
- public website source.

## Required external actions before review

1. Resolve public app-name blocker.
2. Confirm the service use case is eligible and not private/personal-only.
3. Enable each intended advanced scope in Sandbox.
4. Reconnect the Sandbox target account and grant each newly enabled scope.
5. Run the real-scope E2E matrix until each requested scope is PASS.
6. Configure webhook callback and use Developer Portal Test URL.
7. Confirm URL/property verification in Developer Portal.
8. Record the demo videos using the real Sandbox integration/domain.
9. Re-run Review Package Gate.
10. Submit only when all selected scopes have demonstrated evidence.

## Next milestone

External TikTok Developer Portal enablement + real-scope E2E acceptance.

No additional feature scope should be marked complete until TikTok enables the corresponding permission and the real API flow passes.
