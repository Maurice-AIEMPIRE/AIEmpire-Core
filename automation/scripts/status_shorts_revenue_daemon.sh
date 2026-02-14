#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PID_FILE="automation/runs/daemon/shorts_revenue_daemon.pid"
if [ ! -f "$PID_FILE" ]; then
  echo "status=stopped"
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [ -z "$PID" ]; then
  echo "status=stopped"
  exit 0
fi

if ps -p "$PID" >/dev/null 2>&1; then
  echo "status=running"
  echo "pid=$PID"
  exit 0
fi

echo "status=stopped"
