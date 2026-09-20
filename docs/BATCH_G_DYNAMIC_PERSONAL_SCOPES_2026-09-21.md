# Batch G — Dynamic Personal Scopes & Extended Profile

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** CODE PASS / ADVANCED SCOPES PENDING TIKTOK PORTAL ENABLEMENT

## Goal

Prepare the personal-account API layer for:

- `user.info.basic`
- `user.info.profile`
- `user.info.stats`

without requesting permissions that the TikTok Developer App has not enabled.

## Delivered

- Added Dynamic Scope Manager.
- Added personal-scope catalog:
  - Basic profile
  - Extended profile
  - Profile statistics
- OAuth start can now accept a selected scope list.
- Backend rejects unsupported or Developer-Portal-disabled scopes before redirecting to TikTok.
- `user.info.basic` is always included for personal profile authorization.
- OAuth session now records requested scopes.
- Added migration `0005_personal_profile_scopes`.
- Added extended account fields:
  - username
  - bio_description
  - profile_deep_link
  - is_verified
  - follower_count
  - following_count
  - likes_count
  - video_count
- User Info requests are dynamically field-scoped based on the scopes actually granted to each account.
- Admin Scope Manager displays Enabled / Not enabled for each personal permission.
- Account cards can display username, verification, bio, profile link and statistics once those permissions are granted.
- Existing `user.info.basic` accounts remain fully compatible.

## Security / permission behavior

The application does not assume that all requested scopes are granted.

Fields are requested from TikTok only when the corresponding scope exists on the connected account:

- `user.info.basic` -> open_id, union_id, avatar_url, display_name
- `user.info.profile` -> username, bio_description, profile_deep_link, is_verified
- `user.info.stats` -> follower_count, following_count, likes_count, video_count

## Acceptance evidence

- Alembic: `0005_personal_profile_scopes (head)`
- Backend Ruff: PASS
- Backend Pytest: 16/16 PASS
- Frontend TypeScript: PASS
- Frontend ESLint: PASS
- Frontend Vitest: PASS
- Frontend production build: PASS
- Runtime services: UP
- Sandbox environment: active
- Current configured scope: `user.info.basic`
- Basic OAuth start: HTTP 200
- Attempt to request unconfigured `user.info.profile`: HTTP 400
- Existing connected account id 7: CONNECTED
- Existing basic profile sync after migration: PASS

## Next external action

In TikTok Developer Portal / Sandbox, enable and apply:

`user.info.profile`

`user.info.stats`

Only after TikTok makes those scopes available to the app should the live environment value be changed to:

`TIKTOK_SCOPES=user.info.basic,user.info.profile,user.info.stats`

The connected account must then authorize the added permissions before advanced profile/stat fields can be populated.

## Next engineering batch

Batch H — Video Library with `video.list`.
