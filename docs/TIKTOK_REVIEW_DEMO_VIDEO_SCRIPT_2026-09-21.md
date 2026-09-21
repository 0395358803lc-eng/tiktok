# TikTok App Review Demo Video Script

**Date:** 2026-09-21  
**Maximum recommended set:** 5 videos  
**TikTok limit:** maximum 5 uploaded demo videos, each up to 50 MB.

## Recording rules

- Record the real web application on the exact Website URL/domain submitted in Developer Portal.
- For first-time review, use the Sandbox integration.
- Keep TikTok Client Secret, access tokens, refresh tokens, admin password, encryption keys, and terminal secrets out of frame.
- Show actual user interactions, not slides or mocked screenshots.
- Show only products/scopes actually selected for review.
- If a scope is blocked in Sandbox, do not pretend to demonstrate it.

## Video 1 — Login Kit + User Info

Suggested target length: 60–120 seconds.

1. Open public Website URL.
2. Show visible Terms and Privacy links.
3. Open Admin and sign in.
4. Show Scope Manager.
5. Click Connect TikTok.
6. Show TikTok authorization screen and requested scopes.
7. Authorize with Sandbox target user.
8. Return to Admin.
9. Show connected account identity.
10. Run Profile Sync.
11. If approved, show extended profile and real stats.
12. Show token lifetime status without exposing token values.

Scopes demonstrated:

- `user.info.basic`
- `user.info.profile` only if enabled/granted
- `user.info.stats` only if enabled/granted

## Video 2 — Display API / Video Library

Suggested target length: 60–120 seconds.

1. Select the connected Sandbox account.
2. Show `video.list` as granted.
3. Open Video Library.
4. Click Sync latest.
5. Show real TikTok public videos returned.
6. Show real views/likes/comments/shares where available.
7. Click Refresh metadata.
8. Open Analytics.
9. Explain that history uses real snapshots and no fake history is generated.

Scope demonstrated:

- `video.list`

## Video 3 — Draft Upload

Suggested target length: 90–150 seconds.

1. Open Draft Upload Studio.
2. Show `video.upload` granted.
3. Stage a small review-safe test video.
4. Queue to TikTok Draft.
5. Show job states changing.
6. Show TikTok status reaching `SEND_TO_USER_INBOX`.
7. Show Realtime TikTok Events if a webhook arrives.
8. On the target TikTok account, show the Inbox/draft notification without exposing unrelated personal data.
9. Explain that the creator completes editing/posting in TikTok.

Scope demonstrated:

- `video.upload`

## Video 4 — Direct Post

Suggested target length: 90–180 seconds.

1. Open Direct Post Studio.
2. Show `video.publish` granted.
3. Select review-safe media.
4. Show media preview.
5. Show Creator Info-derived privacy options.
6. Manually select privacy; for unaudited review use permitted private/SELF_ONLY behavior.
7. Show Comment/Duet/Stitch defaults OFF and disabled options honored.
8. Show commercial-content controls and Music Usage confirmation.
9. Submit Direct Post.
10. Show publish_id/job status without exposing tokens.
11. Show PublishWorker/status/webhook completion.
12. If allowed by the current audit state, show the resulting TikTok post.

Scope demonstrated:

- `video.publish`

## Video 5 — Operations + Revocation + Webhook evidence

Suggested target length: 60–120 seconds.

1. Open Operations Control Center.
2. Show account health, scope health, worker health, and Production/Review gates.
3. Open Realtime TikTok Events.
4. Use Developer Portal Test URL and show the signed event appears.
5. Demonstrate disconnect/revoke on a review account if included in the submitted flow.
6. Show the account changing state appropriately.
7. Finish on Review Package and show all requested scopes have PASS live evidence.

## Before recording

- Resolve public app-name blocker.
- Confirm Website/Terms/Privacy URL properties in Developer Portal.
- Confirm webhook callback and Test URL.
- Enable only the scopes intended for this review.
- Reconnect the Sandbox target user so newly enabled scopes are actually granted.
- Prepare non-sensitive sample video/photo content.
- Close terminals and secret-management screens.
- Clear unrelated notifications/browser tabs.

## Final review-video acceptance

Do not upload until:

- file size is <=50 MB per video;
- actual domain matches Developer Portal Website URL;
- all visible product names match the submitted app name;
- no secret values are visible;
- every requested scope appears in at least one complete end-to-end flow.
