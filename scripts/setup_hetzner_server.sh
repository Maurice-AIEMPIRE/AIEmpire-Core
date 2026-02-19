#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# HETZNER SERVER SETUP — AIEmpire-Core (Linux/Ubuntu)
# ══════════════════════════════════════════════════════════════════════════════
#
# Ein-Befehl-Installation fuer deinen Hetzner Dedicated Server.
# Installiert ALLES was du brauchst: AI, Datenbanken, Tools, Services.
#
# Zielserver: i7-8700, 128GB RAM, 2x1TB SSD, Ubuntu 22.04/24.04 LTS
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/Maurice-AIEMPIRE/AIEmpire-Core/main/scripts/setup_hetzner_server.sh | sudo bash
#   # ODER:
#   chmod +x scripts/setup_hetzner_server.sh
#   sudo ./scripts/setup_hetzner_server.sh
#
# ══════════════════════════════════════════════════════════════════════════════

set -e

G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
B='\033[0;34m'
C='\033[0;36m'
W='\033[1;37m'
N='\033[0m'

PROJECT_DIR="/opt/aiempire"
LOG_FILE="/var/log/aiempire/setup_$(date +%Y%m%d_%H%M%S).log"

mkdir -p /var/log/aiempire

log() {
    local level="$1"; shift
    local msg="$*"
    local ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[$ts] [$level] $msg" >> "$LOG_FILE"
    case "$level" in
        OK)    echo -e "  ${G}[OK]${N}      $msg" ;;
        INSTALL) echo -e "  ${Y}[INSTALL]${N} $msg" ;;
        INFO)  echo -e "  ${B}[INFO]${N}    $msg" ;;
        WARN)  echo -e "  ${Y}[WARN]${N}    $msg" ;;
        FAIL)  echo -e "  ${R}[FAIL]${N}    $msg" ;;
    esac
}

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║     HETZNER SERVER SETUP — AIEmpire-Core (Linux)         ║${N}"
echo -e "${W}║     128GB RAM • Ollama • Redis • PostgreSQL • Docker     ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""

# ─── Check root ─────────────────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${R}[ERROR]${N} Dieses Script muss als root laufen (sudo)"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: SYSTEM UPDATE + BASE TOOLS
# ═══════════════════════════════════════════════════════════════════════════════

echo -e "${C}═══ PHASE 1: System Update + Base Tools ═══${N}"
echo ""

export DEBIAN_FRONTEND=noninteractive

log INFO "System-Update..."
apt-get update -qq
apt-get upgrade -y -qq
log OK "System aktualisiert"

# Base packages
PACKAGES="git curl wget build-essential software-properties-common apt-transport-https ca-certificates gnupg lsb-release jq unzip htop"

log INSTALL "Base Tools..."
apt-get install -y -qq $PACKAGES
log OK "Base Tools installiert"

# ripgrep
if ! command -v rg &>/dev/null; then
    log INSTALL "ripgrep..."
    apt-get install -y -qq ripgrep 2>/dev/null || true
fi
log OK "ripgrep"

# fd-find
if ! command -v fdfind &>/dev/null && ! command -v fd &>/dev/null; then
    log INSTALL "fd-find..."
    apt-get install -y -qq fd-find 2>/dev/null || true
fi
log OK "fd-find"

# btop
if ! command -v btop &>/dev/null; then
    log INSTALL "btop..."
    apt-get install -y -qq btop 2>/dev/null || {
        snap install btop 2>/dev/null || log WARN "btop konnte nicht installiert werden"
    }
fi

