#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME="$ROOT/.runtime"

check_http() {
  local name="$1" url="$2"
  if curl -fsS "$url" >/dev/null 2>&1; then
    printf "%-12s %s\n" "$name" "UP"
  else
    printf "%-12s %s\n" "$name" "DOWN"
  fi
}

if "$RUNTIME/bin/pg_isready" -h 127.0.0.1 -p 15432 >/dev/null 2>&1; then
  printf "%-12s %s\n" "PostgreSQL" "UP"
else
  printf "%-12s %s\n" "PostgreSQL" "DOWN"
fi

if "$RUNTIME/bin/valkey-cli" -h 127.0.0.1 -p 16379 ping >/dev/null 2>&1; then
  printf "%-12s %s\n" "Cache" "UP"
else
  printf "%-12s %s\n" "Cache" "DOWN"
fi
check_http "Backend" "http://127.0.0.1:18000/health"
check_http "Frontend" "http://127.0.0.1:15173/"

if [[ -f "$ROOT/runtime/token-worker.pid" ]] && kill -0 "$(cat "$ROOT/runtime/token-worker.pid")" 2>/dev/null; then
  printf "%-12s %s\n" "TokenWorker" "UP"
else
  printf "%-12s %s\n" "TokenWorker" "DOWN"
fi

if [[ -f "$ROOT/runtime/webhook-worker.pid" ]] && kill -0 "$(cat "$ROOT/runtime/webhook-worker.pid")" 2>/dev/null; then
  printf "%-14s %s\n" "WebhookWorker" "UP"
else
  printf "%-14s %s\n" "WebhookWorker" "DOWN"
fi

if [[ -f "$ROOT/runtime/publish-worker.pid" ]] && kill -0 "$(cat "$ROOT/runtime/publish-worker.pid")" 2>/dev/null; then
  printf "%-14s %s\n" "PublishWorker" "UP"
else
  printf "%-14s %s\n" "PublishWorker" "DOWN"
fi

if [[ -f "$ROOT/runtime/draft-worker.pid" ]] && kill -0 "$(cat "$ROOT/runtime/draft-worker.pid")" 2>/dev/null; then
  printf "%-12s %s\n" "DraftWorker" "UP"
else
  printf "%-12s %s\n" "DraftWorker" "DOWN"
fi

if [[ -f "$ROOT/runtime/analytics-worker.pid" ]] && kill -0 "$(cat "$ROOT/runtime/analytics-worker.pid")" 2>/dev/null; then
  printf "%-12s %s\n" "AnalyticsWorker" "UP"
else
  printf "%-12s %s\n" "AnalyticsWorker" "DOWN"
fi

if [[ -f "$ROOT/runtime/ngrok/ngrok.pid" ]] && kill -0 "$(cat "$ROOT/runtime/ngrok/ngrok.pid")" 2>/dev/null; then
  printf "%-12s %s\n" "Ngrok" "UP"
else
  printf "%-12s %s\n" "Ngrok" "DOWN"
fi

if [[ -f "$ROOT/runtime/watchdog.pid" ]] && kill -0 "$(cat "$ROOT/runtime/watchdog.pid")" 2>/dev/null; then
  printf "%-12s %s\n" "Watchdog" "UP"
else
  printf "%-12s %s\n" "Watchdog" "DOWN"
fi

latest_backup="$(find "$ROOT/runtime/backups" -maxdepth 1 -type f -name 'th_tiktok_*.dump' -printf '%T@ %f\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2- || true)"
if [[ -n "$latest_backup" ]]; then
  printf "%-12s %s\n" "Backup" "$latest_backup"
else
  printf "%-12s %s\n" "Backup" "NONE"
fi
