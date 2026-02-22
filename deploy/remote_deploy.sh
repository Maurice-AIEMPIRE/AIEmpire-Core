#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# AI EMPIRE - One-Click Remote Deployment to Hetzner
# Run from your LOCAL machine (Mac/Linux)
# Usage: bash deploy/remote_deploy.sh
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────
SERVER_IP="100.124.239.46"
SERVER_USER="root"
REMOTE_DIR="/opt/aiempire"
REPO_URL="https://github.com/Maurice-AIEMPIRE/AIEmpire-Core.git"
BRANCH="claude/deploy-openclaw-abt-protocol-cf1G2"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }
info() { echo -e "${CYAN}[INFO]${NC} $*"; }

SSH_CMD="ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     AI EMPIRE — Hetzner Remote Deployment               ║${NC}"
echo -e "${GREEN}║     Server: ${SERVER_IP}                            ║${NC}"
echo -e "${GREEN}║     Branch: ${BRANCH}  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Step 1: Test SSH Connection ─────────────────────────────
log "Step 1/6: Testing SSH connection..."
if ! $SSH_CMD 'echo "connected"' 2>/dev/null; then
    err "Cannot connect to $SERVER_IP"
    err "Make sure SSH key is set up: ssh-copy-id root@$SERVER_IP"
    exit 1
fi
info "SSH connection OK"

# ─── Step 2: Setup Server (Docker, Git, System) ─────────────
log "Step 2/6: Setting up server..."
$SSH_CMD << 'REMOTE_SETUP'
set -e

echo "[SERVER] Updating packages..."
apt-get update -qq

echo "[SERVER] Installing essentials..."
apt-get install -y -qq \
    curl wget git htop tmux vim \
    ca-certificates gnupg lsb-release \
    python3 python3-pip python3-venv \
    ufw 2>/dev/null || true

# Install Docker if needed
if ! command -v docker &>/dev/null; then
    echo "[SERVER] Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Docker Compose plugin
if ! docker compose version &>/dev/null; then
    echo "[SERVER] Installing Docker Compose..."
    apt-get install -y -qq docker-compose-plugin 2>/dev/null || true
fi

echo "[SERVER] Docker: $(docker --version 2>/dev/null || echo 'not found')"

# System tuning
cat > /etc/sysctl.d/99-empire.conf << 'SYSCTL'
vm.overcommit_memory=1
vm.swappiness=10
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535
fs.file-max=1000000
SYSCTL
sysctl -p /etc/sysctl.d/99-empire.conf 2>/dev/null || true

# Firewall
if command -v ufw &>/dev/null; then
    ufw allow 22/tcp 2>/dev/null || true
    ufw allow 80/tcp 2>/dev/null || true
    ufw allow 443/tcp 2>/dev/null || true
    ufw --force enable 2>/dev/null || true
fi

# Backup dir
mkdir -p /mnt/backup/empire

echo "[SERVER] Setup complete"
REMOTE_SETUP

info "Server setup done"

# ─── Step 3: Clone/Update Repository ─────────────────────────
log "Step 3/6: Deploying code to server..."
$SSH_CMD << REMOTE_CLONE
set -e

if [ -d "${REMOTE_DIR}/.git" ]; then
    echo "[SERVER] Updating existing repo..."
    cd ${REMOTE_DIR}

    # Clean macOS resource forks
    find .git/objects/pack -name '._*' -delete 2>/dev/null || true

    git fetch origin ${BRANCH} || {
        echo "[SERVER] Fetch failed, doing fresh clone..."
        cd /opt
        mv aiempire aiempire.old.\$(date +%s) 2>/dev/null || true
        git clone ${REPO_URL} aiempire
        cd ${REMOTE_DIR}
    }

    git checkout ${BRANCH} 2>/dev/null || git checkout -b ${BRANCH} origin/${BRANCH}
    git pull origin ${BRANCH} || git reset --hard origin/${BRANCH}
else
    echo "[SERVER] Fresh clone..."
    mkdir -p /opt
    git clone ${REPO_URL} ${REMOTE_DIR}
    cd ${REMOTE_DIR}
    git checkout -b ${BRANCH} origin/${BRANCH} 2>/dev/null || git checkout ${BRANCH}
fi

echo "[SERVER] Branch: \$(git branch --show-current)"
echo "[SERVER] Latest commit: \$(git log --oneline -1)"
REMOTE_CLONE

info "Code deployed to ${REMOTE_DIR}"

# ─── Step 4: Setup Environment ──────────────────────────────
log "Step 4/6: Configuring environment..."
$SSH_CMD << REMOTE_ENV
set -e
cd ${REMOTE_DIR}/deploy