# lazygit
if ! command -v lazygit &>/dev/null; then
    log INSTALL "lazygit..."
    LAZYGIT_VERSION=$(curl -s "https://api.github.com/repos/jesseduffield/lazygit/releases/latest" | jq -r '.tag_name' | sed 's/v//')
    if [ -n "$LAZYGIT_VERSION" ] && [ "$LAZYGIT_VERSION" != "null" ]; then
        curl -Lo /tmp/lazygit.tar.gz "https://github.com/jesseduffield/lazygit/releases/latest/download/lazygit_${LAZYGIT_VERSION}_Linux_x86_64.tar.gz"
        tar xzf /tmp/lazygit.tar.gz -C /tmp lazygit
        install /tmp/lazygit /usr/local/bin/
        rm -f /tmp/lazygit /tmp/lazygit.tar.gz
        log OK "lazygit v${LAZYGIT_VERSION}"
    else
        log WARN "lazygit Version nicht gefunden"
    fi
else
    log OK "lazygit"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: PYTHON 3.12
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 2: Python 3.12 ═══${N}"
echo ""

if python3 --version 2>/dev/null | grep -q "3.12"; then
    log OK "Python $(python3 --version | cut -d' ' -f2)"
else
    log INSTALL "Python 3.12 via deadsnakes PPA..."
    add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
    apt-get update -qq
    apt-get install -y -qq python3.12 python3.12-venv python3.12-dev python3-pip || {
        log WARN "Python 3.12 PPA nicht verfuegbar, nutze System-Python"
        apt-get install -y -qq python3 python3-venv python3-dev python3-pip
    }
    log OK "Python installiert"
fi

# Python packages
log INSTALL "Python Packages..."
pip3 install --quiet --break-system-packages \
    httpx aiohttp fastapi uvicorn \
    pyyaml python-dotenv \
    ruff pytest redis \
    2>/dev/null || pip3 install --quiet \
    httpx aiohttp fastapi uvicorn \
    pyyaml python-dotenv \
    ruff pytest redis \
    2>/dev/null
log OK "Python Packages"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: NODE.JS 20
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 3: Node.js 20 ═══${N}"
echo ""

if command -v node &>/dev/null && node --version | grep -q "v2[0-9]"; then
    log OK "Node.js $(node --version)"
else
    log INSTALL "Node.js 20 via NodeSource..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
    log OK "Node.js $(node --version)"
fi

# npm global tools
npm install -g pm2 2>/dev/null && log OK "pm2 (Process Manager)" || log WARN "pm2"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: DOCKER + DOCKER COMPOSE
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 4: Docker ═══${N}"
echo ""

if command -v docker &>/dev/null; then
    log OK "Docker $(docker --version | cut -d' ' -f3 | tr -d ',')"
else
    log INSTALL "Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    log OK "Docker installiert"
fi

# Docker Compose (v2 plugin)
if docker compose version &>/dev/null; then
    log OK "Docker Compose $(docker compose version --short)"
else
    log INSTALL "Docker Compose Plugin..."
    apt-get install -y -qq docker-compose-plugin 2>/dev/null || true
fi

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: OLLAMA (LOKALE LLMs — KOSTENLOS)
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 5: Ollama (Lokale AI — Kostenlos) ═══${N}"
echo ""

if command -v ollama &>/dev/null; then
    log OK "Ollama"
else
    log INSTALL "Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    log OK "Ollama installiert"
fi

# Enable and start Ollama service
systemctl enable ollama 2>/dev/null || true
systemctl start ollama 2>/dev/null || true
sleep 3

# Pull models (128GB RAM = can handle big models)
log INFO "Lade AI Modelle (128GB RAM = grosse Modelle moeglich)..."
for model in "qwen2.5-coder:7b" "qwen2.5-coder:14b" "deepseek-r1:7b"; do
    if ollama list 2>/dev/null | grep -q "$model"; then
        log OK "Model: $model"
    else
        log INSTALL "Model: $model (einmalig, dauert ein paar Minuten)..."
        ollama pull "$model" 2>/dev/null && log OK "Model: $model" || log WARN "Model $model konnte nicht geladen werden"
    fi
done

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: DATABASES (Redis + PostgreSQL)
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 6: Datenbanken ═══${N}"
echo ""

# Redis
if command -v redis-server &>/dev/null; then
    log OK "Redis"
else
    log INSTALL "Redis..."
    apt-get install -y -qq redis-server
    systemctl enable redis-server
    systemctl start redis-server
    log OK "Redis installiert und gestartet"
