#!/bin/bash
# ══════════════════════════════════════════════════════════════
# BIDIRECTIONAL SYNC: Mac ↔ Google Cloud
# ══════════════════════════════════════════════════════════════
# Syncs your local AIEmpire-Core with Google Cloud Storage.
# Run this to keep Mac and Cloud in sync.
#
# Usage:
#   ./cloud/sync_local_cloud.sh up     → Mac → Cloud
#   ./cloud/sync_local_cloud.sh down   → Cloud → Mac
#   ./cloud/sync_local_cloud.sh both   → Bidirectional
#   ./cloud/sync_local_cloud.sh watch  → Auto-sync every 5 min
# ══════════════════════════════════════════════════════════════

PROJECT_ID="ai-empire-486415"
BUCKET="gs://${PROJECT_ID}-empire-data"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# Directories to sync
SYNC_DIRS=(
    "empire_data"
    "antigravity/_knowledge"
    "antigravity/_state"
    "products"
    "x_lead_machine"
    "BMA_ACADEMY"
)

# Exclude patterns
EXCLUDE="--exclude=__pycache__/ --exclude=.git/ --exclude=.venv/ --exclude=node_modules/ --exclude=*.pyc"

sync_up() {
    echo -e "${CYAN}→ Syncing Mac → Cloud${NC}"
    for dir in "${SYNC_DIRS[@]}"; do
        if [ -d "$LOCAL_DIR/$dir" ]; then
            echo "  $dir/ → $BUCKET/$dir/"
            gsutil -m rsync -r $EXCLUDE "$LOCAL_DIR/$dir/" "$BUCKET/$dir/" 2>/dev/null
        fi
    done
    # Also sync core Python files
    gsutil cp "$LOCAL_DIR/empire_boot.py" "$BUCKET/code/" 2>/dev/null
    gsutil cp "$LOCAL_DIR/empire_engine.py" "$BUCKET/code/" 2>/dev/null
    gsutil cp "$LOCAL_DIR/requirements.txt" "$BUCKET/code/" 2>/dev/null
    gsutil cp "$LOCAL_DIR/.env" "$BUCKET/config/.env" 2>/dev/null
    echo -e "${GREEN}✓ Upload complete${NC}"
}

sync_down() {
    echo -e "${CYAN}→ Syncing Cloud → Mac${NC}"
    for dir in "${SYNC_DIRS[@]}"; do
        mkdir -p "$LOCAL_DIR/$dir"
        echo "  $BUCKET/$dir/ → $dir/"
        gsutil -m rsync -r "$BUCKET/$dir/" "$LOCAL_DIR/$dir/" 2>/dev/null
    done
    echo -e "${GREEN}✓ Download complete${NC}"
}

sync_both() {
    sync_up
    echo ""
    sync_down
}

watch_sync() {
    echo -e "${CYAN}→ Auto-sync every 5 minutes (Ctrl+C to stop)${NC}"
    while true; do
        echo -e "\n[$(date '+%H:%M:%S')] Syncing..."
        sync_up
        sleep 300
    done
}

case "${1:-both}" in
    up)    sync_up ;;
    down)  sync_down ;;
    both)  sync_both ;;
    watch) watch_sync ;;
    *)     echo "Usage: $0 {up|down|both|watch}" ;;
esac
