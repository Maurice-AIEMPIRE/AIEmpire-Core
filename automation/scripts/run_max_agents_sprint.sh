#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT_DIR"

RUN_DIR="$ROOT_DIR/automation/runs/max_agents_sprint"
STATE_FILE="$RUN_DIR/state.env"

DEFAULT_HOURS=24
DEFAULT_INTERVAL_MIN=30
DEFAULT_WORKERS=10
DEFAULT_PUBLISH_POLICY="internal-only"
DEFAULT_SHORTS_SESSION="max_agents_sprint_shorts"
DEFAULT_OPS_SESSION="max_agents_sprint_ops"
DEFAULT_LEGION_SESSION="max_agents_sprint_legion"

ensure_run_dir() {
  mkdir -p "$RUN_DIR"
}

load_env_files() {
  set -a
  if [ -f "$ROOT_DIR/ai-vault/empire.env" ]; then
    # shellcheck disable=SC1090
    source "$ROOT_DIR/ai-vault/empire.env"
  fi
  if [ -f "$HOME/.openclaw/.env" ]; then
    # shellcheck disable=SC1090
    source "$HOME/.openclaw/.env"
  fi
  set +a
}

tmux_has_session() {
  local name="$1"
  tmux has-session -t "$name" 2>/dev/null
}

start_tmux_session() {
  local name="$1"
  local cmd="$2"
  if tmux_has_session "$name"; then
    echo "[max-sprint] session exists: $name"
    return 0
  fi
  tmux new-session -d -s "$name" "$cmd"
  echo "[max-sprint] session started: $name"
}

stop_tmux_session() {
  local name="$1"
  if tmux_has_session "$name"; then
    tmux kill-session -t "$name"
    echo "[max-sprint] session stopped: $name"
  else
    echo "[max-sprint] session not running: $name"
  fi
}

ensure_tmux() {
  if ! command -v tmux >/dev/null 2>&1; then
    echo "ERROR: tmux not installed." >&2
    exit 1
  fi
}

list_conflicting_sessions() {
  local known_conflicts=(
    "ai_empire_shorts"
    "ai_empire_ops"
  )
  local found=()
  local session
  for session in "${known_conflicts[@]}"; do
    if tmux_has_session "$session"; then
      found+=("$session")
    fi
  done
  if [ "${#found[@]}" -gt 0 ]; then
    printf '%s\n' "${found[@]}"
  fi
}

check_conflicting_sessions() {
  local force_start="$1"
  local conflicts
  conflicts="$(list_conflicting_sessions || true)"
  if [ -n "$conflicts" ] && [ "$force_start" != "1" ]; then
    echo "ERROR: conflicting tmux sessions detected:"
    echo "$conflicts" | sed 's/^/- /'
    echo "Use --force if you intentionally want to run this sprint in parallel."
    exit 3
  fi
}

print_key_status() {
  local key="$1"
  local value="${!key:-}"
  if [ -n "$value" ]; then
    echo "$key=SET"
  else
    echo "$key=MISSING"
  fi
}

state_set() {
  local key="$1"
  local value="${2:-}"
  printf '%s=%q\n' "$key" "$value" >> "$STATE_FILE"
}

write_state_file() {
  : > "$STATE_FILE"
  state_set SPRINT_ID "$SPRINT_ID"
  state_set SPRINT_STATUS "$SPRINT_STATUS"
  state_set STARTED_AT "$STARTED_AT"
  state_set PAUSED_AT "$PAUSED_AT"
  state_set FINISHED_AT "$FINISHED_AT"
  state_set HOURS "$HOURS"
  state_set INTERVAL_MIN "$INTERVAL_MIN"
  state_set WORKERS "$WORKERS"
  state_set PUBLISH_POLICY "$PUBLISH_POLICY"
  state_set AUTO_PUBLISH_YOUTUBE "$AUTO_PUBLISH_YOUTUBE"
  state_set AUTO_PUBLISH_MODE "$AUTO_PUBLISH_MODE"
  state_set AUTO_PUBLISH_DRY_RUN "$AUTO_PUBLISH_DRY_RUN"
  state_set SHORTS_SESSION "$SHORTS_SESSION"
  state_set OPS_SESSION "$OPS_SESSION"
  state_set LEGION_SESSION "$LEGION_SESSION"
  state_set SHORTS_LOG "$SHORTS_LOG"
  state_set OPS_LOG "$OPS_LOG"
  state_set LEGION_LOG "$LEGION_LOG"
  state_set WORKTREE_BEFORE "$WORKTREE_BEFORE"
  state_set WORKTREE_AFTER "$WORKTREE_AFTER"
  state_set WORKTREE_PRUNE_LOG "$WORKTREE_PRUNE_LOG"
  state_set LAST_VALIDATION_LOG "$LAST_VALIDATION_LOG"
}

