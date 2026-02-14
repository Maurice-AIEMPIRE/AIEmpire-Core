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

LOG_DIR="$ROOT_DIR/automation/runs/launchd"
mkdir -p "$LOG_DIR"
RUN_TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/shorts_revenue_once_${RUN_TS}.log"

{
  echo "[shorts-revenue-once] start ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  set +e
  python3 -m automation run --workflow shorts_revenue --execute
  RC=$?
  set -e
  if [ "${AUTO_PUBLISH_YOUTUBE:-0}" = "1" ] && [ "$RC" -eq 0 ]; then
    automation/scripts/auto_publish_youtube_queue.sh shorts_revenue || true
  fi
  if [ "${TELEGRAM_INCOME_STREAM:-1}" = "1" ] && [ "$RC" -eq 0 ] && [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
    automation/scripts/run_income_stream_report.sh send || true
  fi
  echo "[shorts-revenue-once] exit_code=$RC ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit "$RC"
} 2>&1 | tee -a "$LOG_FILE"
