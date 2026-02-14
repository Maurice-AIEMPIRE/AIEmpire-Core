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

WORKFLOW="${1:-youtube_shorts}"
if [[ "$WORKFLOW" != "youtube_shorts" && "$WORKFLOW" != "shorts_revenue" ]]; then
  echo "Usage: $0 [youtube_shorts|shorts_revenue]" >&2
  exit 1
fi

LATEST_JSON="$ROOT_DIR/content_factory/deliverables/$WORKFLOW/latest.json"
if [ ! -f "$LATEST_JSON" ]; then
  echo "No latest run found for $WORKFLOW" >&2
  exit 1
fi

if command -v jq >/dev/null 2>&1; then
  RUN_ID="$(jq -r '.run_id' "$LATEST_JSON")"
else
  RUN_ID="$(python3 - "$LATEST_JSON" <<'PY'
import json,sys
with open(sys.argv[1],"r",encoding="utf-8") as f:
    print((json.load(f) or {}).get("run_id",""))
PY
)"
fi

if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
  echo "Could not resolve run_id from $LATEST_JSON" >&2
  exit 1
fi

SRC_DIR="$ROOT_DIR/content_factory/deliverables/$WORKFLOW/$RUN_ID"
if [ ! -d "$SRC_DIR" ]; then
  echo "Run dir not found: $SRC_DIR" >&2
  exit 1
fi

sync_target() {
  local target_root="$1"
  local label="$2"
  if [ -z "${target_root:-}" ]; then
    return 0
  fi
  mkdir -p "$target_root/$WORKFLOW"
  local target_dir="$target_root/$WORKFLOW/$RUN_ID"
  rm -rf "$target_dir"
  cp -R "$SRC_DIR" "$target_dir"
  cp "$LATEST_JSON" "$target_root/$WORKFLOW/latest.json"
  echo "Synced $WORKFLOW/$RUN_ID -> $label ($target_dir)"
}

sync_target "${GOOGLE_DRIVE_SHORTS_DIR:-}" "Google Drive"
sync_target "${ICLOUD_SHORTS_DIR:-}" "iCloud"

echo "Sync complete for $WORKFLOW run $RUN_ID"
