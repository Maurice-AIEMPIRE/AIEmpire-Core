#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/automation/runs/operating_day"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/day_cycle_$(date +%Y%m%d).log"

now_hm() { date +%H:%M; }
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"; }

in_window() {
  local now
  now="$(date +%H%M)"
  [ "$now" -ge 0800 ] && [ "$now" -lt 2300 ]
}

log "start mode=operating_day timezone=$(date +%Z)"

# 07:55 precheck
log "checkpoint=07:55 precheck"
python3 automation/scripts/preflight_gate.py >> "$LOG_FILE" 2>&1 || true

if in_window; then
  # 08:00 outbound/autopilot start
  log "checkpoint=08:00 service_outbound_start"
  python3 automation/scripts/write_daily_kpi.py >> "$LOG_FILE" 2>&1 || true
  # Keep run short in cycle mode; recurring launchd handles repetition.
  EXECUTE_MODE=1 PREFLIGHT_GATE=1 SAFETY_GUARD=1 HOURS=1 INTERVAL_MIN=30 \
    automation/scripts/run_shorts_revenue_autopilot.sh 1 30 >> "$LOG_FILE" 2>&1 || true

  # 12:30 KPI checkpoint
  log "checkpoint=12:30 midday_kpi"
  python3 automation/scripts/write_daily_kpi.py >> "$LOG_FILE" 2>&1 || true

  # 18:00 closing block
  log "checkpoint=18:00 closing_block"
  python3 automation/scripts/write_thread_handoff.py >> "$LOG_FILE" 2>&1 || true
fi

# 22:30 degrade+snapshot
log "checkpoint=22:30 shutdown_degrade_snapshot"
python3 automation/scripts/run_degrade_maintenance.py >> "$LOG_FILE" 2>&1 || true
python3 automation/scripts/audit_infra_runtime.py --mode snapshot --output "$ROOT_DIR/00_SYSTEM/infra/SYSTEM_INVENTORY_2026-02-18.json" --redact-secrets true >> "$LOG_FILE" 2>&1 || true

log "done log_file=$LOG_FILE"
