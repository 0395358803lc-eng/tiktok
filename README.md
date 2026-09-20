# TH TikTok Manager

API-first TikTok account management platform.

## Current milestone

Batch A — Foundation is implemented without Docker. Services run directly on the server as native/user-space processes.

### Runtime ports
- Frontend: `15173`
- Backend API: `18000`
- PostgreSQL: `15432` on localhost only
- Redis-compatible cache (Valkey): `16379` on localhost only

## Service control

From the repository root:

```bash
./scripts/start-native.sh
./scripts/status-native.sh
./scripts/stop-native.sh
```

PostgreSQL and cache are intentionally bound to `127.0.0.1`.

## Backend

The FastAPI backend uses:
- PostgreSQL with SQLAlchemy/Alembic
- Redis protocol cache
- server-backed admin sessions
- HttpOnly session cookies
- structured JSON logging
- `/health` liveness endpoint
- `/ready` dependency readiness endpoint

Secrets are loaded from root `.env`, which is gitignored.

Run migrations:

```bash
cd backend
../.venv/bin/alembic upgrade head
```

Run backend checks:

```bash
cd backend
../.venv/bin/ruff check app tests alembic
../.venv/bin/pytest
```

## Frontend

The React/TypeScript frontend provides the Batch A admin login and infrastructure status screen.

Run quality checks:

```bash
cd frontend
npm run typecheck
npm run lint
npm test
npm run build
```

The production build is served with Vite preview by the native start script for acceptance testing.

## Admin credentials

Credentials are generated locally on the server and are not committed to Git. The local operator can read:

```text
runtime/admin_credentials.secret
```

Do not place this file in source control or logs.

## Data and runtime directories

- `.runtime/` — PostgreSQL/Valkey binaries installed in the project Conda prefix
- `.venv/` — backend Python environment
- `runtime/postgres/data/` — PostgreSQL data directory
- `runtime/valkey/` — cache persistence/runtime files
- `logs/` — backend, frontend, PostgreSQL and cache logs
- `frontend/dist/` — production frontend build

These are excluded from source control as appropriate.

## Next milestone

Batch B will add TikTok Login Kit/OAuth, state validation, account connection and token lifecycle management only after Batch A acceptance remains green.


## Batch B — TikTok OAuth

Implemented server-side:
- TikTok Login Kit authorization URL.
- OAuth state generation and hashed state persistence.
- Callback validation with one-time state consumption.
- Authorization-code token exchange.
- Encrypted access/refresh token vault.
- Manual refresh and disconnect/revoke endpoints.
- Native token refresh worker.
- Account connection list without exposing raw tokens.

Required external configuration in root `.env`:

```env
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
TIKTOK_REDIRECT_URI=https://your-domain.example/api/tiktok/oauth/callback
TIKTOK_SCOPES=user.info.basic
```

The redirect URI must be HTTPS, static, and registered exactly in the TikTok Developer App.

After changing OAuth environment values, restart native services:

```bash
./scripts/stop-native.sh
./scripts/start-native.sh
```

Verify the token worker:

```bash
./scripts/status-native.sh
tail -f logs/token-worker.log
```

When TikTok credentials are not configured, the worker remains healthy and skips refresh calls.


## Public website and review routes

The production-readiness frontend separates the public website from the protected admin control plane:

- `/` — public product website
- `/admin` — administrator control plane
- `/terms` — Terms of Service
- `/privacy` — Privacy Policy
- `/api/tiktok/oauth/callback` — TikTok OAuth callback

TikTok OAuth success/error redirects return to `/admin`.

## Sandbox / Production switching

Use `TIKTOK_ENVIRONMENT=sandbox` during TikTok Sandbox acceptance and switch to
`TIKTOK_ENVIRONMENT=production` after Production approval. Optional environment-specific
credentials are supported through `TIKTOK_SANDBOX_CLIENT_KEY`,
`TIKTOK_SANDBOX_CLIENT_SECRET`, `TIKTOK_PRODUCTION_CLIENT_KEY`, and
`TIKTOK_PRODUCTION_CLIENT_SECRET`. The original `TIKTOK_CLIENT_KEY` and
`TIKTOK_CLIENT_SECRET` remain supported as migration fallbacks.


## Personal API scope manager

The personal-account integration supports dynamic authorization for:

- `user.info.basic`
- `user.info.profile`
- `user.info.stats`

Only scopes listed in `TIKTOK_SCOPES` are requestable. The backend rejects attempts to
request a scope that has not been enabled for the current TikTok Developer App.

The User Info client requests fields according to the scopes actually granted to each account,
so a basic-only account never requests protected profile/statistics fields.


## Personal Video Library

The Display API video module is implemented for the `video.list` scope.

Backend routes:

- `GET /api/tiktok/accounts/{id}/videos`
- `POST /api/tiktok/accounts/{id}/videos/sync`
- `POST /api/tiktok/accounts/{id}/videos/refresh`

TikTok video metadata is synchronized into PostgreSQL. List pagination is cursor-based and
uses at most 20 records per TikTok API request. Stored cover URLs can be refreshed through
the video-query endpoint because TikTok cover-image URLs are temporary.

The backend refuses live sync/refresh operations unless the connected account actually
granted `video.list`.
