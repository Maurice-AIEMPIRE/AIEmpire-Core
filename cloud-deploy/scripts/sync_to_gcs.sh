#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# AIEmpire-Core — State Sync to Google Cloud Storage
# ═══════════════════════════════════════════════════════════════
# Synchronizes local state with GCS for parallel operation.
# Runs as cron job or one-shot.
#
# Usage:
#   ./sync_to_gcs.sh                 # Full sync (up + down)
#   ./sync_to_gcs.sh --upload        # Upload only
#   ./sync_to_gcs.sh --download      # Download only
#   ./sync_to_gcs.sh --status        # Show sync status
#
# Cron (every 15 min):
#   */15 * * * * /opt/aiempire/cloud-deploy/scripts/sync_to_gcs.sh >> /var/log/empire-sync.log 2>&1
# ═══════════════════════════════════════════════════════════════

PROJECT_ID="${GCP_PROJECT_ID:-aiempire-core}"
BUCKET="gs://${PROJECT_ID}-state"
LOCAL_ROOT="${EMPIRE_ROOT:-/home/user/AIEmpire-Core}"
SYNC_LOG="${LOCAL_ROOT}/cloud-deploy/_sync.log"

# Directories to sync
SYNC_DIRS=(
    "workflow_system/state"
    "workflow_system/output"
    "gemini-mirror/state"
    "gemini-mirror/output"
    "gemini-mirror/memory"
    "antigravity/_tasks"
    "antigravity/_artifacts"
    "antigravity/_conversations"
    "antigravity/_notifications"
    "antigravity/_walkthroughs"
    "knowledge-items"
)

# Files to sync
SYNC_FILES=(
    "workflow_system/state/current_state.json"
    "workflow_system/state/cowork_state.json"
    "workflow_system/state/pattern_library.json"
    "gemini-mirror/state/mirror_state.json"
    "gemini-mirror/state/sync_state.json"
    "gemini-mirror/state/vision_state.json"
)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$SYNC_LOG"; }

# ─── Upload to GCS ─────────────────────────────────────────
upload() {
    log "UPLOAD: Starting sync to GCS..."
    local count=0

    for dir in "${SYNC_DIRS[@]}"; do
        local_path="${LOCAL_ROOT}/${dir}"
        if [ -d "$local_path" ]; then
            gsutil -m rsync -r -d "$local_path" "${BUCKET}/${dir}/" 2>/dev/null && \
                count=$((count + 1)) || true
        fi
    done

    for file in "${SYNC_FILES[@]}"; do
        local_path="${LOCAL_ROOT}/${file}"
        if [ -f "$local_path" ]; then
            gsutil cp "$local_path" "${BUCKET}/${file}" 2>/dev/null && \
                count=$((count + 1)) || true
        fi
    done

    log "UPLOAD: Synced $count items to ${BUCKET}"
}

# ─── Download from GCS ─────────────────────────────────────
download() {
    log "DOWNLOAD: Starting sync from GCS..."
    local count=0

    for dir in "${SYNC_DIRS[@]}"; do
        local_path="${LOCAL_ROOT}/${dir}"
        mkdir -p "$local_path"
        gsutil -m rsync -r "${BUCKET}/${dir}/" "$local_path" 2>/dev/null && \
            count=$((count + 1)) || true
    done

    log "DOWNLOAD: Synced $count items from ${BUCKET}"
}

# ─── Conflict Resolution ───────────────────────────────────
resolve_conflicts() {
    # Simple strategy: newest wins
    # For state files, GCS version takes precedence (cloud is source of truth)
    # For output files, merge both (keep all)
    log "CONFLICT: Using newest-wins strategy (GCS = source of truth for state)"
}

# ─── Status ─────────────────────────────────────────────────
show_status() {
    echo "═══════════════════════════════════════════════════════"
    echo "  GCS Sync Status"
    echo "═══════════════════════════════════════════════════════"
    echo "  Bucket: $BUCKET"
    echo "  Local:  $LOCAL_ROOT"
    echo

    echo "  Remote objects:"
    gsutil du -s "$BUCKET" 2>/dev/null || echo "  (bucket not accessible)"

    echo
    echo "  Last sync:"
    if [ -f "$SYNC_LOG" ]; then
        tail -3 "$SYNC_LOG"
    else
        echo "  No sync history"
    fi

    echo
    echo "  Sync directories:"
    for dir in "${SYNC_DIRS[@]}"; do
        local_exists="LOCAL"
        [ ! -d "${LOCAL_ROOT}/${dir}" ] && local_exists="-----"
        remote_count=$(gsutil ls "${BUCKET}/${dir}/" 2>/dev/null | wc -l || echo 0)
        printf "    %-40s %s | remote: %s files\n" "$dir" "$local_exists" "$remote_count"
    done
    echo "═══════════════════════════════════════════════════════"
}

# ─── Main ──────────────────────────────────────────────────
case "${1:-}" in
    --upload)   upload ;;
    --download) download ;;
    --status)   show_status ;;
    --help)
        echo "Usage: $0 [--upload|--download|--status|--help]"
        echo "Default: bidirectional sync (download then upload)"
        ;;
    *)
        # Bidirectional: download first (cloud = truth), then upload local changes
        download
        upload
        log "SYNC: Bidirectional sync complete"
        ;;
esac
