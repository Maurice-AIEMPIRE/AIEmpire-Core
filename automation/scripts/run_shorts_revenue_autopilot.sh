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

if ! [[ "$HOURS" =~ ^[0-9]+$ ]]; then
  echo "ERROR: HOURS must be an integer" >&2
  exit 1
fi
if ! [[ "$INTERVAL_MIN" =~ ^[0-9]+$ ]] || [ "$INTERVAL_MIN" -le 0 ]; then
  echo "ERROR: INTERVAL_MIN must be a positive integer" >&2
  exit 1
fi

RUNS=$(( (HOURS * 60 + INTERVAL_MIN - 1) / INTERVAL_MIN ))
if [ "$RUNS" -lt 1 ]; then
  RUNS=1
fi

LOG_DIR="$ROOT_DIR/automation/runs/shorts_revenue_autopilot"
mkdir -p "$LOG_DIR"
SESSION_TS="$(date +%Y%m%d_%H%M%S)"
SESSION_LOG="$LOG_DIR/session_${SESSION_TS}.log"

echo "[shorts-revenue] start ts=$(date -u +%Y-%m-%dT%H:%M:%SZ) runs=$RUNS interval_min=$INTERVAL_MIN execute_mode=$EXECUTE_MODE" | tee -a "$SESSION_LOG"

SUCCESS_COUNT=0
FAIL_COUNT=0

for ((i=1; i<=RUNS; i++)); do
  echo "[shorts-revenue] run=$i/$RUNS ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$SESSION_LOG"

  CMD=(python3 -m automation run --workflow shorts_revenue)
  if [ "$EXECUTE_MODE" = "1" ]; then
    CMD+=(--execute)
  fi

  set +e
  "${CMD[@]}" | tee -a "$SESSION_LOG"
  RC=${PIPESTATUS[0]}
  set -e

  if [ "$RC" -eq 0 ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    echo "[shorts-revenue] run=$i status=ok" | tee -a "$SESSION_LOG"
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "[shorts-revenue] run=$i status=error exit_code=$RC (continuing)" | tee -a "$SESSION_LOG"
  fi

  if [ "$SYNC_SHORTS_ASSETS" = "1" ]; then
    automation/scripts/sync_shorts_assets.sh shorts_revenue | tee -a "$SESSION_LOG" || true
  fi

  if [ "$i" -lt "$RUNS" ]; then
    sleep "$((INTERVAL_MIN * 60))"
  fi
done

echo "[shorts-revenue] finished ts=$(date -u +%Y-%m-%dT%H:%M:%SZ) success=$SUCCESS_COUNT fail=$FAIL_COUNT" | tee -a "$SESSION_LOG"
