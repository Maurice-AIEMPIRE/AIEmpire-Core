#!/bin/bash
#############################################
# AIEmpire Soul Architecture v2.0 Deploy
# Run on your real Hetzner server via SSH
#############################################

set -e
echo "========================================="
echo "  DEPLOY: Soul Architecture v2.0"
echo "========================================="

# 1. Find repo
cd ~/AIEmpire-Core 2>/dev/null || cd ~/AI_Empire 2>/dev/null || {
    echo "ERROR: Repo nicht gefunden"
    exit 1
}
REPO=$(pwd)
echo "[1/5] Repo: $REPO"

# 2. Pull latest
echo ""
echo "[2/5] Git Pull..."
git fetch origin claude/empire-infrastructure-setup-KtNDE
git merge origin/claude/empire-infrastructure-setup-KtNDE --no-edit 2>/dev/null || {
    echo "  Merge conflict oder nicht auf richtigem Branch."
    echo "  Versuche direkt checkout..."
    git stash 2>/dev/null || true
    git checkout claude/empire-infrastructure-setup-KtNDE 2>/dev/null || git checkout -b claude/empire-infrastructure-setup-KtNDE origin/claude/empire-infrastructure-setup-KtNDE
    git pull origin claude/empire-infrastructure-setup-KtNDE
}
echo "[OK] Code aktualisiert"

# 3. Install dependencies
echo ""
echo "[3/5] Dependencies..."
pip3 install pyyaml -q 2>/dev/null || pip install pyyaml -q 2>/dev/null || echo "[SKIP] pyyaml manuell installieren: pip3 install pyyaml"
echo "[OK] Dependencies"

# 4. Verify Soul Architecture
echo ""
echo "[4/5] Soul Architecture verifizieren..."
python3 "$REPO/souls/soul_spawner.py"

# 5. Full status
echo ""
echo "[5/5] Empire Engine Status..."
python3 "$REPO/empire_engine.py" souls

echo ""
echo "========================================="
echo "  DEPLOY COMPLETE"
echo "========================================="
echo ""
echo "  Souls:   $REPO/souls/ (4 Core + 39 Specialists)"
echo "  Engine:  python3 empire_engine.py souls"
echo "  Bridge:  bridge.execute_with_soul(...)"
echo "  Jobs:    openclaw-config/jobs.json v2"
echo ""
echo "  COPY-PASTE TEST:"
echo "  python3 -c \"from souls.soul_spawner import get_spawner; s=get_spawner(); print(s.stats())\""
echo "========================================="
