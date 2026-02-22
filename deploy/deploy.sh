#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# AI EMPIRE - VPS Deployment Script
# Target: Hetzner Auction Server (i7-6700, 64GB RAM, 2x512GB NVMe)
# Usage: ./deploy.sh [setup|start|stop|update|status|logs|backup|ollama-pull]
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
ENV_FILE="$SCRIPT_DIR/.env"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[EMPIRE]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ─── Setup: Install Docker, configure system ────────────────
cmd_setup() {
    log "Setting up AI Empire on VPS..."

    # Update system
    log "Updating system packages..."
    apt-get update && apt-get upgrade -y

    # Install essentials
    apt-get install -y \
        curl wget git htop tmux vim \
        ca-certificates gnupg lsb-release \
        python3 python3-pip python3-venv

    # Install Docker
    if ! command -v docker &>/dev/null; then
        log "Installing Docker..."
        curl -fsSL https://get.docker.com | sh
        systemctl enable docker
        systemctl start docker
        log "Docker installed."
    else
        log "Docker already installed."
    fi

    # Install Docker Compose plugin
    if ! docker compose version &>/dev/null; then
        log "Installing Docker Compose plugin..."
        apt-get install -y docker-compose-plugin
    fi

    # Configure system limits for 64GB RAM server
    log "Configuring system limits..."
    cat > /etc/sysctl.d/99-empire.conf << 'SYSCTL'
# AI Empire - Optimized for 64GB RAM server
vm.overcommit_memory=1
vm.swappiness=10
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535
fs.file-max=1000000
SYSCTL
    sysctl -p /etc/sysctl.d/99-empire.conf 2>/dev/null || true

    # Create .env from template if not exists
    if [ ! -f "$ENV_FILE" ]; then
        cp "$SCRIPT_DIR/.env.template" "$ENV_FILE"
        warn ".env created from template - EDIT IT with your API keys!"
        warn "Run: nano $ENV_FILE"
    fi

    # Create backup directory
    mkdir -p /mnt/backup/empire

    # Setup firewall
    log "Configuring UFW firewall..."
    if command -v ufw &>/dev/null; then
        ufw allow 22/tcp    # SSH
        ufw allow 80/tcp    # HTTP
        ufw allow 443/tcp   # HTTPS
        ufw --force enable
    fi

    log "Setup complete! Next steps:"
    echo "  1. Edit $ENV_FILE with your API keys"
    echo "  2. Run: ./deploy.sh start"
    echo "  3. Run: ./deploy.sh ollama-pull"
}

# ─── Start all services ────────────────────────────────────
cmd_start() {
    log "Starting AI Empire stack..."
    if [ ! -f "$ENV_FILE" ]; then
        err ".env file not found! Run: ./deploy.sh setup"
        exit 1
    fi
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    log "Stack started. Checking health..."
    sleep 10
    cmd_status
}

# ─── Stop all services ────────────────────────────────────
cmd_stop() {
    log "Stopping AI Empire stack..."
    docker compose -f "$COMPOSE_FILE" down
    log "Stack stopped."
}

# ─── Update (git pull + rebuild) ──────────────────────────
cmd_update() {
    log "Updating AI Empire..."
    cd "$PROJECT_DIR"
    git pull origin main
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    log "Update complete."
    cmd_status
}

# ─── Status ───────────────────────────────────────────────
cmd_status() {
    echo -e "\n${CYAN}═══ AI EMPIRE STATUS ═══${NC}\n"

    # Docker containers
    docker compose -f "$COMPOSE_FILE" ps

    echo ""

    # Health checks
    echo -e "${CYAN}── Service Health ──${NC}"
    for svc in "Ollama:11434/api/tags" "LiteLLM:4000/health" "Redis:6379" "ChromaDB:8000/api/v1/heartbeat" "AntProtocol:8900/health" "Skybot:8901/health" "Grafana:3000/api/health"; do
        name="${svc%%:*}"
        endpoint="${svc#*:}"
        port="${endpoint%%/*}"
        path="/${endpoint#*/}"
        [ "$path" = "/$port" ] && path=""

        if curl -sf "http://localhost:${port}${path}" >/dev/null 2>&1; then
            echo -e "  ${GREEN}OK${NC}  $name (port $port)"
        else
            echo -e "  ${RED}--${NC}  $name (port $port)"
        fi
    done

    # System resources
    echo -e "\n${CYAN}── System Resources ──${NC}"
    echo "  RAM: $(free -h | awk '/^Mem:/{print $3"/"$2}')"
    echo "  Disk: $(df -h / | awk 'NR==2{print $3"/"$2" ("$5")"}')"
    echo "  CPU: $(nproc) cores, load: $(uptime | awk -F'load average:' '{print $2}')"
    echo ""
}

