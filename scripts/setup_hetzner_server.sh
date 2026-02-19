#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# HETZNER SERVER SETUP — AIEmpire-Core (Linux)
# ══════════════════════════════════════════════════════════════════════════════
#
# One-shot setup for a fresh Hetzner dedicated server (Ubuntu 24.04).
# Installs everything needed to run the full AI Empire stack.
#
# Server: AX102 (128GB RAM, 2x 3.84TB NVMe, AMD Ryzen 9 7950X3D)
# IP: 65.21.203.174 / 2a01:4f9:6a:1263::2
#
# Usage (run as root on server):
#   cd /opt/aiempire && bash scripts/setup_hetzner_server.sh
#
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Config ─────────────────────────────────────────────────────────────────
PROJECT_DIR="/opt/aiempire"
LOG_DIR="/var/log/aiempire"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$LOG_DIR/setup_$(date +%Y%m%d_%H%M%S).log"

# ─── Colors ─────────────────────────────────────────────────────────────────
R='\033[0;31m'
G='\033[0;32m'
Y='\033[1;33m'
B='\033[0;34m'
W='\033[1;37m'
N='\033[0m'

log_ok()   { echo -e "  ${G}[OK]${N}      $*"; echo "[OK] $*" >> "$LOG_FILE"; }
log_info() { echo -e "  ${B}[INFO]${N}    $*"; echo "[INFO] $*" >> "$LOG_FILE"; }
log_inst() { echo -e "  ${Y}[INSTALL]${N} $*"; echo "[INSTALL] $*" >> "$LOG_FILE"; }
log_fail() { echo -e "  ${R}[FAIL]${N}    $*"; echo "[FAIL] $*" >> "$LOG_FILE"; }

mkdir -p "$LOG_DIR"

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║     HETZNER SERVER SETUP — AIEmpire-Core (Linux)         ║${N}"
echo -e "${W}║     128GB RAM • Ollama • Redis • PostgreSQL • Docker     ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: System Update + Base Tools
# ═══════════════════════════════════════════════════════════════════════════

echo -e "${B}═══ PHASE 1: System Update + Base Tools ═══${N}"
echo ""

log_info "System-Update..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get upgrade -y -qq 2>&1 | tail -1
log_ok "System aktualisiert"

log_inst "Base Tools..."
apt-get install -y -qq \
    curl wget git jq htop tmux unzip zip \
    build-essential pkg-config libssl-dev \
    net-tools lsof ncdu tree \
    ca-certificates gnupg software-properties-common \
    2>&1 | tail -1
log_ok "Base Tools installiert"

# ripgrep
if ! command -v rg &>/dev/null; then
    apt-get install -y -qq ripgrep 2>/dev/null || true
fi
command -v rg &>/dev/null && log_ok "ripgrep" || log_info "ripgrep not available"

# fd
if ! command -v fdfind &>/dev/null; then
    apt-get install -y -qq fd-find 2>/dev/null || true
fi
command -v fdfind &>/dev/null && log_ok "fd-find" || log_info "fd-find not available"

# lazygit
if ! command -v lazygit &>/dev/null; then
    log_inst "lazygit..."
    LAZYGIT_VERSION=$(curl -s "https://api.github.com/repos/jesseduffield/lazygit/releases/latest" | jq -r '.tag_name' | sed 's/v//')
    curl -sL "https://github.com/jesseduffield/lazygit/releases/download/v${LAZYGIT_VERSION}/lazygit_${LAZYGIT_VERSION}_Linux_x86_64.tar.gz" | tar xz -C /usr/local/bin lazygit
    log_ok "lazygit v${LAZYGIT_VERSION}"
fi

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: Python 3.12
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${B}═══ PHASE 2: Python 3.12 ═══${N}"
echo ""

if ! command -v python3.12 &>/dev/null && ! python3 --version 2>/dev/null | grep -q "3.12"; then
    add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
    apt-get update -qq
    apt-get install -y -qq python3.12 python3.12-venv python3.12-dev
fi
log_ok "$(python3 --version 2>&1)"

# venv
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
log_ok "venv existiert: $VENV_DIR"

log_inst "pip upgrade..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip 2>&1 | tail -1
log_ok "pip aktuell"

