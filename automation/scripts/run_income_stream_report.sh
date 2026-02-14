#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

set -a
if [ -f "$ROOT_DIR/ai-vault/empire.env" ]; then
  # shellcheck disable=SC1090
  source "$ROOT_DIR/ai-vault/empire.env"
fi
if [ -f "$HOME/.openclaw/.env" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.openclaw/.env"
fi
set +a

LOOKBACK_HOURS="${STRIPE_LOOKBACK_HOURS:-24}"
MAX_RECORDS="${STRIPE_MAX_RECORDS:-200}"
SEND="${1:-send}"
LOG_DIR="$ROOT_DIR/automation/runs/telegram_income"
mkdir -p "$LOG_DIR"
RUN_TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/income_stream_${RUN_TS}.log"

{
  echo "[income-stream] start ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [ -n "${STRIPE_SECRET_KEY:-}" ]; then
    python3 -m automation.stripe_sync --lookback-hours "$LOOKBACK_HOURS" --max-records "$MAX_RECORDS" || true
  else
    echo "[income-stream] stripe sync skipped: STRIPE_SECRET_KEY missing"
  fi

  if [ "$SEND" = "send" ]; then
    python3 -m automation.income_stream --send
  else
    python3 -m automation.income_stream
  fi
  echo "[income-stream] end ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} 2>&1 | tee -a "$LOG_FILE"