# ─── Logs ─────────────────────────────────────────────────
cmd_logs() {
    local service="${1:-}"
    if [ -n "$service" ]; then
        docker compose -f "$COMPOSE_FILE" logs -f --tail=100 "$service"
    else
        docker compose -f "$COMPOSE_FILE" logs -f --tail=50
    fi
}

# ─── Pull Ollama Models (uses native Ollama, not Docker) ─
cmd_ollama_pull() {
    log "Pulling Ollama models (native Ollama on host)..."

    if ! command -v ollama &>/dev/null; then
        err "ollama not found. Install from: curl -fsSL https://ollama.com/install.sh | sh"
        return 1
    fi

    local models=(
        "qwen2.5-coder:14b"
        "qwen2.5-coder:7b"
        "deepseek-r1:7b"
    )

    for model in "${models[@]}"; do
        log "Pulling $model..."
        ollama pull "$model" || warn "Failed to pull $model"
    done

    log "Models installed:"
    ollama list
}

# ─── Backup ──────────────────────────────────────────────
cmd_backup() {
    local backup_dir="/mnt/backup/empire/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    log "Backing up to $backup_dir..."

    # Dump Redis
    docker exec redis redis-cli BGSAVE >/dev/null 2>&1
    sleep 2
    docker cp redis:/data/dump.rdb "$backup_dir/redis-dump.rdb" 2>/dev/null || warn "Redis backup skipped"

    # Backup ChromaDB data
    docker cp chromadb:/chroma/chroma "$backup_dir/chromadb/" 2>/dev/null || warn "ChromaDB backup skipped"

    # Backup config
    cp -r "$SCRIPT_DIR/.env" "$backup_dir/" 2>/dev/null || true
    cp -r "$PROJECT_DIR/openclaw-config" "$backup_dir/" 2>/dev/null || true

    # Compress
    tar czf "$backup_dir.tar.gz" -C "$(dirname "$backup_dir")" "$(basename "$backup_dir")"
    rm -rf "$backup_dir"

    log "Backup saved: $backup_dir.tar.gz"

    # Cleanup old backups (keep 30 days)
    find /mnt/backup/empire -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true
}

# ─── Full Deploy (one command does everything) ────────────
cmd_full_deploy() {
    log "FULL DEPLOY - Ollama-First Mode (zero cloud cost)"
    echo ""

    # 1. Create .env if missing
    if [ ! -f "$ENV_FILE" ]; then
        cp "$SCRIPT_DIR/.env.template" "$ENV_FILE"
        log "Created .env from template (Ollama-first defaults)"
    else
        log ".env exists, keeping current config"
    fi

    # 2. Start the stack
    log "Starting Docker stack..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    log "Stack starting..."

    # 3. Check native Ollama is running
    log "Checking native Ollama (must be running on host)..."
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        log "Native Ollama is ready!"
    else
        warn "Ollama not detected on port 11434."
        warn "Start it with: ollama serve &"
        warn "Install from: curl -fsSL https://ollama.com/install.sh | sh"
    fi

    # 4. Pull Ollama models
    log "Pulling AI models via native Ollama..."
    cmd_ollama_pull

    # 5. Wait for all services
    log "Waiting for services to stabilize..."
    sleep 10

    # 6. Status report
    cmd_status

    echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  FULL DEPLOY COMPLETE - Ollama-First Mode            ${NC}"
    echo -e "${GREEN}  All services running on LOCAL Ollama models (FREE)  ${NC}"
    echo -e "${GREEN}  Add GEMINI_API_KEY to .env for cloud fallback       ${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
}

