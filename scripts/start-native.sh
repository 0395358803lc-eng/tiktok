#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME="$ROOT/.runtime"
mkdir -p "$ROOT/logs" "$ROOT/runtime/valkey"

if ! "$RUNTIME/bin/pg_isready" -h 127.0.0.1 -p 15432 >/dev/null 2>&1; then
  "$RUNTIME/bin/pg_ctl" -D "$ROOT/runtime/postgres/data"     -l "$ROOT/logs/postgres.log"     -o "-h 127.0.0.1 -p 15432" start
fi

if ! "$RUNTIME/bin/valkey-cli" -h 127.0.0.1 -p 16379 ping >/dev/null 2>&1; then
  "$RUNTIME/bin/valkey-server" --bind 127.0.0.1 --port 16379     --daemonize yes --appendonly yes     --dir "$ROOT/runtime/valkey"     --pidfile "$ROOT/runtime/valkey/valkey.pid"     --logfile "$ROOT/logs/valkey.log"
fi

if [[ ! -f "$ROOT/runtime/backend.pid" ]] || ! kill -0 "$(cat "$ROOT/runtime/backend.pid")" 2>/dev/null; then
  cd "$ROOT/backend"
  nohup "$ROOT/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 18000 --no-access-log     > "$ROOT/logs/backend.log" 2>&1 &
  echo $! > "$ROOT/runtime/backend.pid"
fi

if [[ ! -f "$ROOT/runtime/token-worker.pid" ]] || ! kill -0 "$(cat "$ROOT/runtime/token-worker.pid")" 2>/dev/null; then
  cd "$ROOT/backend"
  nohup "$ROOT/.venv/bin/python" -m app.workers.tiktok_token_refresh \
    > "$ROOT/logs/token-worker.log" 2>&1 &
  echo $! > "$ROOT/runtime/token-worker.pid"
fi

if [[ ! -f "$ROOT/runtime/frontend.pid" ]] || ! kill -0 "$(cat "$ROOT/runtime/frontend.pid")" 2>/dev/null; then
  cd "$ROOT/frontend"
  nohup "$ROOT/frontend/node_modules/.bin/vite" preview --host 0.0.0.0 --port 15173 --strictPort     > "$ROOT/logs/frontend.log" 2>&1 &
  echo $! > "$ROOT/runtime/frontend.pid"
fi

if [[ ! -f "$ROOT/runtime/ngrok/ngrok.pid" ]] || ! kill -0 "$(cat "$ROOT/runtime/ngrok/ngrok.pid")" 2>/dev/null; then
  nohup "$ROOT/.runtime/bin/ngrok" http 15173 \
    --url https://ditzy-dares-evaporate.ngrok-free.dev \
    --config "$ROOT/runtime/ngrok/ngrok.yml" \
    --log "$ROOT/logs/ngrok.log" --log-format json \
    >/dev/null 2>&1 &
  echo $! > "$ROOT/runtime/ngrok/ngrok.pid"
fi

sleep 2
"$ROOT/scripts/status-native.sh"
