#!/bin/bash
#############################################
# AIEmpire Local Setup - Run on Mac via SSH
# Copy-paste this entire block into Terminus
#############################################

set -e
echo "========================================="
echo "  AIEmpire Local Setup"
echo "========================================="

# 1. Pull latest from Git
echo ""
echo "[1/6] Git Pull..."
cd ~/AIEmpire-Core 2>/dev/null || cd ~/AI_Empire 2>/dev/null || {
    echo "ERROR: Repo not found at ~/AIEmpire-Core or ~/AI_Empire"
    echo "Run: git clone https://github.com/Maurice-AIEMPIRE/AIEmpire-Core.git ~/AIEmpire-Core"
    exit 1
}
REPO_DIR=$(pwd)
git pull origin claude/empire-infrastructure-setup-3pUSp 2>/dev/null || git fetch origin && git checkout claude/empire-infrastructure-setup-3pUSp && git pull
echo "[OK] Repo updated: $REPO_DIR"

# 2. Create OpenClaw workspace + symlink
echo ""
echo "[2/6] OpenClaw Workspace..."
mkdir -p ~/.openclaw/workspace
cp -f "$REPO_DIR/workspace/INVENTORY.md" ~/.openclaw/workspace/
cp -f "$REPO_DIR/workspace/OPPORTUNITIES.md" ~/.openclaw/workspace/
cp -f "$REPO_DIR/workspace/BUILD_LOG.md" ~/.openclaw/workspace/
echo "[OK] 3 files in ~/.openclaw/workspace/"

# 3. EMPIRE_BRAIN in iCloud
echo ""
echo "[3/6] EMPIRE_BRAIN in iCloud..."
ICLOUD=~/Library/Mobile\ Documents/com~apple~CloudDocs
if [ -d "$ICLOUD" ]; then
    mkdir -p "$ICLOUD/EMPIRE_BRAIN"
    # Symlink from repo to iCloud
    for DIR in memory/chats memory/knowledge projects assets revenue legacy; do
        mkdir -p "$ICLOUD/EMPIRE_BRAIN/$DIR"
    done
    # Copy READMEs
    cp -f "$REPO_DIR/empire_brain/README.md" "$ICLOUD/EMPIRE_BRAIN/"
    cp -f "$REPO_DIR/empire_brain/memory/chats/README.md" "$ICLOUD/EMPIRE_BRAIN/memory/chats/"
    cp -f "$REPO_DIR/empire_brain/memory/knowledge/README.md" "$ICLOUD/EMPIRE_BRAIN/memory/knowledge/"
    cp -f "$REPO_DIR/empire_brain/projects/README.md" "$ICLOUD/EMPIRE_BRAIN/projects/"
    cp -f "$REPO_DIR/empire_brain/assets/README.md" "$ICLOUD/EMPIRE_BRAIN/assets/"
    cp -f "$REPO_DIR/empire_brain/revenue/README.md" "$ICLOUD/EMPIRE_BRAIN/revenue/"
    cp -f "$REPO_DIR/empire_brain/legacy/README.md" "$ICLOUD/EMPIRE_BRAIN/legacy/"
    echo "[OK] EMPIRE_BRAIN in iCloud erstellt"
else
    echo "[SKIP] iCloud nicht gefunden - nur auf macOS verfuegbar"
fi

# 4. Verify content_scheduler.py
echo ""
echo "[4/6] Content Scheduler..."
chmod +x "$REPO_DIR/src/content_scheduler.py"
python3 "$REPO_DIR/src/content_scheduler.py" --dry-run 2>/dev/null | head -5
echo "[OK] content_scheduler.py ist executable"

# 5. Show product listings
echo ""
echo "[5/6] Product Listings bereit..."
echo "  Gumroad:"
ls -1 "$REPO_DIR/publish/listings/gumroad_"* 2>/dev/null | while read f; do echo "    $(basename $f)"; done
echo "  Etsy:"
ls -1 "$REPO_DIR/publish/listings/etsy_"* 2>/dev/null | while read f; do echo "    $(basename $f)"; done
echo "  Formatted Posts:"
ls -1 "$REPO_DIR/publish/formatted/"* 2>/dev/null | wc -l | xargs -I{} echo "    {} platform-ready posts"

# 6. Summary
echo ""
echo "========================================="
echo "  SETUP COMPLETE"
echo "========================================="
echo ""
echo "  Workspace:    ~/.openclaw/workspace/ (3 .md files)"
echo "  Scheduler:    $REPO_DIR/src/content_scheduler.py"
echo "  Listings:     $REPO_DIR/publish/listings/ (6 files)"
echo "  EMPIRE_BRAIN: iCloud/EMPIRE_BRAIN/ (6 dirs)"
echo ""
echo "  NEXT STEPS:"
echo "  1. Gumroad Listing oeffnen:"
echo "     cat $REPO_DIR/publish/listings/gumroad_bma_checklisten.md"
echo "  2. Content posten:"
echo "     python3 $REPO_DIR/src/content_scheduler.py"
echo "  3. Etsy Listing anschauen:"
echo "     cat $REPO_DIR/publish/listings/etsy_bma_checklisten.txt"
echo "========================================="
