#!/usr/bin/env bash

set -u

export PATH="/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${AI_EMPIRE_ROOT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
OUT_ROOT="$ROOT_DIR/ai-vault/backups/openclaw"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="$OUT_ROOT/$TS"
RETENTION="${OPENCLAW_SNAPSHOT_RETENTION:-72}"

mkdir -p "$DEST"

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -f "$src" ]; then
    cp "$src" "$dst" 2>/dev/null || true
  fi
}

copy_if_exists "$HOME/.openclaw/openclaw.json" "$DEST/openclaw.json"
copy_if_exists "$HOME/.openclaw/agents/main/agent/models.json" "$DEST/agent_models.json"
copy_if_exists "$HOME/.openclaw/agents/main/agent/auth-profiles.json" "$DEST/agent_auth_profiles.json"
copy_if_exists "$HOME/.openclaw/cron/jobs.json" "$DEST/cron_jobs_store.json"

openclaw --no-color status --json >"$DEST/status.raw.txt" 2>&1 || true
sed -n '/^{/,$p' "$DEST/status.raw.txt" >"$DEST/status.json" || true

openclaw --no-color cron list --json >"$DEST/cron_list.raw.txt" 2>&1 || true
sed -n '/^\[/,$p' "$DEST/cron_list.raw.txt" >"$DEST/cron_list.json" || true

openclaw --no-color security audit >"$DEST/security_audit.txt" 2>&1 || true
openclaw --no-color config get agents.defaults.model.primary >"$DEST/config_primary.txt" 2>&1 || true
openclaw --no-color config get agents.defaults.model.fallbacks --json >"$DEST/config_fallbacks.txt" 2>&1 || true

all_snapshots=()
while IFS= read -r snapshot_dir; do
  all_snapshots+=("$snapshot_dir")
done < <(find "$OUT_ROOT" -mindepth 1 -maxdepth 1 -type d | sort)
count="${#all_snapshots[@]}"
if [ "$count" -gt "$RETENTION" ]; then
  remove_count=$((count - RETENTION))
  for ((i=0; i<remove_count; i++)); do
    rm -rf "${all_snapshots[$i]}"
  done
fi

printf '%s\n' "$DEST"
