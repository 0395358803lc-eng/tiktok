# Batch E — Native Monitoring, Log Rotation & PostgreSQL Backup

**Date:** 2026-09-21  
**Project:** TH TikTok Manager  
**Status:** PASS

## Delivered

- Added native watchdog process managed by start/stop/status scripts.
- Watchdog checks:
  - Backend `/health`
  - Backend `/ready`
  - Frontend local HTTP
  - TokenWorker PID
  - Public ngrok URL
- Watchdog repairs only failed components and invokes the native start script.
- Public ngrok check is dependency-aware: if frontend is down, ngrok is not restarted unnecessarily.
- Added size-based log rotation with copy-truncate behavior.
- Default log threshold: 10 MiB.
- Default retained rotations: 5.
- Added PostgreSQL custom-format backups under `runtime/backups`.
- Backup directory permission: 700.
- Backup file permission: 600.
- Default backup interval: 24 hours.
- Default backup retention: 7 days.
- Backup process validates each archive with `pg_restore -l`.
- Status script now shows Watchdog and latest Backup.

## Acceptance evidence

- PostgreSQL: UP
- Cache: UP
- Backend: UP
- Frontend: UP
- TokenWorker: UP
- Ngrok: UP
- Watchdog: UP
- Public frontend: HTTP 200

### Log rotation
A controlled 11 MiB test log was rotated:
- active file after rotation: 0 bytes
- rotated `.1` file: 11,534,336 bytes

### Watchdog self-heal
Frontend process was deliberately terminated:
- old frontend PID: 125025
- repaired frontend PID: 125445
- ngrok PID before/after: 125026
- result: frontend recovered, ngrok was not restarted unnecessarily

### PostgreSQL backup
Backup created:
- `runtime/backups/th_tiktok_20260920T223646Z.dump`
- archive validation: PASS

### PostgreSQL restore test
The backup was restored into a temporary database:
- restored TikTok accounts: 1
- restored audit events: 1
- temporary restore database removed after validation

## Operational limitation

The watchdog provides recovery while the host operating environment is running. If the entire host/Codespace is stopped or suspended, an external host-level startup mechanism is still required.
