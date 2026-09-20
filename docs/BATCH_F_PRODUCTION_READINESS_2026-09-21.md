# Batch F — Production Readiness Website & Environment Switching

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** APPLICATION SIDE PASS / DEVELOPER PORTAL ACTIONS REMAIN

## Delivered

- Public website at `/`.
- Admin control plane moved to `/admin`.
- Real Terms of Service page at `/terms`.
- Real Privacy Policy page at `/privacy`.
- Terms and Privacy links are visible directly in the public header and footer.
- OAuth callback now redirects to `/admin` after success/error.
- Public website explains:
  - official TikTok OAuth authorization,
  - current Login Kit integration,
  - basic profile synchronization,
  - server-side encrypted token storage,
  - user-controlled disconnect/revocation.
- Added `TIKTOK_ENVIRONMENT=sandbox|production`.
- Added optional sandbox and production credential pairs.
- Legacy `TIKTOK_CLIENT_KEY/TIKTOK_CLIENT_SECRET` remain supported as a fallback.
- Admin UI displays the active TikTok environment.
- Live runtime is explicitly set to `sandbox`.

## Public URLs

- Website: `https://ditzy-dares-evaporate.ngrok-free.dev/`
- Admin: `https://ditzy-dares-evaporate.ngrok-free.dev/admin`
- Terms: `https://ditzy-dares-evaporate.ngrok-free.dev/terms`
- Privacy: `https://ditzy-dares-evaporate.ngrok-free.dev/privacy`
- OAuth callback: `https://ditzy-dares-evaporate.ngrok-free.dev/api/tiktok/oauth/callback`

All four public SPA routes return HTTP 200.

## Current TikTok integration

- Environment: `sandbox`
- Product implemented: Login Kit
- Scope implemented: `user.info.basic`
- OAuth configured: true
- Connected-account flow: PASS
- Profile sync: PASS
- Refresh token flow: PASS
- Disconnect/revoke flow: implemented
- OAuth callback returns to `/admin`: PASS

## TikTok review checklist

### Application-side PASS

- Website is no longer only an admin/login screen.
- Privacy Policy is public and linked directly.
- Terms of Service is public and linked directly.
- Web redirect URI is HTTPS and stable for the current environment.
- The requested scope is actually used by the application.
- User authorization uses TikTok Login Kit rather than collecting TikTok passwords.
- Demoable Sandbox integration exists with a successful connected account.
- Access and refresh tokens stay server-side.

### Developer Portal actions still required

1. Production App details must use the same Website, Terms and Privacy URLs.
2. Production URL properties must be verified in the TikTok Developer Portal where required.
3. Production Products should include only integrations actually implemented and demonstrated.
4. Production Scopes should currently remain limited to `user.info.basic` unless new features are implemented before review.
5. Record and upload an end-to-end Sandbox demo video showing:
   - public website,
   - admin sign in,
   - Connect TikTok,
   - TikTok authorization,
   - successful callback,
   - connected account name/avatar,
   - profile synchronization,
   - disconnect/revoke if included in the review explanation.
6. Complete the App Review explanation for Login Kit and `user.info.basic`.
7. Submit Production for review.
8. After approval, configure Production credentials and set `TIKTOK_ENVIRONMENT=production`.

## Review blocker to resolve before submission

TikTok's current App Review Guidelines state that an app name should not include a reference to a social media company. The current public/developer name **TH TikTok Manager** contains the TikTok brand name.

Do not submit the current name without reviewing this requirement. Rename the public/Developer Portal app consistently before Production submission if TikTok applies this rule to the app.

The internal repository/project folder can remain named `tiktok`; this concern is about the public app name shown during review/authorization.
