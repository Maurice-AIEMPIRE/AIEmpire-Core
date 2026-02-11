#!/bin/bash
# Auto-Commit Watch System - Maurice's AI Empire
# Watches for git changes and auto-commits when validated

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
AUTO_COMMIT_SCRIPT="$REPO_DIR/automation/scripts/auto_commit.py"
LOG_FILE="$REPO_DIR/00_SYSTEM/auto_commit_watch.log"

# Create log directory
mkdir -p "$REPO_DIR/00_SYSTEM"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if there are changes
has_changes() {
    cd "$REPO_DIR"
    # Check for staged or unstaged changes
    if git diff --quiet && git diff --cached --quiet; then
        return 1  # No changes
    else
        return 0  # Has changes
    fi
}

# Function to run auto-commit
run_auto_commit() {
    cd "$REPO_DIR"
    log "Running auto-commit..."

    if python3 "$AUTO_COMMIT_SCRIPT"; then
        log "✅ Auto-commit successful"
        return 0
    else
        log "❌ Auto-commit failed"
        return 1
    fi
}

# Main watch loop
log "🚀 Starting Auto-Commit Watch System"
log "📁 Watching: $REPO_DIR"
log "🔄 Check interval: 30 seconds"

while true; do
    if has_changes; then
        log "📝 Changes detected, running auto-commit..."
        if run_auto_commit; then
            log "✅ Changes committed successfully"
        else
            log "⚠️  Auto-commit failed, will retry in next cycle"
        fi
    fi

    # Wait 30 seconds before next check
    sleep 30
done