load_state_file() {
  if [ ! -f "$STATE_FILE" ]; then
    echo "No sprint state found: $STATE_FILE"
    return 1
  fi
  # shellcheck disable=SC1090
  source "$STATE_FILE"
  return 0
}

resolve_publish_policy() {
  case "$PUBLISH_POLICY" in
    internal-only)
      AUTO_PUBLISH_YOUTUBE=1
      AUTO_PUBLISH_MODE="private"
      AUTO_PUBLISH_DRY_RUN=1
      ;;
    public)
      AUTO_PUBLISH_YOUTUBE=1
      AUTO_PUBLISH_MODE="public"
      AUTO_PUBLISH_DRY_RUN=0
      ;;
    dry-run)
      AUTO_PUBLISH_YOUTUBE=1
      AUTO_PUBLISH_MODE="private"
      AUTO_PUBLISH_DRY_RUN=1
      ;;
    *)
      echo "ERROR: unsupported --publish value: $PUBLISH_POLICY" >&2
      echo "Allowed: internal-only | public | dry-run" >&2
      exit 2
      ;;
  esac
}

cleanup_stale_worktrees() {
  local ts="$1"
  WORKTREE_BEFORE="$RUN_DIR/worktrees_before_${ts}.txt"
  WORKTREE_AFTER="$RUN_DIR/worktrees_after_${ts}.txt"
  WORKTREE_PRUNE_LOG="$RUN_DIR/worktree_prune_${ts}.log"
  {
    echo "[worktree-prune] async-start ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    git worktree list > "$WORKTREE_BEFORE" 2>/dev/null || true
    git worktree prune --verbose >> "$WORKTREE_PRUNE_LOG" 2>&1 || true
    git worktree list > "$WORKTREE_AFTER" 2>/dev/null || true
    echo "[worktree-prune] async-finish ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } >> "$WORKTREE_PRUNE_LOG" 2>&1 &
}

run_internal_publish_validation() {
  local ts="$1"
  local out_file="$RUN_DIR/publish_validation_${ts}.log"
  LAST_VALIDATION_LOG="$out_file"
  (
    cd "$ROOT_DIR"
    echo "[publish-validation] async-start ts=$(date -u +%Y-%m-%dT%H:%M:%SZ) policy=$PUBLISH_POLICY"
    set +e
    AUTO_PUBLISH_DRY_RUN=1 AUTO_PUBLISH_MODE=private \
      python3 -m automation.youtube_publish \
      --workflow shorts_revenue \
      --mode private \
      --max-posts 1 \
      --max-posts-per-day 6 \
      --min-spacing-min 120 \
      --dry-run
    rc_short=$?
    AUTO_PUBLISH_DRY_RUN=1 AUTO_PUBLISH_MODE=private \
      python3 -m automation.youtube_publish \
      --workflow youtube_shorts \
      --mode private \
      --max-posts 1 \
      --max-posts-per-day 6 \
      --min-spacing-min 120 \
      --dry-run
    rc_yt=$?
    set -e
    echo "[publish-validation] async-finish ts=$(date -u +%Y-%m-%dT%H:%M:%SZ) shorts_revenue=$rc_short youtube_shorts=$rc_yt"
  ) > "$out_file" 2>&1 &
}

show_publish_summaries() {
  python3 - <<'PY'
import json
from pathlib import Path
from typing import Optional

def latest_summary(base: Path) -> Optional[Path]:
    if not base.exists():
        return None
    runs = sorted([p for p in base.iterdir() if p.is_dir() and p.name[:8].isdigit()], reverse=True)
    for run in runs:
        p = run / "publish_run_summary.json"
        if p.exists():
            return p
    return None

targets = {
    "shorts_revenue": Path("content_factory/deliverables/shorts_revenue"),
    "youtube_shorts": Path("content_factory/deliverables/youtube_shorts"),
}
for workflow, base in targets.items():
    p = latest_summary(base)
    if not p:
        print(f"{workflow}: summary=missing")
        continue
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"{workflow}: summary={p} parse_error={exc}")
        continue
    auth_ready = data.get("auth_ready")
    dry_run = data.get("dry_run")
    published_count = data.get("published_count")
    blocked_reason = data.get("blocked_reason")
    mode = data.get("mode")
    effective_mode = data.get("effective_mode")
    print(
        f"{workflow}: summary={p} auth_ready={auth_ready} dry_run={dry_run} "
        f"published_count={published_count} mode={mode}->{effective_mode} "
        f"blocked_reason={blocked_reason or 'none'}"
    )
PY
}

