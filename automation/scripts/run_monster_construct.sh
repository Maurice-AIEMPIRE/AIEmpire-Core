#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

APPLY_CONSOLIDATION=0
while [ $# -gt 0 ]; do
  case "$1" in
    --apply-consolidation)
      APPLY_CONSOLIDATION=1
      ;;
    *)
      echo "Usage: $0 [--apply-consolidation]" >&2
      exit 1
      ;;
  esac
  shift
done

TODAY="$(date +%Y-%m-%d)"
LOG_DIR="$ROOT_DIR/automation/runs/monster_construct"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/monster_construct_${TODAY}_$(date +%H%M%S).log"

INVENTORY_OUT="$ROOT_DIR/00_SYSTEM/infra/SYSTEM_INVENTORY_${TODAY}.json"
CONSOLIDATION_OUT="$ROOT_DIR/00_SYSTEM/infra/LAUNCHD_CONSOLIDATION_REPORT_${TODAY}.md"
MASTER_MD_OUT="$ROOT_DIR/00_SYSTEM/MONSTER_CONSTRUCT_MASTER.md"
MASTER_JSON_OUT="$ROOT_DIR/00_SYSTEM/MONSTER_CONSTRUCT_MASTER.json"

FAILURES=()

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"
}

run_step() {
  local step="$1"
  shift
  log "step=$step status=start"
  if "$@" >>"$LOG_FILE" 2>&1; then
    log "step=$step status=ok"
  else
    local rc=$?
    FAILURES+=("${step}:${rc}")
    log "step=$step status=fail rc=$rc"
  fi
}

run_preflight() {
  local step="preflight_gate"
  log "step=$step status=start"
  set +e
  python3 automation/scripts/preflight_gate.py >>"$LOG_FILE" 2>&1
  local rc=$?
  set -e
  if [ "$rc" -eq 0 ] || [ "$rc" -eq 2 ]; then
    log "step=$step status=ok rc=$rc"
  else
    FAILURES+=("${step}:${rc}")
    log "step=$step status=fail rc=$rc"
  fi
}

log "mode=monster_construct apply_consolidation=$APPLY_CONSOLIDATION"
log "root=$ROOT_DIR"

run_preflight
run_step "audit_snapshot" python3 automation/scripts/audit_infra_runtime.py --mode snapshot --output "$INVENTORY_OUT" --redact-secrets true
run_step "audit_verify" python3 automation/scripts/audit_infra_runtime.py --mode verify --output "$INVENTORY_OUT" --redact-secrets true

if [ "$APPLY_CONSOLIDATION" = "1" ]; then
  run_step "launchd_consolidation_apply" python3 automation/scripts/consolidate_launchd_runtime.py --output "$CONSOLIDATION_OUT"
else
  run_step "launchd_consolidation_dry_run" python3 automation/scripts/consolidate_launchd_runtime.py --dry-run --output "$CONSOLIDATION_OUT"
fi

run_step "daily_kpi" python3 automation/scripts/write_daily_kpi.py --date "$TODAY"
run_step "chat_artifacts_index" python3 automation/scripts/build_master_chat_artifact_index.py --output "$ROOT_DIR/00_SYSTEM/chat_artifacts/MASTER_CHAT_ARTIFACTS_INDEX.md" --priority-limit 120
run_step "monster_master_build" python3 automation/scripts/build_monster_construct.py --inventory "$INVENTORY_OUT" --output "$MASTER_MD_OUT" --json-output "$MASTER_JSON_OUT"

if [ ${#FAILURES[@]} -eq 0 ]; then
  log "status=ok output_md=$MASTER_MD_OUT output_json=$MASTER_JSON_OUT"
  echo "$MASTER_MD_OUT"
  exit 0
fi

log "status=degraded failures=${FAILURES[*]}"
echo "$MASTER_MD_OUT"
exit 1
