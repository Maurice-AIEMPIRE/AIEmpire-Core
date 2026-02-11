#!/usr/bin/env bash

set -u

export PATH="/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${AI_EMPIRE_ROOT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
OUT_DIR="$ROOT_DIR/00_SYSTEM/stability"
HEALTH_SCRIPT="$SCRIPT_DIR/openclaw_healthcheck.sh"

mkdir -p "$OUT_DIR"

LOG_FILE="$OUT_DIR/self_heal.log"
REPORT_FILE="$OUT_DIR/last_self_heal.json"
SUMMARY_JSON="$OUT_DIR/last_healthcheck.json"

TARGET_PRIMARY_MODEL="${TARGET_PRIMARY_MODEL:-openai/gpt-5.2}"
TARGET_FB_1="${TARGET_FB_1:-openai/gpt-5.2-codex}"
TARGET_FB_2="${TARGET_FB_2:-openai/gpt-5-mini}"

timestamp_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

log() {
  printf '[%s] %s\n' "$(timestamp_utc)" "$1" >>"$LOG_FILE"
}

run_silent() {
  "$@" >>"$LOG_FILE" 2>&1
}

join_actions() {
  local IFS=','
  printf '%s' "$*"
}

actions=()

# Baseline health snapshot before remediation.
if ! "$HEALTH_SCRIPT" >/dev/null 2>&1; then
  log "health script failed on pre-check"
fi

gateway_ok=0
cron_ok=0
if [ -f "$SUMMARY_JSON" ]; then
  gateway_ok="$(jq -r '.checks.gateway_ok // 0' "$SUMMARY_JSON" 2>/dev/null)"
  cron_ok="$(jq -r '.checks.cron_ok // 0' "$SUMMARY_JSON" 2>/dev/null)"
fi

current_primary="$(openclaw --no-color config get agents.defaults.model.primary 2>/dev/null | tail -n 1)"
if [ "$current_primary" != "$TARGET_PRIMARY_MODEL" ]; then
  if run_silent openclaw models set "$TARGET_PRIMARY_MODEL"; then
    actions+=("set_primary_model")
    log "set primary model to $TARGET_PRIMARY_MODEL"
  else
    log "failed to set primary model"
  fi
fi

current_fallbacks="$(openclaw --no-color config get agents.defaults.model.fallbacks --json 2>/dev/null | sed -n '/^\[/,$p' | jq -c '.' 2>/dev/null)"
target_fallbacks="$(jq -nc --arg f1 "$TARGET_FB_1" --arg f2 "$TARGET_FB_2" '[ $f1, $f2 ]')"
if [ "$current_fallbacks" != "$target_fallbacks" ]; then
  if run_silent openclaw models fallbacks clear \
    && run_silent openclaw models fallbacks add "$TARGET_FB_1" \
    && run_silent openclaw models fallbacks add "$TARGET_FB_2"; then
    actions+=("reset_fallbacks")
    log "reset fallback chain to $TARGET_FB_1,$TARGET_FB_2"
  else
    log "failed to reset fallback chain"
  fi
fi

if [ "$gateway_ok" != "1" ]; then
  if run_silent openclaw gateway restart; then
    actions+=("restart_gateway")
    log "gateway restarted"
    sleep 2
  else
    log "failed to restart gateway"
  fi
fi

if [ "$cron_ok" != "1" ]; then
  if run_silent openclaw gateway restart; then
    actions+=("restart_gateway_for_cron")
    log "gateway restarted for cron recovery"
    sleep 2
  fi
fi

# Post-check.
if ! "$HEALTH_SCRIPT" >/dev/null 2>&1; then
  log "health script failed on post-check"
fi

post_overall="unknown"
post_gateway_ok=0
post_cron_ok=0
if [ -f "$SUMMARY_JSON" ]; then
  post_overall="$(jq -r '.overall // "unknown"' "$SUMMARY_JSON" 2>/dev/null)"
  post_gateway_ok="$(jq -r '.checks.gateway_ok // 0' "$SUMMARY_JSON" 2>/dev/null)"
  post_cron_ok="$(jq -r '.checks.cron_ok // 0' "$SUMMARY_JSON" 2>/dev/null)"
fi

set +u
actions_csv="$(join_actions "${actions[@]}")"
set -u

jq -n \
  --arg timestamp "$(timestamp_utc)" \
  --arg target_primary "$TARGET_PRIMARY_MODEL" \
  --arg actions "$actions_csv" \
  --arg post_overall "$post_overall" \
  --argjson post_gateway_ok "$post_gateway_ok" \
  --argjson post_cron_ok "$post_cron_ok" \
  '{
    timestamp: $timestamp,
    target_primary: $target_primary,
    actions: (if $actions == "" then [] else ($actions | split(",")) end),
    postcheck: {
      overall: $post_overall,
      gateway_ok: $post_gateway_ok,
      cron_ok: $post_cron_ok
    }
  }' >"$REPORT_FILE"

log "self-heal completed post_overall=$post_overall actions=$actions_csv"
cat "$REPORT_FILE"