fi

# PostgreSQL 16
if command -v psql &>/dev/null; then
    log OK "PostgreSQL $(psql --version | cut -d' ' -f3)"
else
    log INSTALL "PostgreSQL 16..."
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' 2>/dev/null || true
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - 2>/dev/null || true
    apt-get update -qq
    apt-get install -y -qq postgresql-16 || apt-get install -y -qq postgresql
    systemctl enable postgresql
    systemctl start postgresql
    log OK "PostgreSQL installiert"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: CLONE REPO + SETUP
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 7: AIEmpire-Core Setup ═══${N}"
echo ""

if [ -d "$PROJECT_DIR/.git" ]; then
    log OK "Repository bereits vorhanden in $PROJECT_DIR"
    cd "$PROJECT_DIR"
    git pull origin main 2>/dev/null || true
else
    log INSTALL "Clone AIEmpire-Core..."
    git clone https://github.com/Maurice-AIEMPIRE/AIEmpire-Core.git "$PROJECT_DIR" 2>/dev/null || {
        log WARN "Git clone fehlgeschlagen (Private Repo?)"
        log INFO "Manuell: git clone <url> $PROJECT_DIR"
        mkdir -p "$PROJECT_DIR"
    }
fi

# ─── .env Setup ─────────────────────────────────────────────────────────────
if [ ! -f "$PROJECT_DIR/.env" ]; then
    log INFO "Erstelle .env Datei..."
    cat > "$PROJECT_DIR/.env" << 'ENVFILE'
# ══════════════════════════════════════════════════════════════════════════════
# AIEmpire-Core Environment Variables
# Alle API Keys hier eintragen — NIEMALS ins Repo committen!
# ══════════════════════════════════════════════════════════════════════════════

# --- AI APIs ---
ANTHROPIC_API_KEY=
MOONSHOT_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=

# --- Revenue ---
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
GUMROAD_API_KEY=

# --- Social Media ---
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=

# --- Communication ---
TELEGRAM_BOT_TOKEN=

# --- Database ---
POSTGRES_PASSWORD=aiempire
POSTGRES_DB=aiempire
REDIS_URL=redis://localhost:6379

# --- Server ---
NODE_ENV=production
PORT=3500
OLLAMA_HOST=http://localhost:11434
ENVFILE
    chmod 600 "$PROJECT_DIR/.env"
    log OK ".env erstellt (API Keys eintragen!)"
else
    log OK ".env existiert bereits"
fi

# ─── CRM Dependencies ───────────────────────────────────────────────────────
if [ -d "$PROJECT_DIR/crm" ] && [ -f "$PROJECT_DIR/crm/package.json" ]; then
    log INSTALL "CRM Dependencies..."
    cd "$PROJECT_DIR/crm"
    npm install --production 2>/dev/null && log OK "CRM Dependencies" || log WARN "CRM npm install fehlgeschlagen"
    cd "$PROJECT_DIR"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8: SYSTEMD SERVICES
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 8: Systemd Services ═══${N}"
echo ""

# CRM Service
cat > /etc/systemd/system/aiempire-crm.service << UNIT
[Unit]
Description=AIEmpire CRM (Express.js)
After=network.target redis-server.service postgresql.service
Wants=redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}/crm
ExecStart=$(which node) server.js
Restart=on-failure
RestartSec=10
EnvironmentFile=${PROJECT_DIR}/.env
Environment=PORT=3500

[Install]
WantedBy=multi-user.target
UNIT
log OK "aiempire-crm.service"

# SkyBot Service
cat > /etc/systemd/system/aiempire-skybot.service << UNIT
[Unit]
Description=AIEmpire SkyBot (Telegram AI Agent)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=$(which python3) -m skybot.bot
Restart=on-failure
RestartSec=30
EnvironmentFile=${PROJECT_DIR}/.env

[Install]
WantedBy=multi-user.target
UNIT
log OK "aiempire-skybot.service"

