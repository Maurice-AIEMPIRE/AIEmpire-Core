#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# AIEmpire-Core — Google Drive Backup & Sync
# ═══════════════════════════════════════════════════════════════
# Backs up critical files to Google Drive using rclone.
# Keeps code, state, outputs, and gold nuggets in sync.
#
# Setup (one-time):
#   1. Install rclone: curl https://rclone.org/install.sh | bash
#   2. Configure: rclone config (choose Google Drive)
#   3. Name remote: "gdrive"
#
# Usage:
#   ./gdrive_sync.sh                  # Full backup
#   ./gdrive_sync.sh --restore        # Restore from Drive
#   ./gdrive_sync.sh --status         # Show sync status
#
# Cron (daily at 2am):
#   0 2 * * * /opt/aiempire/cloud-deploy/scripts/gdrive_sync.sh
# ═══════════════════════════════════════════════════════════════

REMOTE="gdrive:AIEmpire-Core"
LOCAL_ROOT="${EMPIRE_ROOT:-/home/user/AIEmpire-Core}"
LOG_FILE="${LOCAL_ROOT}/cloud-deploy/_gdrive_sync.log"

# What to sync
SYNC_DIRS=(
    "workflow_system/state"
    "workflow_system/output"
    "gemini-mirror/state"
    "gemini-mirror/output"
    "gemini-mirror/memory"
    "antigravity/_tasks"
    "antigravity/_artifacts"
    "antigravity/_conversations"
    "antigravity/_walkthroughs"
    "knowledge-items"
    "gold-nuggets"
    "docs"
)

# Code directories (backup, not continuous sync)
CODE_DIRS=(
    "antigravity"
    "workflow_system"
    "gemini-mirror"
    "empire_api"
    "atomic_reactor"
    "x_lead_machine"
    "kimi_swarm"
    "brain_system"
    "cloud-deploy"
)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# ─── Check rclone ──────────────────────────────────────────
check_rclone() {
    if ! command -v rclone &>/dev/null; then
        echo "rclone not found. Installing..."
        curl -fsSL https://rclone.org/install.sh | bash
    fi

    # Check if gdrive remote is configured
    if ! rclone listremotes | grep -q "gdrive:"; then
        echo "Google Drive remote not configured."
        echo "Run: rclone config"
        echo "  1. Choose 'n' for new remote"
        echo "  2. Name: gdrive"
        echo "  3. Type: drive (Google Drive)"
        echo "  4. Follow OAuth flow"
        exit 1
    fi
}

# ─── Backup to Drive ──────────────────────────────────────
backup() {
    log "BACKUP: Starting sync to Google Drive..."

    # Sync state directories
    for dir in "${SYNC_DIRS[@]}"; do
        local_path="${LOCAL_ROOT}/${dir}"
        if [ -d "$local_path" ]; then
            rclone sync "$local_path" "${REMOTE}/sync/${dir}" \
                --quiet --transfers=4 --checkers=8 \
                2>/dev/null && \
                log "  OK: ${dir}" || \
                log "  SKIP: ${dir} (empty or error)"
        fi
    done

    # Backup code (copy, don't sync - preserve Drive history)
    for dir in "${CODE_DIRS[@]}"; do
        local_path="${LOCAL_ROOT}/${dir}"
        if [ -d "$local_path" ]; then
            rclone copy "$local_path" "${REMOTE}/code/${dir}" \
                --quiet --transfers=4 \
                --exclude="__pycache__/**" \
                --exclude="node_modules/**" \
                --exclude=".git/**" \
                --exclude="*.pyc" \
                2>/dev/null && \
                log "  OK: ${dir} (code)" || \
                log "  SKIP: ${dir}"
        fi
    done

    # Backup key files
    for file in CLAUDE.md .env.example requirements.txt docker-compose.prod.yml; do
        if [ -f "${LOCAL_ROOT}/${file}" ]; then
            rclone copy "${LOCAL_ROOT}/${file}" "${REMOTE}/config/" --quiet 2>/dev/null
        fi
    done

    log "BACKUP: Complete"
}

# ─── Restore from Drive ────────────────────────────────────
restore() {
    log "RESTORE: Starting restore from Google Drive..."

    for dir in "${SYNC_DIRS[@]}"; do
        local_path="${LOCAL_ROOT}/${dir}"
        mkdir -p "$local_path"
        rclone sync "${REMOTE}/sync/${dir}" "$local_path" \
            --quiet --transfers=4 \
            2>/dev/null && \
            log "  OK: ${dir}" || \
            log "  SKIP: ${dir} (not in Drive)"
    done

    log "RESTORE: Complete"
}

# ─── Status ─────────────────────────────────────────────────
show_status() {
    echo "═══════════════════════════════════════════════════════"
    echo "  Google Drive Sync Status"
    echo "═══════════════════════════════════════════════════════"
    echo "  Remote: $REMOTE"
    echo "  Local:  $LOCAL_ROOT"
    echo

    echo "  Remote directories:"
    rclone lsd "$REMOTE/" 2>/dev/null | while read -r line; do
        echo "    $line"
    done || echo "    (not accessible)"

    echo
    echo "  Remote size:"
    rclone size "$REMOTE/" 2>/dev/null || echo "    (not accessible)"

    echo
    echo "  Last sync:"
    if [ -f "$LOG_FILE" ]; then
        tail -5 "$LOG_FILE"
    else
        echo "    No sync history"
    fi
    echo "═══════════════════════════════════════════════════════"
}

# ─── Main ──────────────────────────────────────────────────
check_rclone

case "${1:-}" in
    --restore) restore ;;
    --status)  show_status ;;
    --help)
        echo "Usage: $0 [--restore|--status|--help]"
        echo "Default: backup to Google Drive"
        ;;
    *)         backup ;;
esac
