#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INTERVAL="${WATCHDOG_INTERVAL_SECONDS:-60}"
PUBLIC_URL="${PUBLIC_URL:-https://ditzy-dares-evaporate.ngrok-free.dev/}"
LOG="$ROOT/logs/watchdog.log"
mkdir -p "$ROOT/logs"

log() {
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG"
}

kill_managed() {
  local name="$1"
  local pidfile="$ROOT/runtime/$2"
  if [[ -f "$pidfile" ]]; then
    local pid
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 1
    fi
    rm -f "$pidfile"
    log "reset component=$name"
  fi
}

log "watchdog started interval=${INTERVAL}s"

while true; do
  repair=0

  if ! curl -fsS --max-time 5 http://127.0.0.1:18000/health >/dev/null 2>&1 ||      ! curl -fsS --max-time 5 http://127.0.0.1:18000/ready >/dev/null 2>&1; then
    log "health failure component=backend"
    kill_managed backend backend.pid
    repair=1
  fi

  frontend_ok=1
  if ! curl -fsS --max-time 5 http://127.0.0.1:15173/ >/dev/null 2>&1; then
    frontend_ok=0
    log "health failure component=frontend"
    kill_managed frontend frontend.pid
    repair=1
  fi

  if [[ ! -f "$ROOT/runtime/token-worker.pid" ]] ||      ! kill -0 "$(cat "$ROOT/runtime/token-worker.pid" 2>/dev/null || echo 0)" 2>/dev/null; then
    rm -f "$ROOT/runtime/token-worker.pid"
    log "process failure component=token-worker"
    repair=1
  fi

  if (( frontend_ok )); then
    if ! curl -fsS --max-time 8 "$PUBLIC_URL" >/dev/null 2>&1; then
      log "health failure component=ngrok"
      kill_managed ngrok ngrok/ngrok.pid
      repair=1
    fi
  fi

  if (( repair )); then
    log "repair start"
    "$ROOT/scripts/start-native.sh" >> "$LOG" 2>&1 || log "repair failed"
  fi

  "$ROOT/scripts/rotate-logs.sh" || log "log rotation failed"
  "$ROOT/scripts/backup-postgres.sh" >> "$LOG" 2>&1 || log "database backup failed"

  if [[ "${WATCHDOG_ONCE:-0}" == "1" ]]; then
    break
  fi
  sleep "$INTERVAL"
done
