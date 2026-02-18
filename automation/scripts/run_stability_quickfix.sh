#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-stabilize}" # check|stabilize
UID_NUM="$(id -u)"
LOG_DIR="$ROOT_DIR/automation/runs/stability"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/quickfix_$(date +%Y%m%d_%H%M%S).log"

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"
}

disable_failing_jobs() {
  launchctl list | awk '$2==78 && $3 ~ /^(com\.ai-empire|com\.empire|ai-empire|com\.aiempire|com\.openclaw)/ {print $3}' \
    | while IFS= read -r label; do
        [ -z "$label" ] && continue
        log "disable_job label=$label"
        launchctl disable "gui/${UID_NUM}/${label}" || true
        launchctl bootout "gui/${UID_NUM}/${label}" >/dev/null 2>&1 || true
      done
}

write_workspace_guards() {
  mkdir -p "$ROOT_DIR/.vscode"
  cat > "$ROOT_DIR/.vscode/settings.json" <<'JSON'
{
  "search.followSymlinks": false,
  "search.exclude": {
    "**/00_SYSTEM/chat_artifacts/**": true,
    "**/automation/runs/**": true,
    "**/content_factory/deliverables/backup_*/**": true,
    "**/content_factory/deliverables/exports/**": true
  },
  "files.watcherExclude": {
    "**/00_SYSTEM/chat_artifacts/**": true,
    "**/automation/runs/**": true,
    "**/content_factory/deliverables/backup_*/**": true,
    "**/content_factory/deliverables/exports/**": true
  },
  "files.exclude": {
    "**/00_SYSTEM/chat_artifacts/PULL_*/downloads_backup_tree": true,
    "**/00_SYSTEM/chat_artifacts/PULL_*/downloads_backup_raw": true
  },
  "python.analysis.exclude": [
    "**/00_SYSTEM/chat_artifacts/**",
    "**/automation/runs/**",
    "**/content_factory/deliverables/backup_*/**",
    "**/content_factory/deliverables/exports/**"
  ]
}
JSON

  touch "$ROOT_DIR/00_SYSTEM/chat_artifacts/.metadata_never_index"
  touch "$ROOT_DIR/automation/runs/.metadata_never_index"
  log "workspace_guard updated"
}

kill_spike_processes() {
  log "killing_scan_spikes"
  pkill -f "@vscode/ripgrep/bin/rg --files" || true
  pkill -f "ms-python.vscode-pylance" || true
}

print_snapshot() {
  log "uptime=$(uptime)"
  log "top_cpu_start"
  ps -axo pid,pcpu,pmem,command | sort -k2 -nr | head -n 15 | tee -a "$LOG_FILE"
  log "top_cpu_end"
}

log "mode=$MODE root=$ROOT_DIR"

case "$MODE" in
  check)
    print_snapshot
    ;;
  stabilize)
    disable_failing_jobs
    write_workspace_guards
    kill_spike_processes
    print_snapshot
    ;;
  *)
    echo "Usage: $0 [check|stabilize]" >&2
    exit 1
    ;;
esac

log "done log_file=$LOG_FILE"
