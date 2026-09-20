# Batch A — Foundation Acceptance Report

**Project:** TH TikTok Manager  
**Date:** 2026-09-21  
**Server:** codespaces-626c07  
**Repository:** /workspaces/tiktok  
**Deployment mode:** Native processes only — no Docker.

## 1. Final status

**Result: PASS**

Batch A foundation is implemented and running directly on the server.

Current services:
- PostgreSQL 17.9 — UP
- Redis-compatible cache (Valkey 8.1.2) — UP
- FastAPI backend — UP
- React frontend — UP

Reserved project ports:
- Frontend: 15173
- Backend: 18000
- PostgreSQL: 15432 (localhost only)
- Cache: 16379 (localhost only)
## 2. Foundation delivered

Implemented:
- React + TypeScript frontend.
- FastAPI backend.
- PostgreSQL database.
- Alembic migration framework.
- Redis protocol cache using Valkey.
- Server-backed admin session.
- HttpOnly admin session cookie.
- Structured JSON logging.
- Central unexpected-error handler.
- /health liveness endpoint.
- /ready dependency readiness endpoint.
- Native start/stop/status scripts.
- GitHub CI workflow without Docker.
- Environment validation through Pydantic settings.
- .env.example and gitignore.
- Backend and frontend test frameworks.

No TikTok OAuth or production TikTok credentials have been implemented in Batch A.
## 3. Acceptance evidence

Backend:
- Ruff: PASS.
- Pytest: 2 passed.
- Alembic migration: 0001_admin_sessions at head.
- /health: HTTP 200, status=ok.
- /ready: database=true, cache=true.

Frontend:
- TypeScript typecheck: PASS.
- ESLint: PASS.
- Vitest: 1 passed.
- Production build: PASS.
- Frontend HTTP response: 200.
- npm audit: 0 vulnerabilities.

Secrets:
- .env permission: 600.
- runtime/admin_credentials.secret permission: 600.
- runtime/postgres/.pg_password permission: 600.
- No Dockerfile or docker-compose file exists in the repository.
## 4. Native runtime control

Use these commands from /workspaces/tiktok:

```bash
./scripts/start-native.sh
./scripts/status-native.sh
./scripts/stop-native.sh
```

The start script starts or verifies:
1. PostgreSQL.
2. Valkey cache.
3. FastAPI backend.
4. Production frontend preview.

The scripts use project-specific ports and do not touch unrelated server ports.

## 5. Database note

The first empty PostgreSQL initialization inherited SQL_ASCII from the environment and caused a Python 3.14 driver compatibility issue.

Because the cluster contained no project data, it was reinitialized with:
- Encoding: UTF-8
- Locale: C.UTF-8

Alembic migrations then completed successfully.
## 6. Security decisions

- No TikTok password storage.
- No access token storage in frontend/localStorage.
- Application secret remains server-side.
- Admin credentials remain server-side.
- Database and cache bind only to localhost.
- Secret files are excluded from Git.
- Session state is stored in PostgreSQL.
- UI does not display secret values.

## 7. Known non-blocking note

Backend tests currently show upstream deprecation warnings from the FastAPI/Starlette test client stack on Python 3.14. Tests pass and application runtime is unaffected. Track dependency updates in later maintenance.

## 8. Gate for Batch B

Batch B may begin only from this green baseline.

Next scope:
- TikTok Developer configuration.
- Login Kit/OAuth authorization.
- OAuth state validation.
- Callback handling.
- Account connection.
- Token lifecycle and encrypted token vault.

**Batch A conclusion: ACCEPTED.**
