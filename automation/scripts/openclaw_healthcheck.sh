#!/usr/bin/env bash

set -u

export PATH="/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${AI_EMPIRE_ROOT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
OUT_DIR="$ROOT_DIR/00_SYSTEM/stability"

mkdir -p "$OUT_DIR"

LOG_FILE="$OUT_DIR/healthcheck.log"
GATEWAY_JSON="$OUT_DIR/gateway_health.json"
CRON_JSON="$OUT_DIR/cron_status.json"
STATUS_JSON="$OUT_DIR/openclaw_status.json"
SUMMARY_JSON="$OUT_DIR/last_healthcheck.json"

timestamp_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

log() {
  printf '[%s] %s\n' "$(timestamp_utc)" "$1" >>"$LOG_FILE"
}

run_openclaw_json() {
  local cmd="$1"
  local out_file="$2"
  local raw_file="${out_file}.raw"
  local clean_file="${out_file}.tmp"

  if eval "$cmd" >"$raw_file" 2>&1; then
    sed -n '/^{/,$p' "$raw_file" >"$clean_file"
    if [ -s "$clean_file" ]; then
      mv "$clean_file" "$out_file"
      return 0
    fi
  fi
  return 1
}

gateway_ok=0
cron_ok=0
status_ok=0

if run_openclaw_json "openclaw --no-color gateway health --json" "$GATEWAY_JSON"; then
  gateway_ok=1
else
  log "gateway health check failed"
fi

if run_openclaw_json "openclaw --no-color cron status --json" "$CRON_JSON"; then
  cron_ok=1
else
  log "cron status check failed"
fi

if run_openclaw_json "openclaw --no-color status --json" "$STATUS_JSON"; then
  status_ok=1
else
  log "status check failed"
fi

configured_primary="$(openclaw --no-color config get agents.defaults.model.primary 2>/dev/null | tail -n 1)"
configured_fallbacks="$(openclaw --no-color config get agents.defaults.model.fallbacks --json 2>/dev/null | sed -n '/^\[/,$p')"
[ -n "$configured_fallbacks" ] || configured_fallbacks='[]'

disk_used="$(df -h "$HOME" | awk 'NR==2 {print $5}')"
disk_pct="${disk_used%%%}"

overall="ok"
if [ "$gateway_ok" -eq 0 ] || [ "$cron_ok" -eq 0 ] || [ "$status_ok" -eq 0 ]; then
  overall="degraded"
fi
if [ "${disk_pct:-0}" -ge 95 ]; then
  overall="critical"
fi

jq -n \
  --arg timestamp "$(timestamp_utc)" \
  --arg overall "$overall" \
  --arg configured_primary "$configured_primary" \
  --argjson configured_fallbacks "$configured_fallbacks" \
  --arg disk_used "$disk_used" \
  --argjson gateway_ok "$gateway_ok" \
  --argjson cron_ok "$cron_ok" \
  --argjson status_ok "$status_ok" \
  '{
    timestamp: $timestamp,
    overall: $overall,
    checks: {
      gateway_ok: $gateway_ok,
      cron_ok: $cron_ok,
      status_ok: $status_ok
    },
    config: {
      primary: $configured_primary,
      fallbacks: $configured_fallbacks
    },
    host: {
      disk_used: $disk_used
    }
  }' >"$SUMMARY_JSON"

if [ "$overall" = "ok" ]; then
  log "healthcheck ok primary=$configured_primary disk=$disk_used"
else
  log "healthcheck $overall primary=$configured_primary disk=$disk_used"
fi

cat "$SUMMARY_JSON"
