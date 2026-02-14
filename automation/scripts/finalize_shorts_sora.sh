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

MAX_RENDERS="${1:-6}"
if ! [[ "$MAX_RENDERS" =~ ^[0-9]+$ ]] || [ "$MAX_RENDERS" -lt 1 ]; then
  echo "ERROR: MAX_RENDERS must be a positive integer" >&2
  exit 1
fi

export VIDEO_PROVIDER="${VIDEO_PROVIDER:-sora}"
export SORA_VIDEO_ENABLED="${SORA_VIDEO_ENABLED:-1}"
export SORA_MODEL="${SORA_MODEL:-sora-2}"
export SORA_SIZE="${SORA_SIZE:-720x1280}"
export EXECUTE_MODE=1

echo "[finalize-sora] provider=$VIDEO_PROVIDER model=$SORA_MODEL size=$SORA_SIZE max_renders=$MAX_RENDERS"
if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "[finalize-sora] OPENAI_API_KEY missing -> local ffmpeg fallback will be used."
fi

python3 -m automation run --workflow shorts_revenue --execute --video-provider "$VIDEO_PROVIDER" --video-max-renders "$MAX_RENDERS"

if [ -n "${YOUTUBE_CLIENT_ID:-}" ] && [ -n "${YOUTUBE_CLIENT_SECRET:-}" ] && [ -n "${YOUTUBE_REFRESH_TOKEN:-}" ]; then
  echo "[finalize-sora] YouTube credentials found -> running auto publish."
  automation/scripts/auto_publish_youtube_queue.sh shorts_revenue || true
else
  echo "[finalize-sora] YouTube OAuth credentials missing -> videos queued only (no upload)."
fi

echo "[finalize-sora] done."

