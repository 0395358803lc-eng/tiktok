#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/logs"
MAX_BYTES="${LOG_MAX_BYTES:-10485760}"
KEEP="${LOG_KEEP_FILES:-5}"
mkdir -p "$LOG_DIR"

rotate_one() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  local size
  size="$(stat -c %s "$file" 2>/dev/null || echo 0)"
  (( size >= MAX_BYTES )) || return 0

  for ((i=KEEP; i>=2; i--)); do
    [[ -f "$file.$((i-1))" ]] && mv -f "$file.$((i-1))" "$file.$i"
  done
  cp "$file" "$file.1"
  : > "$file"
}

for file in "$LOG_DIR"/*.log; do
  [[ -e "$file" ]] || continue
  rotate_one "$file"
done
