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

if [[ -f "$ROOT/runtime/ngrok/ngrok.pid" ]] && kill -0 "$(cat "$ROOT/runtime/ngrok/ngrok.pid")" 2>/dev/null; then
  printf "%-12s %s\n" "Ngrok" "UP"
else
  printf "%-12s %s\n" "Ngrok" "DOWN"
fi