print_auth_hygiene_status() {
  local conflict=0
  if [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ] && [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    conflict=1
    echo "auth_conflict=1 (ANTHROPIC_AUTH_TOKEN + ANTHROPIC_API_KEY are both set)"
  else
    echo "auth_conflict=0"
  fi
  if [ -n "${OPENAI_API_KEY:-}" ]; then
    echo "openai_api_key=SET"
  else
    echo "openai_api_key=MISSING"
  fi
  return "$conflict"
}

build_legion_prompt() {
  cat <<'EOF'
24h hard sprint for code and ops blockers only.
Objective:
- Stabilize automation runtime.
- Close publish pipeline blockers.
- Improve reliability and deterministic execution.
Output format:
- P1/P2/P3 actions
- blockers
- risks
- next 3 executable commands
EOF
}

start_sessions() {
  local ts="$1"
  local legion_prompt
  local legion_prompt_q
  legion_prompt="$(build_legion_prompt)"
  printf -v legion_prompt_q '%q' "$legion_prompt"

  local shorts_cmd="cd '$ROOT_DIR' && MISSION_MAX_WORKERS='$WORKERS' EXECUTE_MODE=1 SAFETY_GUARD=1 SAFETY_COOLDOWN_MIN=20 AUTOPILOT_NICE=10 DEGRADE_MAINTENANCE_ON_BLOCK=1 AUTO_PUBLISH_YOUTUBE='$AUTO_PUBLISH_YOUTUBE' AUTO_PUBLISH_MODE='$AUTO_PUBLISH_MODE' AUTO_PUBLISH_DRY_RUN='$AUTO_PUBLISH_DRY_RUN' AUTO_COMMIT_ENABLED=1 AUTO_COMMIT_PUSH=0 X_SCOUT_ENABLED=1 automation/scripts/run_shorts_revenue_autopilot.sh '$HOURS' '$INTERVAL_MIN' | tee -a '$SHORTS_LOG'"
  local ops_cmd="cd '$ROOT_DIR' && OPS_LOOP_SLEEP_SEC=300 CHAT_EXPORT_INTERVAL_SEC=21600 INCOME_INTERVAL_SEC=3600 STRIPE_SYNC_INTERVAL_SEC=7200 HANDOFF_INTERVAL_SEC=7200 automation/scripts/run_ops_maintenance_loop.sh | tee -a '$OPS_LOG'"
  local legion_cmd="cd '$ROOT_DIR' && MISSION_MAX_WORKERS='$WORKERS' automation/scripts/run_legion_50.sh --execute --tier premium --task-type strategy --agents-per-wave '$WORKERS' --max-output-tokens 320 --prompt $legion_prompt_q | tee -a '$LEGION_LOG'"

  start_tmux_session "$SHORTS_SESSION" "$shorts_cmd"
  start_tmux_session "$OPS_SESSION" "$ops_cmd"
  start_tmux_session "$LEGION_SESSION" "$legion_cmd"

  run_internal_publish_validation "$ts"
}

show_status() {
  load_env_files
  if ! load_state_file; then
    echo "Use: automation/scripts/run_max_agents_sprint.sh start --hours 24 --workers 10 --publish internal-only"
    return 0
  fi

  echo "== Max Agents Sprint Status =="
  echo "repo=$ROOT_DIR"
  echo "state=$STATE_FILE"
  echo "time=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "-- Sprint --"
  echo "sprint_id=$SPRINT_ID"
  echo "sprint_status=$SPRINT_STATUS"
  echo "started_at=$STARTED_AT"
  echo "paused_at=${PAUSED_AT:-n/a}"
  echo "finished_at=${FINISHED_AT:-n/a}"
  echo "hours=$HOURS"
  echo "interval_min=$INTERVAL_MIN"
  echo "workers=$WORKERS"
  echo "publish_policy=$PUBLISH_POLICY"
  echo "publish_mode=$AUTO_PUBLISH_MODE"
  echo "publish_dry_run=$AUTO_PUBLISH_DRY_RUN"
  echo
  echo "-- Sessions --"
  for s in "$SHORTS_SESSION" "$OPS_SESSION" "$LEGION_SESSION"; do
    if tmux_has_session "$s"; then
      echo "$s=running"
    else
      echo "$s=stopped"
    fi
  done
  echo
  echo "-- Key Status --"
  print_key_status MISSION_MAX_WORKERS
  print_key_status YOUTUBE_CLIENT_ID
  print_key_status YOUTUBE_CLIENT_SECRET
  print_key_status YOUTUBE_REFRESH_TOKEN
  print_key_status YOUTUBE_ACCESS_TOKEN
  print_key_status OPENAI_API_KEY
  print_key_status ANTHROPIC_API_KEY
  print_key_status ANTHROPIC_AUTH_TOKEN
  print_auth_hygiene_status || true
  echo
  echo "-- Publish Summaries --"
  show_publish_summaries
  echo
  echo "-- Logs --"
  echo "shorts_log=$SHORTS_LOG"
  echo "ops_log=$OPS_LOG"
  echo "legion_log=$LEGION_LOG"
  echo "last_validation_log=${LAST_VALIDATION_LOG:-n/a}"
  echo "worktree_before=$WORKTREE_BEFORE"
  echo "worktree_after=$WORKTREE_AFTER"
  echo "worktree_prune_log=$WORKTREE_PRUNE_LOG"
}

cmd_start() {
  HOURS="$DEFAULT_HOURS"
  INTERVAL_MIN="$DEFAULT_INTERVAL_MIN"
  WORKERS="$DEFAULT_WORKERS"
  PUBLISH_POLICY="$DEFAULT_PUBLISH_POLICY"
  FORCE_START=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --hours)
        HOURS="$2"
        shift 2
        ;;
      --workers)
        WORKERS="$2"
        shift 2
        ;;
      --publish)
        PUBLISH_POLICY="$2"
        shift 2
        ;;
      --interval-min)
        INTERVAL_MIN="$2"
        shift 2
        ;;
      --force)
        FORCE_START=1
        shift
        ;;
      *)
        echo "Unknown option for start: $1" >&2
        exit 2
        ;;
    esac
  done

  if ! [[ "$HOURS" =~ ^[0-9]+$ ]] || [ "$HOURS" -lt 1 ]; then
    echo "ERROR: --hours must be integer >= 1" >&2
    exit 2
  fi
  if ! [[ "$WORKERS" =~ ^[0-9]+$ ]] || [ "$WORKERS" -lt 1 ]; then
    echo "ERROR: --workers must be integer >= 1" >&2
    exit 2
  fi
  if ! [[ "$INTERVAL_MIN" =~ ^[0-9]+$ ]] || [ "$INTERVAL_MIN" -lt 1 ]; then
    echo "ERROR: --interval-min must be integer >= 1" >&2
    exit 2
  fi

  ensure_run_dir
  load_env_files
  ensure_tmux
  check_conflicting_sessions "$FORCE_START"
  resolve_publish_policy

  local ts
  ts="$(date +%Y%m%d_%H%M%S)"
  SPRINT_ID="max_agents_${ts}"
  SPRINT_STATUS="running"
  STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  PAUSED_AT=""
  FINISHED_AT=""
  SHORTS_SESSION="$DEFAULT_SHORTS_SESSION"
  OPS_SESSION="$DEFAULT_OPS_SESSION"
  LEGION_SESSION="$DEFAULT_LEGION_SESSION"
  SHORTS_LOG="$RUN_DIR/shorts_${ts}.log"
  OPS_LOG="$RUN_DIR/ops_${ts}.log"
  LEGION_LOG="$RUN_DIR/legion_${ts}.log"
  LAST_VALIDATION_LOG=""

  cleanup_stale_worktrees "$ts"
  start_sessions "$ts"
  write_state_file

  echo "[max-sprint] started sprint_id=$SPRINT_ID"
  echo "[max-sprint] sprint_board=00_SYSTEM/sprints/2026-02-14_max_agents_sprint.md"
  echo "[max-sprint] attach_shorts=tmux attach -t $SHORTS_SESSION"
  echo "[max-sprint] attach_ops=tmux attach -t $OPS_SESSION"
  echo "[max-sprint] attach_legion=tmux attach -t $LEGION_SESSION"
  show_status
}