# ─── Validate deployment ─────────────────────────────────
cmd_validate() {
    echo -e "\n${CYAN}=== DEPLOYMENT VALIDATION ===${NC}\n"
    local errors=0

    # Check .env
    if [ -f "$ENV_FILE" ]; then
        echo -e "  ${GREEN}OK${NC}  .env file exists"
    else
        echo -e "  ${RED}FAIL${NC}  .env file missing"
        errors=$((errors + 1))
    fi

    # Check Docker
    if docker compose version >/dev/null 2>&1; then
        echo -e "  ${GREEN}OK${NC}  Docker Compose available"
    else
        echo -e "  ${RED}FAIL${NC}  Docker Compose not found"
        errors=$((errors + 1))
    fi

    # Check containers running
    local running
    running=$(docker compose -f "$COMPOSE_FILE" ps --status running -q 2>/dev/null | wc -l)
    echo -e "  ${CYAN}INFO${NC}  $running containers running"

    # Check native Ollama
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "  ${GREEN}OK${NC}  Native Ollama responding (port 11434)"
        if command -v ollama &>/dev/null; then
            local models
            models=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
            echo -e "  ${CYAN}INFO${NC}  $models Ollama models installed"
        fi
    else
        echo -e "  ${YELLOW}WARN${NC}  Ollama not responding (start with: ollama serve)"
    fi

    # Check native OpenClaw
    if curl -sf http://127.0.0.1:18789/health >/dev/null 2>&1; then
        echo -e "  ${GREEN}OK${NC}  OpenClaw gateway healthy (port 18789)"
    else
        echo -e "  ${YELLOW}WARN${NC}  OpenClaw not responding (run: openclaw gateway &)"
    fi

    # Check LiteLLM
    if curl -sf http://localhost:4000/health >/dev/null 2>&1; then
        echo -e "  ${GREEN}OK${NC}  LiteLLM proxy healthy"
    else
        echo -e "  ${YELLOW}WARN${NC}  LiteLLM not responding"
    fi

    # Check Redis
    if docker exec redis redis-cli ping >/dev/null 2>&1; then
        echo -e "  ${GREEN}OK${NC}  Redis responding"
    else
        echo -e "  ${YELLOW}WARN${NC}  Redis not responding"
    fi

    # Check Ant Protocol
    if curl -sf http://localhost:8900/health >/dev/null 2>&1; then
        echo -e "  ${GREEN}OK${NC}  Ant Protocol API healthy"
    else
        echo -e "  ${YELLOW}WARN${NC}  Ant Protocol not responding"
    fi

    echo ""
    if [ $errors -eq 0 ]; then
        echo -e "  ${GREEN}RESULT: All critical checks passed${NC}"
    else
        echo -e "  ${RED}RESULT: $errors critical issues found${NC}"
    fi
    echo ""
}

# ─── Configure OpenClaw for Tailscale/iPhone access ──────
cmd_configure_access() {
    log "Configuring OpenClaw for Tailscale access (Mac + iPhone)..."
    bash "$SCRIPT_DIR/configure_openclaw_access.sh"
}

# ─── Main ────────────────────────────────────────────────
case "${1:-help}" in
    setup)            cmd_setup ;;
    start)            cmd_start ;;
    stop)             cmd_stop ;;
    update)           cmd_update ;;
    status)           cmd_status ;;
    logs)             cmd_logs "${2:-}" ;;
    ollama-pull)      cmd_ollama_pull ;;
    backup)           cmd_backup ;;
    full-deploy)      cmd_full_deploy ;;
    validate)         cmd_validate ;;
    configure-access) cmd_configure_access ;;
    restart)
        cmd_stop
        cmd_start
        ;;
    *)
        echo "AI Empire VPS Deployment"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  full-deploy       One-command: start + pull models + validate (recommended)"
        echo "  configure-access  Configure OpenClaw for Tailscale (Mac + iPhone access)"
        echo "  setup             First-time server setup (Docker, firewall, sysctl)"
        echo "  start             Start Docker services"
        echo "  stop              Stop Docker services"
        echo "  restart           Stop + Start"
        echo "  update            Git pull + rebuild containers"
        echo "  status            Show service health + system resources"
        echo "  validate          Run deployment validation checks"
        echo "  logs [svc]        Tail logs (all or specific service)"
        echo "  ollama-pull       Download Ollama models (qwen, deepseek)"
        echo "  backup            Backup Redis + ChromaDB + configs"
        ;;
esac