log_inst "Python Packages..."
"$VENV_DIR/bin/pip" install --quiet \
    fastapi uvicorn[standard] httpx aiohttp aiofiles \
    redis psycopg2-binary chromadb \
    pydantic python-dotenv pyyaml \
    requests beautifulsoup4 \
    2>&1 | tail -1
log_ok "Python Packages (in venv)"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: Node.js 20
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${B}═══ PHASE 3: Node.js 20 ═══${N}"
echo ""

if ! command -v node &>/dev/null || ! node --version 2>/dev/null | grep -q "v20"; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>&1 | tail -1
    apt-get install -y -qq nodejs 2>&1 | tail -1
fi
log_ok "Node.js $(node --version 2>&1)"

npm install -g pm2 2>&1 | tail -3
log_ok "pm2 (Process Manager)"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: Docker
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${B}═══ PHASE 4: Docker ═══${N}"
echo ""

if ! command -v docker &>/dev/null; then
    log_inst "Docker..."
    curl -fsSL https://get.docker.com | bash 2>&1 | tail -1
fi
log_ok "Docker $(docker --version 2>&1 | grep -oP '\d+\.\d+\.\d+')"

if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null 2>&1; then
    apt-get install -y -qq docker-compose-plugin 2>/dev/null || true
fi
log_ok "Docker Compose $(docker compose version 2>&1 | grep -oP '\d+\.\d+\.\d+')"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 5: Ollama (Lokale AI — Kostenlos)
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${B}═══ PHASE 5: Ollama (Lokale AI — Kostenlos) ═══${N}"
echo ""

if ! command -v ollama &>/dev/null; then
    log_inst "Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    log_ok "Ollama installiert"
else
    log_ok "Ollama bereits installiert"
fi

# Wait for Ollama to be ready
sleep 2

# Detect GPU
if command -v nvidia-smi &>/dev/null; then
    log_ok "NVIDIA GPU detected — Ollama uses GPU acceleration"
else
    echo -e "  ${Y}WARNING:${N} No NVIDIA/AMD GPU detected. Ollama will run in CPU-only mode."
fi

log_info "Lade AI Modelle (128GB RAM = grosse Modelle moeglich)..."

for MODEL in "qwen2.5-coder:7b" "qwen2.5-coder:14b" "deepseek-r1:7b"; do
    if ollama list 2>/dev/null | grep -q "$(echo $MODEL | cut -d: -f1)"; then
        log_ok "Model: $MODEL (already pulled)"
    else
        log_inst "Model: $MODEL (einmalig, dauert ein paar Minuten)..."
        ollama pull "$MODEL" 2>&1 | tail -1
        log_ok "Model: $MODEL"
    fi
done

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 6: Datenbanken
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${B}═══ PHASE 6: Datenbanken ═══${N}"
echo ""

# Redis
if ! command -v redis-server &>/dev/null; then
    log_inst "Redis..."
    apt-get install -y -qq redis-server 2>&1 | tail -1
fi
systemctl enable --now redis-server 2>/dev/null || true
log_ok "Redis installiert und gestartet"

# PostgreSQL 16
if ! command -v psql &>/dev/null; then
    log_inst "PostgreSQL 16..."
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - 2>/dev/null
    apt-get update -qq
    apt-get install -y -qq postgresql-16 postgresql-client-16 2>&1 | tail -1
fi
systemctl enable --now postgresql 2>/dev/null || true
log_ok "PostgreSQL installiert"

# Create aiempire database if not exists
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='aiempire'\" | grep -q 1 || createdb aiempire" 2>/dev/null || true

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 7: AIEmpire-Core Setup
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${B}═══ PHASE 7: AIEmpire-Core Setup ═══${N}"
echo ""

if [ -d "$PROJECT_DIR/.git" ]; then
    log_ok "Repository bereits vorhanden in $PROJECT_DIR"
else
    log_inst "Cloning Repository..."
    git clone https://github.com/Maurice-AIEMPIRE/AIEmpire-Core.git "$PROJECT_DIR" 2>&1 | tail -1
    log_ok "Repository gecloned"
fi

# .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    log_info "Erstelle .env Datei..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env" 2>/dev/null || true
    chmod 600 "$PROJECT_DIR/.env"
    log_ok ".env erstellt (API Keys eintragen!)"