cmd_pause() {
  if ! load_state_file; then
    exit 1
  fi
  ensure_tmux
  stop_tmux_session "$SHORTS_SESSION"
  stop_tmux_session "$OPS_SESSION"
  stop_tmux_session "$LEGION_SESSION"
  SPRINT_STATUS="paused"
  PAUSED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  write_state_file
  echo "[max-sprint] paused"
}

cmd_resume() {
  local force_start=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --force)
        force_start=1
        shift
        ;;
      *)
        echo "Unknown option for resume: $1" >&2
        exit 2
        ;;
    esac
  done

  if ! load_state_file; then
    exit 1
  fi
  ensure_run_dir
  load_env_files
  ensure_tmux
  check_conflicting_sessions "$force_start"
  resolve_publish_policy

  local ts
  ts="$(date +%Y%m%d_%H%M%S)"
  SHORTS_LOG="$RUN_DIR/shorts_${ts}.log"
  OPS_LOG="$RUN_DIR/ops_${ts}.log"
  LEGION_LOG="$RUN_DIR/legion_${ts}.log"
  LAST_VALIDATION_LOG=""

  start_sessions "$ts"

  SPRINT_STATUS="running"
  PAUSED_AT=""
  write_state_file
  echo "[max-sprint] resumed sprint_id=$SPRINT_ID"
  show_status
}

