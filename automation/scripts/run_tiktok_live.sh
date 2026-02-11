#!/usr/bin/env bash

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR" || exit 1

RUN_ID="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT_DIR/automation/runs/tiktok_live_${RUN_ID}"
REPORT_FILE="$OUT_DIR/session.md"

mkdir -p "$OUT_DIR"

log() {
  local line="$1"
  printf '%s\n' "$line" | tee -a "$REPORT_FILE"
}

run_cmd() {
  log ""
  log "\$ $*"
  local output rc
  set +e
  output="$("$@" 2>&1)"
  rc=$?
  set -e
  if [[ -n "$output" ]]; then
    printf '%s\n' "$output" | tee -a "$REPORT_FILE"
  fi
  log "exit_code=$rc"
  return "$rc"
}

set -e
log "# TikTok Live Session"
log "run_id: $RUN_ID"
log "started_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
log ""

log "## Step 1: Generate PKCE"
PKCE_JSON="$(python3 -m automation.tiktok pkce)"
log ""
log "\$ python3 -m automation.tiktok pkce"
printf '%s\n' "$PKCE_JSON" | tee -a "$REPORT_FILE"
log "exit_code=0"
printf '%s\n' "$PKCE_JSON" > "$OUT_DIR/pkce.json"
PKCE_EXTRACT="$(printf '%s\n' "$PKCE_JSON" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["code_verifier"]); print(d["code_challenge"]); print(d["code_challenge_method"])')"
CODE_VERIFIER="$(printf '%s\n' "$PKCE_EXTRACT" | sed -n '1p')"
CODE_CHALLENGE="$(printf '%s\n' "$PKCE_EXTRACT" | sed -n '2p')"
CODE_CHALLENGE_METHOD="$(printf '%s\n' "$PKCE_EXTRACT" | sed -n '3p')"

export TIKTOK_CODE_VERIFIER="$CODE_VERIFIER"
export TIKTOK_CODE_CHALLENGE="$CODE_CHALLENGE"
export TIKTOK_CODE_CHALLENGE_METHOD="$CODE_CHALLENGE_METHOD"

log "Saved PKCE: $OUT_DIR/pkce.json"

CLIENT_KEY="${TIKTOK_CLIENT_KEY:-demo_client_key}"
REDIRECT_URI="${TIKTOK_REDIRECT_URI:-https://example.com/callback}"
SCOPES="${TIKTOK_SCOPES:-user.info.basic,video.list,video.upload,video.publish}"
STATE_VALUE="${TIKTOK_STATE:-live-${RUN_ID}}"

log ""
log "## Step 2: Build OAuth URL"
AUTH_URL="$(python3 -m automation.tiktok auth-url \
  --client-key "$CLIENT_KEY" \
  --redirect-uri "$REDIRECT_URI" \
  --scopes "$SCOPES" \
  --state "$STATE_VALUE" \
  --code-challenge "$CODE_CHALLENGE" \
  --code-challenge-method "$CODE_CHALLENGE_METHOD")"

printf '%s\n' "$AUTH_URL" > "$OUT_DIR/auth_url.txt"
log "auth_url:"
log "$AUTH_URL"
log "Saved OAuth URL: $OUT_DIR/auth_url.txt"

log ""
log "## Step 3: Live TikTok API checks (if token exists)"

if [[ -n "${TIKTOK_ACCESS_TOKEN:-}" ]]; then
  run_cmd python3 -m automation.tiktok user-info
  run_cmd python3 -m automation.tiktok creator-info
  run_cmd python3 -m automation.tiktok video-list --max-count 10
else
  log "Skipping API checks: TIKTOK_ACCESS_TOKEN is not set."
fi

if [[ -n "${TIKTOK_REFRESH_TOKEN:-}" && -n "${TIKTOK_CLIENT_KEY:-}" && -n "${TIKTOK_CLIENT_SECRET:-}" ]]; then
  run_cmd python3 -m automation.tiktok refresh-token
else
  log "Skipping refresh: requires TIKTOK_REFRESH_TOKEN, TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET."
fi

log ""
log "## Next Commands"
log "1. Open auth URL and complete consent."
log "2. Exchange code:"
log "   python3 -m automation.tiktok exchange-code --code \"<AUTH_CODE>\""
log "3. Set token and rerun:"
log "   TIKTOK_ACCESS_TOKEN=\"...\" automation/scripts/run_tiktok_live.sh"
log ""
log "finished_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
log "report: $REPORT_FILE"

printf '%s\n' "$REPORT_FILE"
