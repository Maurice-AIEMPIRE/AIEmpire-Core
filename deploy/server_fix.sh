#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# AI EMPIRE - Server Fix & Deploy Script
# Run this ON THE HETZNER SERVER via SSH
# Usage: ssh root@100.124.239.46 'bash -s' < deploy/server_fix.sh
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[EMPIRE]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

REPO_DIR="/opt/aiempire"

# ─── Step 1: Fix git corruption (macOS resource forks) ──────
log "Step 1: Fixing git pack corruption..."
cd "$REPO_DIR"

# Remove macOS resource fork files from git objects
find .git/objects/pack -name '._*' -delete 2>/dev/null && \
    log "Removed macOS resource fork files from git pack" || \
    log "No resource fork files found"

# Verify git integrity
git fsck --no-dangling 2>/dev/null || warn "Some git objects may need repair"

# ─── Step 2: Fresh clone if git is too broken ───────────────
if ! git status >/dev/null 2>&1; then
    warn "Git repo too damaged. Doing fresh clone..."
    cd /opt
    mv aiempire aiempire.broken.$(date +%s) 2>/dev/null || true
    git clone https://github.com/Maurice-AIEMPIRE/AIEmpire-Core.git aiempire
    cd "$REPO_DIR"
fi

# ─── Step 3: Fetch and checkout the deploy branch ──────────
log "Step 2: Fetching deploy branch..."
git config pull.rebase false
git fetch origin claude/deploy-openclaw-abt-protocol-cf1G2

# Try to checkout the branch
if git rev-parse --verify claude/deploy-openclaw-abt-protocol-cf1G2 >/dev/null 2>&1; then
    git checkout claude/deploy-openclaw-abt-protocol-cf1G2
    git pull origin claude/deploy-openclaw-abt-protocol-cf1G2 || \
        git reset --hard origin/claude/deploy-openclaw-abt-protocol-cf1G2
else
    git checkout -b claude/deploy-openclaw-abt-protocol-cf1G2 origin/claude/deploy-openclaw-abt-protocol-cf1G2
fi

log "On branch: $(git branch --show-current)"

# ─── Step 4: Install Docker if needed ──────────────────────
log "Step 3: Checking Docker..."
if ! command -v docker &>/dev/null; then
    log "Installing Docker..."
    apt-get update && apt-get install -y curl
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

if ! docker compose version &>/dev/null; then
    log "Installing Docker Compose plugin..."
    apt-get update && apt-get install -y docker-compose-plugin
fi

log "Docker version: $(docker --version)"

# ─── Step 5: Create .env from template ─────────────────────
log "Step 4: Setting up environment..."
cd "$REPO_DIR/deploy"

if [ ! -f .env ]; then
    cp .env.template .env
    warn "Created .env from template!"
    warn "EDIT IT NOW: nano /opt/aiempire/deploy/.env"
else
    log ".env already exists"
fi

# ─── Step 6: System optimization for 64GB RAM ──────────────
log "Step 5: Optimizing system for 64GB RAM..."
cat > /etc/sysctl.d/99-empire.conf << 'SYSCTL'
vm.overcommit_memory=1
vm.swappiness=10
net.core.somaxconn=65535
fs.file-max=1000000
SYSCTL
sysctl -p /etc/sysctl.d/99-empire.conf 2>/dev/null || true

# ─── Step 7: Setup firewall ────────────────────────────────
log "Step 6: Configuring firewall..."
if command -v ufw &>/dev/null; then
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw --force enable 2>/dev/null || true
fi

# ─── Step 8: Create backup dir ─────────────────────────────
mkdir -p /mnt/backup/empire

# ─── Done ───────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN} SERVER SETUP COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit API keys:  nano /opt/aiempire/deploy/.env"
echo "  2. Start stack:    cd /opt/aiempire/deploy && ./deploy.sh start"
echo "  3. Pull models:    ./deploy.sh ollama-pull"
echo "  4. Check status:   ./deploy.sh status"
echo ""
echo "Server: $(hostname) | RAM: $(free -h | awk '/^Mem:/{print $2}') | Disk: $(df -h / | awk 'NR==2{print $2}')"
echo ""