cmd_finish() {
  if ! load_state_file; then
    exit 1
  fi
  ensure_tmux
  stop_tmux_session "$SHORTS_SESSION"
  stop_tmux_session "$OPS_SESSION"
  stop_tmux_session "$LEGION_SESSION"

  local ts
  ts="$(date +%Y%m%d_%H%M%S)"
  run_internal_publish_validation "$ts"
  python3 automation/scripts/write_thread_handoff.py >/dev/null 2>&1 || true

  SPRINT_STATUS="finished"
  FINISHED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  write_state_file

  local report="$RUN_DIR/finish_report_${ts}.md"
  {
    echo "# Max Agents Sprint Finish Report"
    echo
    echo "- sprint_id: $SPRINT_ID"
    echo "- started_at: $STARTED_AT"
    echo "- finished_at: $FINISHED_AT"
    echo "- workers: $WORKERS"
    echo "- publish_policy: $PUBLISH_POLICY"
    echo "- publish_mode: $AUTO_PUBLISH_MODE"
    echo "- publish_dry_run: $AUTO_PUBLISH_DRY_RUN"
    echo "- worktree_before: $WORKTREE_BEFORE"
    echo "- worktree_after: $WORKTREE_AFTER"
    echo "- worktree_prune_log: $WORKTREE_PRUNE_LOG"
    echo "- last_validation_log: $LAST_VALIDATION_LOG"
    echo
    echo "## Latest Publish Summaries"
    show_publish_summaries
  } > "$report"

  echo "[max-sprint] finished report=$report"
  show_status
}

usage() {
  cat <<'USAGE'
Usage:
  automation/scripts/run_max_agents_sprint.sh start --hours 24 --workers 10 --publish internal-only
  automation/scripts/run_max_agents_sprint.sh status
  automation/scripts/run_max_agents_sprint.sh pause
  automation/scripts/run_max_agents_sprint.sh resume
  automation/scripts/run_max_agents_sprint.sh finish

Commands:
  start   Start 24h max-agents sprint orchestration.
          Options:
            --hours <int>          default: 24
            --workers <int>        default: 10
            --publish <policy>     internal-only | public | dry-run (default: internal-only)
            --interval-min <int>   default: 30
            --force                allow parallel run despite known conflicting sessions
  status  Show sprint state, sessions, key status, and latest publish summaries.
  pause   Stop sprint-managed tmux sessions (shorts/ops/legion) and mark sprint paused.
  resume  Restart sprint-managed sessions from saved state.
          Options:
            --force                allow parallel run despite known conflicting sessions
  finish  Stop sessions, run internal publish validation + thread handoff, write finish report.
USAGE
}

main() {
  local cmd="${1:-status}"
  shift || true
  case "$cmd" in
    start)
      cmd_start "$@"
      ;;
    status)
      show_status
      ;;
    pause)
      cmd_pause
      ;;
    resume)
      cmd_resume "$@"
      ;;
    finish)
      cmd_finish
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      echo "Unknown command: $cmd" >&2
      usage
      exit 2
      ;;
  esac
}

main "$@"