if [ ! -f .env ]; then
    cp .env.template .env
    echo "[SERVER] Created .env from template"
    echo "[SERVER] ⚠️  IMPORTANT: Edit API keys in ${REMOTE_DIR}/deploy/.env"
else
    echo "[SERVER] .env already configured"
fi

# Show current config (masked)
echo ""
echo "Current .env (values masked):"
while IFS='=' read -r key value; do
    [[ "\$key" =~ ^#.*$ ]] && continue
    [[ -z "\$key" ]] && continue
    echo "  \$key=****"
done < .env 2>/dev/null || true
REMOTE_ENV

info "Environment configured"

# ─── Step 5: Build and Start Docker Stack ─────────────────────
log "Step 5/6: Starting Docker stack..."
$SSH_CMD << REMOTE_START
set -e
cd ${REMOTE_DIR}/deploy

echo "[SERVER] Building containers..."
docker compose -f docker-compose.yml --env-file .env build 2>&1 | tail -5

echo "[SERVER] Starting all services..."
docker compose -f docker-compose.yml --env-file .env up -d

echo "[SERVER] Waiting for health checks..."
sleep 15

echo ""
echo "═══ CONTAINER STATUS ═══"
docker compose -f docker-compose.yml ps

echo ""
echo "═══ SERVICE HEALTH ═══"
for svc in "Ollama:11434/api/tags" "LiteLLM:4000/health" "Redis:6379" "ChromaDB:8000/api/v1/heartbeat" "AntProtocol:8900/health" "Skybot:8901/health"; do
    name="\${svc%%:*}"
    endpoint="\${svc#*:}"
    port="\${endpoint%%/*}"
    path="/\${endpoint#*/}"
    [ "\$path" = "/\$port" ] && path=""

    if curl -sf "http://localhost:\${port}\${path}" >/dev/null 2>&1; then
        echo "  ✓ \$name (port \$port)"
    else
        echo "  - \$name (port \$port) — starting..."
    fi
done

echo ""
echo "═══ SYSTEM RESOURCES ═══"
echo "  RAM:  \$(free -h | awk '/^Mem:/{print \$3"/"\$2}')"
echo "  Disk: \$(df -h / | awk 'NR==2{print \$3"/"\$2" ("\$5")"}')"
echo "  CPU:  \$(nproc) cores"
REMOTE_START

info "Docker stack started"

# ─── Step 6: Final Summary ────────────────────────────────────
log "Step 6/6: Deployment complete!"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            DEPLOYMENT SUCCESSFUL!                        ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}║  Server:    ${SERVER_IP}                            ║${NC}"
echo -e "${GREEN}║  Directory: ${REMOTE_DIR}                           ║${NC}"
echo -e "${GREEN}║  Branch:    ${BRANCH}  ║${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}║  Services:                                               ║${NC}"
echo -e "${GREEN}║    Ollama      → http://${SERVER_IP}:11434          ║${NC}"
echo -e "${GREEN}║    LiteLLM     → http://${SERVER_IP}:4000           ║${NC}"
echo -e "${GREEN}║    Ant Protocol→ http://${SERVER_IP}:8900           ║${NC}"
echo -e "${GREEN}║    Skybot      → http://${SERVER_IP}:8901           ║${NC}"
echo -e "${GREEN}║    Redis       → ${SERVER_IP}:6379                  ║${NC}"
echo -e "${GREEN}║    ChromaDB    → http://${SERVER_IP}:8000           ║${NC}"
echo -e "${GREEN}║    Grafana     → http://${SERVER_IP}:3000           ║${NC}"
echo -e "${GREEN}║    Prometheus  → http://${SERVER_IP}:9090           ║${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Next Steps:                                             ║${NC}"
echo -e "${GREEN}║  1. Edit API keys:                                       ║${NC}"
echo -e "${GREEN}║     ssh root@${SERVER_IP}                           ║${NC}"
echo -e "${GREEN}║     nano /opt/aiempire/deploy/.env                       ║${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}║  2. Pull Ollama models:                                  ║${NC}"
echo -e "${GREEN}║     ssh root@${SERVER_IP}                           ║${NC}"
echo -e "${GREEN}║     cd /opt/aiempire/deploy && ./deploy.sh ollama-pull   ║${NC}"
echo -e "${GREEN}║                                                          ║${NC}"
echo -e "${GREEN}║  3. Check status:                                        ║${NC}"
echo -e "${GREEN}║     ssh root@${SERVER_IP}                           ║${NC}"
echo -e "${GREEN}║     cd /opt/aiempire/deploy && ./deploy.sh status        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
