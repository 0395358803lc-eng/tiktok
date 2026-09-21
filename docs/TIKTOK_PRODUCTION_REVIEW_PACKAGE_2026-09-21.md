# TikTok Production Review Package

**Date:** 2026-09-21  
**Project:** TH Creator Manager  
**Review status:** NOT READY FOR REVIEW

## Important submission rule

Only select products/scopes in TikTok Developer Portal that can be demonstrated end-to-end in the Sandbox review video.

TikTok's current App Review Guidelines require every selected product/scope to be clearly demonstrated. Scopes that are implemented in code but not yet enabled/granted must remain out of the submission until live Sandbox evidence exists.

## Current public URLs

- Website: https://ditzy-dares-evaporate.ngrok-free.dev/
- Admin: https://ditzy-dares-evaporate.ngrok-free.dev/admin
- Terms: https://ditzy-dares-evaporate.ngrok-free.dev/terms
- Privacy: https://ditzy-dares-evaporate.ngrok-free.dev/privacy
- OAuth callback: https://ditzy-dares-evaporate.ngrok-free.dev/api/tiktok/oauth/callback
- Webhook callback: https://ditzy-dares-evaporate.ngrok-free.dev/api/tiktok/webhooks

## Review-safe app description draft

Use this only if it accurately describes the service available to users:

> A web application that helps authorized TikTok account owners and operators connect accounts through TikTok OAuth, review permitted profile and content information, manage approved draft/direct-post workflows, schedule publishing operations, and monitor authorization and publishing status from one control plane.

Do not describe the application as a private/personal-only utility. TikTok's current review criteria state that apps for private or personal use will not be approved.

## App-name alignment

The current public website name is:

`TH Creator Manager`

The public branding no longer uses TikTok as the product name. Before review, manually confirm that the TikTok Developer Portal app name is also `TH Creator Manager` and that the review video, Website, Terms, and Privacy pages show the same public product name.

The repository/folder name does not need to change.

## Product and scope explanations

### Login Kit — `user.info.basic`

Purpose:

- allow a TikTok user to authorize the application using TikTok OAuth;
- obtain account identity required to associate authorized API data with the correct connected account;
- display the authorized user's basic profile identity in the account-management UI.

User experience:

1. Admin selects Connect TikTok.
2. User is redirected to TikTok authorization.
3. User reviews and grants requested permission.
4. TikTok redirects back to the registered HTTPS callback.
5. Server exchanges the code for tokens and stores tokens encrypted server-side.
6. Connected account is displayed in Admin.

Current live Sandbox evidence: **PASS**.

### User Info — `user.info.profile`

Purpose:

- display additional authorized profile information such as username, bio, profile link, and verification state.

User experience:

- after the user grants this scope, Profile Sync retrieves the approved extended profile fields and shows them in the connected account record.

Current live Sandbox evidence: **BLOCKED — scope not configured/granted**.

### User Info — `user.info.stats`

Purpose:

- show permitted account statistics;
- create historical account-stat snapshots for 7/30/90-day analytics.

User experience:

- after the user grants this scope, Profile Sync retrieves statistics and AnalyticsWorker stores real historical observations.

Current live Sandbox evidence: **BLOCKED — scope not configured/granted**.

### Display API — `video.list`

Purpose:

- retrieve the authorized user's public TikTok videos and permitted video metrics;
- populate Video Library and historical video analytics.

User experience:

- user selects an authorized account and explicitly synchronizes public videos;
- the application stores returned metadata and metrics;
- cover URLs can be refreshed through TikTok video query because they are temporary.

Current live Sandbox evidence: **BLOCKED — scope not configured/granted**.

### Content Posting API — `video.upload`

Purpose:

- send creator-authorized video/photo content to TikTok Inbox as a draft so the creator can finish editing/posting in TikTok.

User experience:

1. User stages content.
2. User explicitly queues a draft.
3. DraftWorker sends the media to TikTok using the approved Upload flow.
4. Job status is tracked.
5. On `SEND_TO_USER_INBOX`, UI instructs the creator to open TikTok and finish the workflow.

Current live Sandbox evidence: **BLOCKED — scope not configured/granted**.

### Content Posting API — `video.publish`

Purpose:

- directly post creator-authorized video/photo content using the Content Posting API;
- support user-selected privacy/interactions/commercial disclosure and an internal scheduling queue.

User experience:

1. Application queries current Creator Info.
2. User previews media.
3. User manually selects privacy.
4. Comment/Duet/Stitch options reflect current creator capabilities and default OFF.
5. Required music/commercial-content confirmations are collected.
6. Backend re-checks Creator Info.
7. PublishWorker initializes Direct Post and tracks completion.
8. Webhook/status events update the operation.

For unaudited clients, demonstrate using TikTok's current unaudited-client restrictions, including private/SELF_ONLY visibility.

Current live Sandbox evidence: **BLOCKED — scope not configured/granted**.

## Webhooks

Webhook callback:

`https://ditzy-dares-evaporate.ngrok-free.dev/api/tiktok/webhooks`

Implemented:

- HTTPS callback;
- TikTok HMAC-SHA256 signature verification;
- timestamp replay window;
- client-key verification;
- idempotent duplicate handling;
- asynchronous processing;
- authorization-removal handling;
- Content Posting event handling.

Current Developer Portal Test URL evidence: **NOT YET CAPTURED**.

Required action:

1. configure callback in Developer Portal;
2. click Test URL;
3. verify the event appears in Admin → Realtime TikTok events;
4. record this in the demo/evidence package.

## URL/property verification

A TikTok verification artifact exists in `frontend/public`.

Still manual in Developer Portal:

- verify Website URL/property;
- verify Terms URL/property where requested;
- verify Privacy URL/property where requested;
- verify Content Posting URL/domain requirements.

Application code cannot prove Developer Portal verification state.

## Demo video requirements

TikTok currently allows up to 5 review videos, each up to 50 MB.

For first review, record the actual Sandbox integration on the same domain submitted as Website URL.

Recommended split:

1. Login Kit + basic/extended profile + stats.
2. Video Library + analytics.
3. Draft Upload + Inbox delivery + webhook.
4. Direct Post under unaudited-client restrictions + publish completion.
5. Operations/revoke/re-auth/readiness evidence.

Do not submit a video for a scope that is not enabled and cannot be demonstrated end-to-end.

## Current blockers before review submission

- Confirm the TikTok Developer Portal app name matches the public name `TH Creator Manager`.
- Confirm the product is not positioned as private/personal-only use.
- Advanced scopes are not configured/granted in the current Sandbox account.
- Developer Portal URL-property verification must be confirmed.
- Webhook Test URL evidence has not been captured.
- Review demo MP4/MOV evidence has not been recorded.
- Each requested scope needs end-to-end Sandbox evidence.

## Official reference pages used for this package

- TikTok App Review Guidelines
- TikTok Developer Guidelines
- TikTok Scopes Reference
- Login Kit Web / token management
- Display API Get Started
- Content Posting API Get Started / Direct Post
- Content Sharing Guidelines
- Development Configuration / URL verification / Webhooks
