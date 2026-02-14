#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

SHORTS_SESSION="${SHORTS_SESSION_NAME:-ai_empire_shorts}"
OPS_SESSION="${OPS_SESSION_NAME:-ai_empire_ops}"

load_env() {
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

has_youtube_auth() {
  if [ -n "${YOUTUBE_ACCESS_TOKEN:-}" ]; then
    return 0
  fi
  if [ -n "${YOUTUBE_CLIENT_ID:-}" ] && [ -n "${YOUTUBE_CLIENT_SECRET:-}" ] && [ -n "${YOUTUBE_REFRESH_TOKEN:-}" ]; then
    return 0
  fi
  return 1
}

tmux_has_session() {
  local name="$1"
  tmux has-session -t "$name" 2>/dev/null
}

start_tmux_session() {
  local name="$1"
  local cmd="$2"
  if tmux_has_session "$name"; then
    echo "[full-autonomy] session exists: $name"
    return 0
  fi
  tmux new-session -d -s "$name" "$cmd"
  echo "[full-autonomy] session started: $name"
}

stop_tmux_session() {
  local name="$1"
  if tmux_has_session "$name"; then
    tmux kill-session -t "$name"
    echo "[full-autonomy] session stopped: $name"
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

show_status() {
  load_env

  echo "== Full Autonomy Status =="
  echo "cwd=$ROOT_DIR"
  echo "time=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo

  echo "-- Sessions --"
  tmux ls 2>/dev/null | rg -n "$SHORTS_SESSION|$OPS_SESSION" || echo "no managed sessions"
  echo

  echo "-- Live Keys --"
  print_key_status OPENAI_API_KEY
  print_key_status YOUTUBE_CLIENT_ID
  print_key_status YOUTUBE_CLIENT_SECRET
  print_key_status YOUTUBE_REFRESH_TOKEN
  print_key_status YOUTUBE_ACCESS_TOKEN
  print_key_status YOUTUBE_API_KEY
  print_key_status STRIPE_SECRET_KEY
  print_key_status STRIPE_WEBHOOK_SECRET
  print_key_status TELEGRAM_BOT_TOKEN
  print_key_status TELEGRAM_CHAT_ID
  echo

  echo "-- Queue Snapshot --"
  python3 - <<'PY'
import csv, re
from pathlib import Path
base=Path('content_factory/deliverables/shorts_revenue')
pat=re.compile(r'^\d{8}_\d{6}$')
runs=sorted([p for p in base.iterdir() if p.is_dir() and pat.match(p.name)]) if base.exists() else []
if not runs:
    print('no runs')
    raise SystemExit
latest=runs[-1]
q=latest/'youtube_publish_queue.csv'
print('latest_run', latest.name)
if not q.exists():
    print('no queue file')
    raise SystemExit
rows=list(csv.DictReader(q.open('r', encoding='utf-8', newline='')))
status={}
for r in rows:
    s=(r.get('status') or r.get('upload_status') or '').strip().lower() or 'unknown'
    status[s]=status.get(s,0)+1
print('queue_file', q)
print('status_counts', status)
PY
}

post_now() {
  load_env
  echo "[full-autonomy] immediate publish attempt: shorts_revenue"
  automation/scripts/auto_publish_youtube_queue.sh shorts_revenue || true
  echo "[full-autonomy] immediate publish attempt: youtube_shorts"
  automation/scripts/auto_publish_youtube_queue.sh youtube_shorts || true
}

start_all() {
  load_env

  if ! command -v tmux >/dev/null 2>&1; then
    echo "[full-autonomy] ERROR: tmux not installed"
    exit 1
  fi

  local hours="${1:-24}"
  local interval="${2:-30}"
  local shorts_log="$ROOT_DIR/automation/runs/daemon/full_autonomy_shorts_$(date +%Y%m%d_%H%M%S).log"
  local ops_log="$ROOT_DIR/automation/runs/daemon/full_autonomy_ops_$(date +%Y%m%d_%H%M%S).log"
  mkdir -p "$ROOT_DIR/automation/runs/daemon"

  local publish_flag="${AUTO_PUBLISH_YOUTUBE:-1}"
  if has_youtube_auth; then
    echo "[full-autonomy] YouTube auth=ready"
  else
    echo "[full-autonomy] YouTube auth=missing -> publish attempts will be skipped without queue damage"
    publish_flag="0"
  fi

  local shorts_cmd="cd '$ROOT_DIR' && EXECUTE_MODE=${EXECUTE_MODE:-1} VIDEO_PROVIDER=${VIDEO_PROVIDER:-sora} SORA_VIDEO_ENABLED=${SORA_VIDEO_ENABLED:-1} OLLAMA_API_KEY=${OLLAMA_API_KEY:-local} OLLAMA_PRIMARY_MODEL=${OLLAMA_PRIMARY_MODEL:-minimax-m2.5:cloud} AUTO_PUBLISH_YOUTUBE=$publish_flag AUTO_PUBLISH_MODE=${AUTO_PUBLISH_MODE:-public} AUTO_PUBLISH_MAX_PER_RUN=${AUTO_PUBLISH_MAX_PER_RUN:-1} AUTO_PUBLISH_MAX_PER_DAY=${AUTO_PUBLISH_MAX_PER_DAY:-6} AUTO_PUBLISH_MIN_SPACING_MIN=${AUTO_PUBLISH_MIN_SPACING_MIN:-120} TELEGRAM_INCOME_STREAM=${TELEGRAM_INCOME_STREAM:-1} AUTO_COMMIT_ENABLED=${AUTO_COMMIT_ENABLED:-1} AUTO_COMMIT_PUSH=${AUTO_COMMIT_PUSH:-0} SAFETY_GUARD=${SAFETY_GUARD:-1} X_SCOUT_ENABLED=${X_SCOUT_ENABLED:-1} ATLAS_SNAPSHOT_ENABLED=${ATLAS_SNAPSHOT_ENABLED:-1} automation/scripts/run_shorts_revenue_autopilot.sh '$hours' '$interval' | tee -a '$shorts_log'"
  local ops_cmd="cd '$ROOT_DIR' && automation/scripts/run_ops_maintenance_loop.sh | tee -a '$ops_log'"

  start_tmux_session "$SHORTS_SESSION" "$shorts_cmd"
  start_tmux_session "$OPS_SESSION" "$ops_cmd"

  if [ "${AUTO_POST_NOW_ON_START:-1}" = "1" ]; then
    post_now
  fi

  echo "[full-autonomy] running"
  echo "[full-autonomy] attach: tmux attach -t $SHORTS_SESSION"
  echo "[full-autonomy] ops:    tmux attach -t $OPS_SESSION"
  echo "[full-autonomy] logs:   $shorts_log"
}

stop_all() {
  stop_tmux_session "$SHORTS_SESSION"
  stop_tmux_session "$OPS_SESSION"
}

restart_all() {
  local hours="${1:-24}"
  local interval="${2:-30}"
  stop_all
  start_all "$hours" "$interval"
}

usage() {
  cat <<USAGE
Usage: automation/scripts/full_autonomy.sh <start|stop|restart|status|post-now> [hours] [interval_min]

Commands:
  start [hours] [interval_min]   Start managed autonomy sessions (default 24h, 30min)
  stop                           Stop managed autonomy sessions
  restart [hours] [interval_min] Restart managed autonomy sessions
  status                         Show sessions, key readiness, queue snapshot
  post-now                       Trigger immediate publish attempt for both workflows
USAGE
}

CMD="${1:-status}"
case "$CMD" in
  start)
    start_all "${2:-24}" "${3:-30}"
    ;;
  stop)
    stop_all
    ;;
  restart)
    restart_all "${2:-24}" "${3:-30}"
    ;;
  status)
    show_status
    ;;
  post-now)
    post_now
    ;;
  *)
    usage
    exit 1
    ;;
esac
