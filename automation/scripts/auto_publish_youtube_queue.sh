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

WORKFLOW="${1:-shorts_revenue}"
if [[ "$WORKFLOW" != "shorts_revenue" && "$WORKFLOW" != "youtube_shorts" ]]; then
  echo "Usage: $0 [shorts_revenue|youtube_shorts]" >&2
  exit 1
fi

MODE="${AUTO_PUBLISH_MODE:-public}"
MAX_POSTS="${AUTO_PUBLISH_MAX_PER_RUN:-1}"
MAX_POSTS_PER_DAY="${AUTO_PUBLISH_MAX_PER_DAY:-6}"
MIN_SPACING_MIN="${AUTO_PUBLISH_MIN_SPACING_MIN:-120}"
DRY_RUN="${AUTO_PUBLISH_DRY_RUN:-0}"
LOG_DIR="$ROOT_DIR/automation/runs/publish"
mkdir -p "$LOG_DIR"
RUN_TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/youtube_publish_${WORKFLOW}_${RUN_TS}.log"

CMD=(
  python3 -m automation.youtube_publish
  --workflow "$WORKFLOW"
  --max-posts "$MAX_POSTS"
  --max-posts-per-day "$MAX_POSTS_PER_DAY"
  --min-spacing-min "$MIN_SPACING_MIN"
  --mode "$MODE"
)
if [ "$DRY_RUN" = "1" ]; then
  CMD+=(--dry-run)
fi

{
  echo "[youtube-publish] start ts=$(date -u +%Y-%m-%dT%H:%M:%SZ) workflow=$WORKFLOW mode=$MODE max_posts=$MAX_POSTS max_posts_per_day=$MAX_POSTS_PER_DAY min_spacing_min=$MIN_SPACING_MIN dry_run=$DRY_RUN"
  set +e
  "${CMD[@]}"
  RC=$?
  set -e
  echo "[youtube-publish] exit_code=$RC ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit "$RC"
} 2>&1 | tee -a "$LOG_FILE"
