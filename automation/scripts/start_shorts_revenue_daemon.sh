#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [ -f "$ROOT_DIR/ai-vault/empire.env" ]; then
  # shellcheck disable=SC1090
  source "$ROOT_DIR/ai-vault/empire.env"
fi
if [ -f "$HOME/.openclaw/.env" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.openclaw/.env"
fi

HOURS="${1:-10}"
INTERVAL_MIN="${2:-30}"
EXECUTE_MODE="${EXECUTE_MODE:-1}"
SYNC_SHORTS_ASSETS="${SYNC_SHORTS_ASSETS:-0}"
AUTO_PUBLISH_YOUTUBE="${AUTO_PUBLISH_YOUTUBE:-1}"
AUTO_PUBLISH_MODE="${AUTO_PUBLISH_MODE:-public}"
AUTO_PUBLISH_MAX_PER_RUN="${AUTO_PUBLISH_MAX_PER_RUN:-1}"
AUTO_PUBLISH_MAX_PER_DAY="${AUTO_PUBLISH_MAX_PER_DAY:-6}"
AUTO_PUBLISH_MIN_SPACING_MIN="${AUTO_PUBLISH_MIN_SPACING_MIN:-120}"
X_SCOUT_ENABLED="${X_SCOUT_ENABLED:-1}"
SAFETY_GUARD="${SAFETY_GUARD:-1}"
SAFETY_COOLDOWN_MIN="${SAFETY_COOLDOWN_MIN:-20}"
AUTOPILOT_NICE="${AUTOPILOT_NICE:-10}"
MAX_LOAD_PER_CORE="${MAX_LOAD_PER_CORE:-0.85}"
MIN_CPU_SPEED_LIMIT="${MIN_CPU_SPEED_LIMIT:-80}"
MIN_MEMORY_FREE_PERCENT="${MIN_MEMORY_FREE_PERCENT:-12}"
ATLAS_SNAPSHOT_ENABLED="${ATLAS_SNAPSHOT_ENABLED:-1}"
DEGRADE_MAINTENANCE_ON_BLOCK="${DEGRADE_MAINTENANCE_ON_BLOCK:-1}"
CAFFEINATE_DAEMON="${CAFFEINATE_DAEMON:-1}"

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
  AUTO_PUBLISH_YOUTUBE="$AUTO_PUBLISH_YOUTUBE" AUTO_PUBLISH_MODE="$AUTO_PUBLISH_MODE" \
  AUTO_PUBLISH_MAX_PER_RUN="$AUTO_PUBLISH_MAX_PER_RUN" AUTO_PUBLISH_MAX_PER_DAY="$AUTO_PUBLISH_MAX_PER_DAY" \
  AUTO_PUBLISH_MIN_SPACING_MIN="$AUTO_PUBLISH_MIN_SPACING_MIN" \
  X_SCOUT_ENABLED="$X_SCOUT_ENABLED" SAFETY_GUARD="$SAFETY_GUARD" SAFETY_COOLDOWN_MIN="$SAFETY_COOLDOWN_MIN" \
  AUTOPILOT_NICE="$AUTOPILOT_NICE" MAX_LOAD_PER_CORE="$MAX_LOAD_PER_CORE" MIN_CPU_SPEED_LIMIT="$MIN_CPU_SPEED_LIMIT" \
  MIN_MEMORY_FREE_PERCENT="$MIN_MEMORY_FREE_PERCENT" ATLAS_SNAPSHOT_ENABLED="$ATLAS_SNAPSHOT_ENABLED" \
  DEGRADE_MAINTENANCE_ON_BLOCK="$DEGRADE_MAINTENANCE_ON_BLOCK" \
  automation/scripts/run_shorts_revenue_autopilot.sh "$HOURS" "$INTERVAL_MIN" > "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

if [ "$CAFFEINATE_DAEMON" = "1" ] && command -v caffeinate >/dev/null 2>&1; then
  nohup caffeinate -d -i -m -s -w "$PID" >/dev/null 2>&1 &
fi

echo "started"
echo "pid=$PID"
echo "log=$LOG_FILE"