else
    log_ok ".env existiert"
fi

# CRM dependencies
if [ -d "$PROJECT_DIR/crm" ] && [ -f "$PROJECT_DIR/crm/package.json" ]; then
    log_inst "CRM Dependencies..."
    cd "$PROJECT_DIR/crm" && npm install --production 2>&1 | tail -3
    cd "$PROJECT_DIR"
    log_ok "CRM Dependencies"
fi

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 8: Systemd Services
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${B}═══ PHASE 8: Systemd Services ═══${N}"
echo ""

SERVICES_DIR="$PROJECT_DIR/systems"

for SERVICE_FILE in "$SERVICES_DIR"/aiempire-*.service "$SERVICES_DIR"/aiempire-*.timer; do
    [ ! -f "$SERVICE_FILE" ] && continue
    BASENAME=$(basename "$SERVICE_FILE")
    cp "$SERVICE_FILE" "/etc/systemd/system/$BASENAME"
    log_ok "$BASENAME"
done

systemctl daemon-reload
systemctl enable aiempire-bombproof.service 2>/dev/null || true
systemctl enable aiempire-content.timer 2>/dev/null || true
log_ok "Alle Services registriert"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 9: Firewall (UFW)
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${B}═══ PHASE 9: Firewall (UFW) ═══${N}"
echo ""

if ! command -v ufw &>/dev/null; then
    apt-get install -y -qq ufw 2>/dev/null
fi

ufw default deny incoming 2>/dev/null
ufw default allow outgoing 2>/dev/null
ufw allow ssh 2>/dev/null
ufw allow 80/tcp 2>/dev/null
ufw allow 443/tcp 2>/dev/null
ufw --force enable 2>/dev/null
log_ok "Firewall aktiv (SSH + HTTP + HTTPS)"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 10: Security
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${B}═══ PHASE 10: Security ═══${N}"
echo ""

if ! command -v fail2ban-client &>/dev/null; then
    log_inst "fail2ban..."
    apt-get install -y -qq fail2ban 2>&1 | tail -1
fi
systemctl enable --now fail2ban 2>/dev/null || true
log_ok "fail2ban (SSH Brute-Force Schutz)"

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║                SETUP COMPLETE                             ║${N}"
echo -e "${W}╠═══════════════════════════════════════════════════════════╣${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}║  AI:         Ollama + Qwen2.5 + DeepSeek R1               ║${N}"
echo -e "${W}║  Runtime:    Python 3.12 + Node.js 20                     ║${N}"
echo -e "${W}║  Container:  Docker + Docker Compose                      ║${N}"
echo -e "${W}║  Datenbank:  PostgreSQL 16 + Redis                        ║${N}"
echo -e "${W}║  Firewall:   UFW (SSH + HTTP/S only)                      ║${N}"
echo -e "${W}║  Security:   fail2ban aktiv                               ║${N}"
echo -e "${W}║  Services:   CRM, Empire API, Bombproof, Content-Timer    ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}║  Projekt:    $PROJECT_DIR                          ║${N}"
echo -e "${W}║  Logs:       $LOG_DIR/                           ║${N}"
echo -e "${W}║  .env:       $PROJECT_DIR/.env                    ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""
echo -e "  ${W}Naechste Schritte:${N}"
echo -e "  1. API Keys eintragen: ${G}nano $PROJECT_DIR/.env${N}"
echo -e "  2. venv aktivieren:    ${G}source $PROJECT_DIR/venv/bin/activate${N}"
echo -e "  3. CRM starten:        ${G}systemctl start aiempire-crm${N}"
echo -e "  4. Empire API starten: ${G}systemctl start aiempire-empire-api${N}"
echo -e "  5. Runner setup:       ${G}bash $PROJECT_DIR/scripts/setup_github_runner.sh${N}"
echo -e "  6. Docker Stack:       ${G}cd $PROJECT_DIR/systems && docker compose up -d${N}"
echo -e "  7. Status pruefen:     ${G}bash $PROJECT_DIR/scripts/bombproof_startup.sh --status${N}"
echo ""
echo -e "  Setup-Log: $LOG_FILE"
echo ""
