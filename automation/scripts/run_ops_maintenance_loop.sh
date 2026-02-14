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

LOOP_SLEEP_SEC="${OPS_LOOP_SLEEP_SEC:-300}"
CHAT_EXPORT_INTERVAL_SEC="${CHAT_EXPORT_INTERVAL_SEC:-21600}"   # 6h
INCOME_INTERVAL_SEC="${INCOME_INTERVAL_SEC:-3600}"               # 1h
STRIPE_SYNC_INTERVAL_SEC="${STRIPE_SYNC_INTERVAL_SEC:-7200}"     # 2h
HANDOFF_INTERVAL_SEC="${HANDOFF_INTERVAL_SEC:-7200}"             # 2h

STATE_DIR="$ROOT_DIR/automation/runs/ops_state"
LOG_DIR="$ROOT_DIR/automation/runs/ops"
mkdir -p "$STATE_DIR" "$LOG_DIR"
LOG_FILE="$LOG_DIR/ops_maintenance_$(date +%Y%m%d_%H%M%S).log"

is_due() {
  local key="$1"
  local interval="$2"
  local stamp_file="$STATE_DIR/${key}.stamp"
  if [ ! -f "$stamp_file" ]; then
    return 0
  fi
  local now
  now="$(date +%s)"
  local last
  last="$(cat "$stamp_file" 2>/dev/null || echo 0)"
  if ! [[ "$last" =~ ^[0-9]+$ ]]; then
    return 0
  fi
  if [ $((now - last)) -ge "$interval" ]; then
    return 0
  fi
  return 1
}

mark_done() {
  local key="$1"
  date +%s > "$STATE_DIR/${key}.stamp"
}

echo "[ops-loop] start ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_FILE"

while true; do
  if is_due "chat_export_ingest" "$CHAT_EXPORT_INTERVAL_SEC"; then
    echo "[ops-loop] task=chat_export_ingest ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_FILE"
    automation/scripts/run_chat_export_ingest.sh >> "$LOG_FILE" 2>&1 || true
    mark_done "chat_export_ingest"
  fi

  if is_due "income_stream" "$INCOME_INTERVAL_SEC"; then
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
      echo "[ops-loop] task=income_stream ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_FILE"
      automation/scripts/run_income_stream_report.sh send >> "$LOG_FILE" 2>&1 || true
    else
      echo "[ops-loop] task=income_stream skipped reason=telegram_missing" | tee -a "$LOG_FILE"
    fi
    mark_done "income_stream"
  fi

  if is_due "stripe_sync" "$STRIPE_SYNC_INTERVAL_SEC"; then
    if [ -n "${STRIPE_SECRET_KEY:-}" ]; then
      echo "[ops-loop] task=stripe_sync ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_FILE"
      automation/scripts/run_stripe_sync.sh >> "$LOG_FILE" 2>&1 || true
    else
      echo "[ops-loop] task=stripe_sync skipped reason=stripe_key_missing" | tee -a "$LOG_FILE"
    fi
    mark_done "stripe_sync"
  fi

  if is_due "handoff" "$HANDOFF_INTERVAL_SEC"; then
    echo "[ops-loop] task=thread_handoff ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG_FILE"
    python3 automation/scripts/write_thread_handoff.py >> "$LOG_FILE" 2>&1 || true
    mark_done "handoff"
  fi

  sleep "$LOOP_SLEEP_SEC"
done
