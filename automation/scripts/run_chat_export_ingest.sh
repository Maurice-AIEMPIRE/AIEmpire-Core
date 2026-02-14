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

EXPORT_DIR="${CHATGPT_EXPORT_DIR:-}"
EXPORT_ZIP="${CHATGPT_EXPORT_ZIP:-}"
CONVERSATION_LIMIT="${CHATGPT_CONVERSATION_LIMIT:-0}"
SINCE_DATE="${CHATGPT_SINCE_DATE:-}"
EXECUTE_MODE="${EXECUTE_MODE:-1}"
SAFETY_GUARD="${SAFETY_GUARD:-1}"
AUTOPILOT_NICE="${AUTOPILOT_NICE:-12}"

LOG_DIR="$ROOT_DIR/automation/runs/launchd"
mkdir -p "$LOG_DIR"
RUN_TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/chat_export_ingest_${RUN_TS}.log"

CMD=(nice -n "$AUTOPILOT_NICE" python3 -m automation.ingest --source chatgpt_export --conversation-limit "$CONVERSATION_LIMIT")

if [ -n "$EXPORT_ZIP" ]; then
  CMD+=(--export-zip "$EXPORT_ZIP")
elif [ -n "$EXPORT_DIR" ]; then
  CMD+=(--export-dir "$EXPORT_DIR")
fi

if [ -n "$SINCE_DATE" ]; then
  CMD+=(--since-date "$SINCE_DATE")
fi

if [ "$EXECUTE_MODE" = "1" ]; then
  CMD+=(--execute)
fi

{
  echo "[chat-export-ingest] start ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [ "$SAFETY_GUARD" = "1" ]; then
    set +e
    automation/scripts/system_safety_guard.sh
    GRC=$?
    set -e
    if [ "$GRC" -ne 0 ]; then
      echo "[chat-export-ingest] skipped reason=safety_guard exit_code=$GRC"
      exit 0
    fi
  fi
  echo "[chat-export-ingest] cmd=${CMD[*]}"
  set +e
  "${CMD[@]}"
  RC=$?
  set -e
  echo "[chat-export-ingest] exit_code=$RC ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit "$RC"
} 2>&1 | tee -a "$LOG_FILE"
