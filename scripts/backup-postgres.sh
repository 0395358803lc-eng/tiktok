#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME="$ROOT/.runtime"
BACKUP_DIR="$ROOT/runtime/backups"
INTERVAL="${BACKUP_INTERVAL_SECONDS:-86400}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

latest="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'th_tiktok_*.dump' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2- || true)"
now="$(date +%s)"
if [[ -n "$latest" ]]; then
  mtime="$(stat -c %Y "$latest")"
  age=$((now-mtime))
  if (( age < INTERVAL )); then
    echo "Backup not due age_seconds=$age"
    exit 0
  fi
fi

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
tmp="$BACKUP_DIR/.th_tiktok_${stamp}.dump.tmp"
out="$BACKUP_DIR/th_tiktok_${stamp}.dump"

"$RUNTIME/bin/pg_dump" -p 15432 -U th_tiktok -Fc -f "$tmp" th_tiktok
"$RUNTIME/bin/pg_restore" -l "$tmp" >/dev/null
chmod 600 "$tmp"
mv "$tmp" "$out"
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'th_tiktok_*.dump' -mtime +"$RETENTION_DAYS" -delete
echo "Backup created: $out"
