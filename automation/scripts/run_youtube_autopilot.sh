#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

# Optional env sources
if [ -f "$ROOT_DIR/ai-vault/empire.env" ]; then
  # shellcheck disable=SC1090
  source "$ROOT_DIR/ai-vault/empire.env"
fi
if [ -f "$HOME/.openclaw/.env" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.openclaw/.env"
fi
export OLLAMA_API_KEY="${OLLAMA_API_KEY:-local}"
export OLLAMA_PRIMARY_MODEL="${OLLAMA_PRIMARY_MODEL:-minimax-m2.5:cloud}"

HOURS="${1:-10}"
INTERVAL_MIN="${2:-30}"
EXECUTE_MODE="${EXECUTE_MODE:-1}"
CHANNEL_ID="${YOUTUBE_CHANNEL_ID:-}"
SYNC_SHORTS_ASSETS="${SYNC_SHORTS_ASSETS:-0}"
AUTO_PUBLISH_YOUTUBE="${AUTO_PUBLISH_YOUTUBE:-1}"
X_SCOUT_ENABLED="${X_SCOUT_ENABLED:-1}"
SAFETY_GUARD="${SAFETY_GUARD:-1}"
SAFETY_COOLDOWN_MIN="${SAFETY_COOLDOWN_MIN:-20}"
AUTOPILOT_NICE="${AUTOPILOT_NICE:-10}"
ATLAS_SNAPSHOT_ENABLED="${ATLAS_SNAPSHOT_ENABLED:-1}"
DEGRADE_MAINTENANCE_ON_BLOCK="${DEGRADE_MAINTENANCE_ON_BLOCK:-1}"
TELEGRAM_INCOME_STREAM="${TELEGRAM_INCOME_STREAM:-1}"
AUTO_COMMIT_ENABLED="${AUTO_COMMIT_ENABLED:-1}"
AUTO_COMMIT_PUSH="${AUTO_COMMIT_PUSH:-0}"

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

LOG_DIR="$ROOT_DIR/automation/runs/youtube_autopilot"
mkdir -p "$LOG_DIR"
SESSION_TS="$(date +%Y%m%d_%H%M%S)"
SESSION_LOG="$LOG_DIR/session_${SESSION_TS}.log"

echo "[youtube-autopilot] start ts=$(date -u +%Y-%m-%dT%H:%M:%SZ) runs=$RUNS interval_min=$INTERVAL_MIN execute_mode=$EXECUTE_MODE" | tee -a "$SESSION_LOG"

SUCCESS_COUNT=0
FAIL_COUNT=0

for ((i=1; i<=RUNS; i++)); do
  echo "[youtube-autopilot] run=$i/$RUNS ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$SESSION_LOG"

  if [ "$SAFETY_GUARD" = "1" ]; then
    set +e
    automation/scripts/system_safety_guard.sh | tee -a "$SESSION_LOG"
    GRC=${PIPESTATUS[0]}
    set -e
    if [ "$GRC" -ne 0 ]; then
      echo "[youtube-autopilot] run=$i status=skipped reason=safety_guard exit_code=$GRC" | tee -a "$SESSION_LOG"
      if [ "$DEGRADE_MAINTENANCE_ON_BLOCK" = "1" ]; then
        echo "[youtube-autopilot] run=$i degrade_mode=on maintenance=ingest+merge+strategy_refresh" | tee -a "$SESSION_LOG"
        nice -n "$AUTOPILOT_NICE" python3 automation/scripts/run_degrade_maintenance.py | tee -a "$SESSION_LOG" || true
      fi
      if [ "$AUTO_COMMIT_ENABLED" = "1" ]; then
        automation/scripts/run_auto_commit.sh youtube_shorts "$i" "$RUNS" | tee -a "$SESSION_LOG" || true
      fi
      if [ "$i" -lt "$RUNS" ]; then
        sleep "$((SAFETY_COOLDOWN_MIN * 60))"
      fi
      continue
    fi
  fi

  if [ "$ATLAS_SNAPSHOT_ENABLED" = "1" ]; then
    automation/scripts/collect_atlas_history_snapshot.sh | tee -a "$SESSION_LOG" || true
  fi

  if [ "$X_SCOUT_ENABLED" = "1" ]; then
    nice -n "$AUTOPILOT_NICE" python3 automation/scripts/run_x_trend_scout.py | tee -a "$SESSION_LOG" || true
  fi

  CMD=(nice -n "$AUTOPILOT_NICE" python3 -m automation run --workflow youtube_shorts)

  if [ "$EXECUTE_MODE" = "1" ]; then
    CMD+=(--execute)
  fi

  if [ -n "$CHANNEL_ID" ]; then
    CMD+=(--youtube-channel-id "$CHANNEL_ID")
  fi

  set +e
  "${CMD[@]}" | tee -a "$SESSION_LOG"
  RC=${PIPESTATUS[0]}
  set -e

  if [ "$RC" -eq 0 ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    echo "[youtube-autopilot] run=$i status=ok" | tee -a "$SESSION_LOG"
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "[youtube-autopilot] run=$i status=error exit_code=$RC (continuing)" | tee -a "$SESSION_LOG"
  fi

  if [ "$SYNC_SHORTS_ASSETS" = "1" ]; then
    automation/scripts/sync_shorts_assets.sh youtube_shorts | tee -a "$SESSION_LOG" || true
  fi

  if [ "$AUTO_PUBLISH_YOUTUBE" = "1" ] && [ "$RC" -eq 0 ]; then
    automation/scripts/auto_publish_youtube_queue.sh youtube_shorts | tee -a "$SESSION_LOG" || true
  fi

  if [ "$TELEGRAM_INCOME_STREAM" = "1" ] && [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
    automation/scripts/run_income_stream_report.sh send | tee -a "$SESSION_LOG" || true
  fi

  if [ "$AUTO_COMMIT_ENABLED" = "1" ]; then
    automation/scripts/run_auto_commit.sh youtube_shorts "$i" "$RUNS" | tee -a "$SESSION_LOG" || true
  fi

  if [ "$i" -lt "$RUNS" ]; then
    sleep "$((INTERVAL_MIN * 60))"
  fi

done

echo "[youtube-autopilot] finished ts=$(date -u +%Y-%m-%dT%H:%M:%SZ) success=$SUCCESS_COUNT fail=$FAIL_COUNT" | tee -a "$SESSION_LOG"