# Bombproof Startup Service (runs once at boot)
cat > /etc/systemd/system/aiempire-bombproof.service << UNIT
[Unit]
Description=AIEmpire Bombproof Startup
After=network.target ollama.service redis-server.service postgresql.service
Wants=ollama.service redis-server.service

[Service]
Type=oneshot
User=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=/bin/bash ${PROJECT_DIR}/scripts/bombproof_startup.sh
RemainAfterExit=yes
EnvironmentFile=${PROJECT_DIR}/.env

[Install]
WantedBy=multi-user.target
UNIT
log OK "aiempire-bombproof.service"

# Content Automation Timer (statt Cron)
cat > /etc/systemd/system/aiempire-content.service << UNIT
[Unit]
Description=AIEmpire Content Generation
After=network.target ollama.service

[Service]
Type=oneshot
User=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=$(which python3) empire_engine.py auto
EnvironmentFile=${PROJECT_DIR}/.env
UNIT

cat > /etc/systemd/system/aiempire-content.timer << UNIT
[Unit]
Description=Run content generation every 4 hours

[Timer]
OnCalendar=*-*-* 06,10,14,18,22:00:00
Persistent=true

[Install]
WantedBy=timers.target
UNIT
log OK "aiempire-content.timer (alle 4 Stunden)"

# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable aiempire-bombproof.service 2>/dev/null
systemctl enable aiempire-content.timer 2>/dev/null
systemctl start aiempire-content.timer 2>/dev/null

log OK "Alle Services registriert"

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 9: FIREWALL
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 9: Firewall (UFW) ═══${N}"
echo ""

if command -v ufw &>/dev/null; then
    ufw --force reset 2>/dev/null || true
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp    # HTTP (fuer Let's Encrypt + Reverse Proxy)
    ufw allow 443/tcp   # HTTPS
    # Interne Services nur ueber localhost erreichbar (kein ufw allow noetig)
    ufw --force enable
    log OK "Firewall aktiv (SSH + HTTP + HTTPS)"
else
    apt-get install -y -qq ufw
    log WARN "UFW installiert — bitte manuell konfigurieren"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10: SECURITY HARDENING
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${C}═══ PHASE 10: Security ═══${N}"
echo ""

# fail2ban
if ! command -v fail2ban-client &>/dev/null; then
    log INSTALL "fail2ban..."
    apt-get install -y -qq fail2ban
    systemctl enable fail2ban
    systemctl start fail2ban
fi
log OK "fail2ban (SSH Brute-Force Schutz)"

# Disable root password login (SSH key only)
if grep -q "^PermitRootLogin yes" /etc/ssh/sshd_config 2>/dev/null; then
    log WARN "Root-Login per Passwort ist aktiv!"
    log INFO "Empfehlung: PermitRootLogin prohibit-password in /etc/ssh/sshd_config"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

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
echo -e "${W}║  Services:   CRM, SkyBot, Bombproof, Content-Timer        ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}║  Projekt:    ${PROJECT_DIR}                          ║${N}"
echo -e "${W}║  Logs:       /var/log/aiempire/                           ║${N}"
echo -e "${W}║  .env:       ${PROJECT_DIR}/.env                    ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""
echo -e "  ${W}Naechste Schritte:${N}"
echo -e "  ${C}1.${N} API Keys eintragen: nano ${PROJECT_DIR}/.env"
echo -e "  ${C}2.${N} CRM starten:        systemctl start aiempire-crm"
echo -e "  ${C}3.${N} SkyBot starten:     systemctl start aiempire-skybot"
echo -e "  ${C}4.${N} Runner setup:       bash ${PROJECT_DIR}/scripts/setup_github_runner.sh"
echo -e "  ${C}5.${N} Docker Stack:       cd ${PROJECT_DIR}/systems && docker compose up -d"
echo -e "  ${C}6.${N} Status pruefen:     bash ${PROJECT_DIR}/scripts/bombproof_startup.sh --status"
echo ""
echo -e "  ${G}Setup-Log:${N} ${LOG_FILE}"
echo ""
