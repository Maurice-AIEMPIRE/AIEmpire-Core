#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

HOURS="${1:-10}"
INTERVAL_MIN="${2:-30}"
EXECUTE_MODE="${EXECUTE_MODE:-1}"
SYNC_SHORTS_ASSETS="${SYNC_SHORTS_ASSETS:-0}"

if ! [[ "$HOURS" =~ ^[0-9]+$ ]]; then
  echo "ERROR: HOURS must be an integer" >&2
  exit 1
fi
if ! [[ "$INTERVAL_MIN" =~ ^[0-9]+$ ]] || [ "$INTERVAL_MIN" -le 0 ]; then
  echo "ERROR: INTERVAL_MIN must be a positive integer" >&2
  exit 1
fi

mkdir -p automation/runs/daemon
PID_FILE="automation/runs/daemon/shorts_revenue_daemon.pid"
TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="automation/runs/daemon/shorts_revenue_10h_${TS}.log"

if [ -f "$PID_FILE" ]; then
  OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$OLD_PID" ] && ps -p "$OLD_PID" >/dev/null 2>&1; then
    echo "Daemon already running with PID $OLD_PID"
    exit 0
  fi
fi

nohup env EXECUTE_MODE="$EXECUTE_MODE" SYNC_SHORTS_ASSETS="$SYNC_SHORTS_ASSETS" \
  automation/scripts/run_shorts_revenue_autopilot.sh "$HOURS" "$INTERVAL_MIN" > "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

echo "started"
echo "pid=$PID"
echo "log=$LOG_FILE"
