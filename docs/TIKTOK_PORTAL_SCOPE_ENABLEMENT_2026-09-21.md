# TikTok Developer Portal — Scope Enablement Runbook

**Date:** 2026-09-21

This runbook is for the next manual step in TikTok Developer Portal. It does not replace TikTok approval.

## Current state

The application currently requests only:

`user.info.basic`

This is intentional. The server should not request advanced scopes before those scopes are actually available to the app in TikTok Developer Portal.

## Scope-management flow

TikTok's current Scopes documentation states that additional scopes are managed from the app page in Developer Portal:

1. Open the target app.
2. Locate the **Scopes** section.
3. Select **Add Scopes**.
4. Add only the scopes required by implemented and reviewable features.
5. Save/apply the app configuration.
6. After scope approval/availability, reconnect the Sandbox user so that the user explicitly grants the new scopes.

Scope approval alone does not give access to user data. The TikTok user must separately authorize each requested scope.

## Intended personal-account scopes

### user.info.profile

Feature:

- extended profile information

Required live evidence:

- username
- bio description where available
- profile links where available
- verification state

### user.info.stats

Feature:

- account statistics and historical analytics

Required live evidence:

- follower count
- following count
- likes count
- public video count

### video.list

Product/use:

- Display API / public video library

Required live evidence:

- real public video list
- real metadata/metrics
- Video Library persistence/refresh

TikTok Display API documentation currently states that `video.list` is required to read a user's public videos.

### video.upload

Product/use:

- Content Posting API draft upload

Required live evidence:

- real TikTok draft initialization
- media transfer or approved pull-from-URL flow
- real `publish_id`
- status reaches TikTok Inbox / draft workflow

### video.publish

Product/use:

- Content Posting API Direct Post

Required live evidence:

- real Creator Info
- real Direct Post initialization
- privacy/interactions constrained by Creator Info
- real `publish_id`
- status/webhook completion

Until TikTok completes the relevant Content Posting audit/review, follow TikTok's unaudited-client restrictions during any Direct Post demo.

## Server-side activation after Portal enablement

Do not enable all five scopes blindly.

After confirming a scope is available in the Developer Portal, add it to the current server `TIKTOK_SCOPES` value.

Example progression:

`user.info.basic,user.info.profile`

then:

`user.info.basic,user.info.profile,user.info.stats`

then, if Display API scope is enabled:

`user.info.basic,user.info.profile,user.info.stats,video.list`

and only after Content Posting scopes are enabled:

`user.info.basic,user.info.profile,user.info.stats,video.list,video.upload,video.publish`

After each change:

1. restart runtime;
2. run `./scripts/scope-e2e-preflight.sh`;
3. reconnect the Sandbox account;
4. verify the new granted scope is stored in the account record;
5. run the corresponding real E2E workflow.

## Review rule

TikTok App Review currently requires all selected products/scopes to be demonstrated in the review video. If a scope cannot be demonstrated end-to-end in Sandbox, remove it from that review request rather than claiming support without evidence.

For a first-time app review, TikTok requires the Sandbox integration to be used in the demo.
