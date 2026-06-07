#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_PATH="${OGM_CACHE_PRIME_LOG:-"$BACKEND_DIR/logs/prime_generated_caches.log"}"
PID_PATH="${OGM_CACHE_PRIME_PID:-"$BACKEND_DIR/tmp/prime_generated_caches.pid"}"

mkdir -p "$(dirname "$LOG_PATH")" "$(dirname "$PID_PATH")"

if [[ -f "$PID_PATH" ]]; then
  old_pid="$(cat "$PID_PATH" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" >/dev/null 2>&1; then
    echo "Generated cache priming is already running as PID $old_pid"
    echo "Log: $LOG_PATH"
    exit 0
  fi
fi

cd "$BACKEND_DIR"
nohup python scripts/prime_generated_caches.py "$@" >> "$LOG_PATH" 2>&1 < /dev/null &
pid="$!"
printf '%s\n' "$pid" > "$PID_PATH"

echo "Started generated cache priming as PID $pid"
echo "Log: $LOG_PATH"
echo "PID file: $PID_PATH"
