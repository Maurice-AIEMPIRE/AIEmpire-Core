#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PID_FILE="automation/runs/daemon/shorts_revenue_daemon.pid"
if [ ! -f "$PID_FILE" ]; then
  echo "already_stopped"
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [ -z "$PID" ]; then
  rm -f "$PID_FILE"
  echo "already_stopped"
  exit 0
fi

if ps -p "$PID" >/dev/null 2>&1; then
  kill "$PID" || true
fi

rm -f "$PID_FILE"
echo "stopped"
