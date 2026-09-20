# Batch B — TikTok OAuth & Token Manager

**Project:** TH TikTok Manager  
**Date:** 2026-09-21  
**Server:** codespaces-626c07  
**Repository:** /workspaces/tiktok  
**Runtime:** Native server processes, no Docker.

## 1. Implementation result

**Internal implementation: PASS**  
**Live TikTok OAuth E2E: PENDING external Developer App credentials + registered HTTPS callback.**

The application intentionally does not simulate a successful TikTok connection when credentials are absent.
## 2. Delivered backend scope

Implemented:
- TikTok OAuth configuration status endpoint.
- Official web authorization URL generation.
- Cryptographically random OAuth state.
- Only SHA-256 state hash stored in PostgreSQL.
- One-time state consumption.
- State expiry enforcement.
- Callback error handling.
- Authorization-code exchange.
- Encrypted access token storage.
- Encrypted refresh token storage.
- Account upsert by TikTok open_id.
- Account list API without raw tokens.
## 3. Token lifecycle

Implemented:
- Manual account token refresh endpoint.
- Refresh token rotation handling.
- Identity check: refreshed open_id must match account open_id.
- Disconnect/revoke endpoint.
- CONNECTED / REAUTH_REQUIRED / ERROR / REVOKED states.
- Native token refresh background worker.
- Default refresh scan interval: 300 seconds.
- Default refresh lead time: 7200 seconds before access-token expiry.
- Expired refresh token moves account to REAUTH_REQUIRED.
- Network failures do not expose token values in logs.

The worker stays running when OAuth is not configured and safely skips API calls.
## 4. Database changes

Migration:
- 0002_tiktok_oauth

New tables:
- oauth_sessions
- tiktok_accounts

oauth_sessions stores:
- state_hash
- created_at
- expires_at
- consumed_at

tiktok_accounts stores:
- open_id
- scopes
- encrypted access token
- encrypted refresh token
- access/refresh expiry timestamps
- status
- last refresh timestamp
- created/updated timestamps
## 5. Frontend scope

Implemented:
- Batch B OAuth dashboard.
- OAuth configured/not-configured indicator.
- Requested scopes display.
- Connect TikTok button.
- Safe setup guidance when credentials are absent.
- OAuth callback success/error notice.
- Connected account list.
- Token expiry visibility without raw tokens.
- Manual Refresh action.
- Disconnect action.

The Connect button remains disabled until the server reports a valid OAuth configuration.
## 6. Acceptance evidence

Backend:
- Ruff: PASS.
- Pytest: 8 passed.
- Alembic: 0002_tiktok_oauth at head.
- Live admin login: HTTP 200.
- Live TikTok config endpoint after admin login: HTTP 200.
- Live account list endpoint: HTTP 200.
- Current connected account count: 0.
- OAuth configured: false because Developer App credentials are intentionally absent.

Frontend:
- TypeScript: PASS.
- ESLint: PASS.
- Vitest: PASS.
- Production build: PASS.
- npm audit: 0 vulnerabilities.
## 7. Runtime evidence

Current native services:
- PostgreSQL: UP.
- Redis-compatible cache: UP.
- FastAPI backend: UP.
- React frontend: UP.
- TikTok TokenWorker: UP.

Health:
- /health = ok.
- /ready = database true, cache true.
- unauthenticated /api/tiktok/config = HTTP 401.
- frontend = HTTP 200.

Token worker confirms that missing OAuth configuration results in a skipped refresh cycle, not a fake API request.
## 8. External configuration required for live OAuth

Add to /workspaces/tiktok/.env:
- TIKTOK_CLIENT_KEY
- TIKTOK_CLIENT_SECRET
- TIKTOK_REDIRECT_URI
- TIKTOK_SCOPES

Required callback path:
- /api/tiktok/oauth/callback

Example shape:
- https://YOUR-DOMAIN/api/tiktok/oauth/callback

The exact HTTPS URI must also be registered in TikTok Developer Portal Login Kit configuration.
Do not use a callback with query parameters or URL fragments.
## 9. Live acceptance procedure after credentials exist

1. Register the exact HTTPS callback in TikTok Developer Portal.
2. Fill TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET in server .env.
3. Set the same callback as TIKTOK_REDIRECT_URI.
4. Restart native services.
5. Sign in to TH TikTok Manager admin.
6. Confirm OAuth status becomes configured.
7. Click Connect TikTok.
8. Authenticate directly on TikTok.
9. Grant the requested scopes.
10. Confirm callback returns to TH TikTok Manager.
11. Confirm a tiktok_accounts row exists.
12. Confirm raw tokens are absent from UI/logs.
13. Trigger manual refresh and verify refresh-token rotation.
14. Disconnect and verify status becomes REVOKED.
## 10. Gate conclusion

Code-level Batch B is complete and green.

The only remaining Batch B gate is an external integration gate that cannot be truthfully completed without:
- a TikTok Developer App client key,
- its client secret,
- an HTTPS public callback URL registered with TikTok.

Do not mark live OAuth as accepted until at least three real TikTok accounts complete the authorization flow successfully.

**Current status: IMPLEMENTATION PASS / LIVE E2E PENDING.**
