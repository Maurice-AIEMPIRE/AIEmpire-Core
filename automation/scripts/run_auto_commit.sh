#!/bin/bash
# Auto-commit wrapper for Maurice's AI Empire

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$REPO_DIR/automation/scripts/auto_commit.py"

cd "$REPO_DIR"

# Run auto-commit
python3 "$SCRIPT"

# Log execution
mkdir -p "$REPO_DIR/00_SYSTEM"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Auto-commit executed" >> "$REPO_DIR/00_SYSTEM/auto_commit.log"
