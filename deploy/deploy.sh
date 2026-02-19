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

# ─── Pull Ollama Models ──────────────────────────────────
cmd_ollama_pull() {
    log "Pulling Ollama models for 64GB RAM server..."

    local models=(
        "qwen2.5-coder:14b"
        "qwen2.5-coder:7b"
        "deepseek-r1:7b"
    )

    for model in "${models[@]}"; do
        log "Pulling $model..."
        docker exec ollama ollama pull "$model" || warn "Failed to pull $model"
    done

    log "Models installed:"
    docker exec ollama ollama list
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

# ─── Main ────────────────────────────────────────────────
case "${1:-help}" in
    setup)      cmd_setup ;;
    start)      cmd_start ;;
    stop)       cmd_stop ;;
    update)     cmd_update ;;
    status)     cmd_status ;;
    logs)       cmd_logs "${2:-}" ;;
    ollama-pull) cmd_ollama_pull ;;
    backup)     cmd_backup ;;
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
        echo "  setup        First-time server setup (Docker, firewall, sysctl)"
        echo "  start        Start all services"
        echo "  stop         Stop all services"
        echo "  restart      Stop + Start"
        echo "  update       Git pull + rebuild containers"
        echo "  status       Show service health + system resources"
        echo "  logs [svc]   Tail logs (all or specific service)"
        echo "  ollama-pull  Download Ollama models (qwen, deepseek)"
        echo "  backup       Backup Redis + ChromaDB + configs"
        ;;
esac
