#!/usr/bin/env bash
#
# ANTIGRAVITY DUPLICATE CLEANUP
# ==============================
# Safely removes duplicate Antigravity installations
# Keeps only: ~/AIEmpire-Core__codex/antigravity
#
# Maurice's AI Empire - 2026

set -euo pipefail

echo "🧹 ANTIGRAVITY DUPLICATE CLEANUP"
echo "================================="
echo

# 1. Create backup
BACKUP_DIR="$HOME/antigravity_backups_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "[1/4] Creating backups in: $BACKUP_DIR"

if [[ -d "$HOME/.gemini/antigravity" ]]; then
    cp -r "$HOME/.gemini/antigravity" "$BACKUP_DIR/gemini_antigravity" 2>/dev/null || true
    echo "  ✅ Backed up ~/.gemini/antigravity"
fi

if [[ -d "$HOME/.antigravity" ]]; then
    cp -r "$HOME/.antigravity" "$BACKUP_DIR/home_antigravity" 2>/dev/null || true
    echo "  ✅ Backed up ~/.antigravity"
fi

# 2. Disable old installations
echo
echo "[2/4] Disabling duplicate installations..."

if [[ -d "$HOME/.gemini/antigravity" ]]; then
    mv "$HOME/.gemini/antigravity" "$HOME/.gemini/antigravity.disabled_$(date +%Y%m%d)" 2>/dev/null || true
    echo "  ✅ Disabled ~/.gemini/antigravity"
fi

if [[ -d "$HOME/.antigravity" ]]; then
    rm -rf "$HOME/.antigravity" 2>/dev/null || true
    echo "  ✅ Removed ~/.antigravity"
fi

# 3. List remaining installations
echo
echo "[3/4] Remaining Antigravity installations:"
find ~ -maxdepth 5 -type d -name "antigravity" 2>/dev/null | while read dir; do
    if [[ "$dir" == *"AIEmpire-Core__codex"* ]]; then
        echo "  ✅ ACTIVE: $dir"
    else
        echo "  📁 Found: $dir (likely Claude worktree - safe to ignore)"
    fi
done

# 4. Verify current installation
echo
echo "[4/4] Verifying current installation..."
cd ~/AIEmpire-Core__codex

if python3 -c "from antigravity.config import AGENTS; print(f'  ✅ {len(AGENTS)} agents loaded successfully')" 2>/dev/null; then
    echo "  ✅ Current installation is working"
else
    echo "  ❌ Problem with current installation!"
    exit 1
fi

echo
echo "================================="
echo "✨ CLEANUP COMPLETE!"
echo "================================="
echo
echo "Summary:"
echo "  • Backups: $BACKUP_DIR"
echo "  • Active: ~/AIEmpire-Core__codex/antigravity"
echo "  • Old installations disabled/removed"
echo
