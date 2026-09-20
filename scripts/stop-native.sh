#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME="$ROOT/.runtime"

for name in watchdog frontend analytics-worker token-worker backend; do
  pidfile="$ROOT/runtime/$name.pid"
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid"
    fi
    rm -f "$pidfile"
  fi
done

ngrok_pidfile="$ROOT/runtime/ngrok/ngrok.pid"
if [[ -f "$ngrok_pidfile" ]]; then
  ngrok_pid="$(cat "$ngrok_pidfile")"
  if kill -0 "$ngrok_pid" 2>/dev/null; then
    kill "$ngrok_pid"
  fi
  rm -f "$ngrok_pidfile"
fi

if "$RUNTIME/bin/valkey-cli" -h 127.0.0.1 -p 16379 ping >/dev/null 2>&1; then
  "$RUNTIME/bin/valkey-cli" -h 127.0.0.1 -p 16379 shutdown
fi

if "$RUNTIME/bin/pg_isready" -h 127.0.0.1 -p 15432 >/dev/null 2>&1; then
  "$RUNTIME/bin/pg_ctl" -D "$ROOT/runtime/postgres/data" stop -m fast
fi
