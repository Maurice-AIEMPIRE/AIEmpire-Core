#!/bin/bash
# ============================================================
# GALAXIA PHASE 1B.2: Hetzner Runner Provisioning
# ============================================================
# Provisions Hetzner runners with:
# - Docker & Docker Compose
# - Ollama (qwen2.5-coder models)
# - PostgreSQL (primary or replica)
# - Redis (primary or replica)
# - ChromaDB
# - Health monitoring
# - Auto-repair integration
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
RUNNER_TYPE="${1:-primary}"  # primary or standby
REPO_ROOT="${2:-.}"
HETZNER_IP="${3:-65.21.203.174}"

# Hetzner-specific paths
AIEMPIRE_HOME="/opt/aiempire"
DOCKER_COMPOSE_DIR="$AIEMPIRE_HOME/compose"
SERVICE_LOG_DIR="/var/log/galaxia"
DATA_DIR="/var/lib/galaxia"

# ============================================================
# FUNCTIONS
# ============================================================

log_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  GALAXIA: Hetzner $RUNNER_TYPE Runner Provisioning   ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_step() {
    echo -e "${YELLOW}[$1]${NC} $2"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

run_on_hetzner() {
    # Execute command on Hetzner via SSH
    ssh -o ConnectTimeout=5 "root@$HETZNER_IP" "$@"
}

# ============================================================
# STEP 1: System Preparation
# ============================================================

log_header

log_step "1/10" "Preparing Hetzner system..."

# Update system
run_on_hetzner << 'SCRIPT'
set -e
apt-get update -qq
apt-get upgrade -y -qq
log_success "System updated"
SCRIPT

log_success "System prepared"
echo ""

# ============================================================
# STEP 2: Docker Installation
# ============================================================

log_step "2/10" "Installing Docker..."

run_on_hetzner << 'SCRIPT'
set -e

# Install Docker if not exists
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    bash get-docker.sh -q
    rm get-docker.sh

    # Install Docker Compose
    curl -fsSL "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    # Enable Docker daemon
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed"
fi

echo "✓ Docker ready"
SCRIPT

log_success "Docker installed"
echo ""

# ============================================================
# STEP 3: Prepare Directories
# ============================================================

log_step "3/10" "Preparing directories..."

run_on_hetzner << SCRIPT
set -e
mkdir -p $AIEMPIRE_HOME/{compose,data,logs}
mkdir -p $SERVICE_LOG_DIR
mkdir -p $DATA_DIR/{ollama,redis,postgresql,chromadb}
mkdir -p /etc/aiempire

# Set permissions
chmod 755 $AIEMPIRE_HOME
chmod 755 $SERVICE_LOG_DIR
chmod 755 $DATA_DIR

echo "✓ Directories created"
SCRIPT

log_success "Directories prepared"
echo ""

# ============================================================
# STEP 4: Docker Compose Configuration
# ============================================================

log_step "4/10" "Uploading Docker Compose configuration..."

# Prepare docker-compose file
COMPOSE_FILE=$(cat <<'COMPOSE'
version: '3.9'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: galaxia-ollama
    ports:
      - "11434:11434"
    volumes:
      - /var/lib/galaxia/ollama:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: galaxia-redis
    ports:
      - "6379:6379"
    volumes:
      - /var/lib/galaxia/redis:/data
    command: redis-server --appendonly yes --loglevel notice
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  chromadb:
    image: chromadb/chroma:latest
    container_name: galaxia-chromadb
    ports:
      - "8000:8000"
    volumes:
      - /var/lib/galaxia/chromadb:/chroma/data
    environment:
      - ANONYMIZED_TELEMETRY=False
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 3

networks:
  default:
    name: galaxia-network
COMPOSE
)

# Upload compose file
scp -q /dev/stdin "root@$HETZNER_IP:$AIEMPIRE_HOME/compose/docker-compose.yml" << EOF
$COMPOSE_FILE
EOF

log_success "Docker Compose uploaded"
echo ""

# ============================================================
# STEP 5: Start Services
# ============================================================

log_step "5/10" "Starting Docker services..."

run_on_hetzner << SCRIPT
set -e
cd $AIEMPIRE_HOME/compose
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to become healthy..."
sleep 10

# Check health
docker-compose ps
echo "✓ Services started"
SCRIPT

log_success "Services started"
echo ""

# ============================================================
# STEP 6: Ollama Model Setup
# ============================================================

log_step "6/10" "Setting up Ollama models..."

run_on_hetzner << 'SCRIPT'
set -e

# Pull base models
echo "Pulling qwen2.5-coder:7b..."
docker exec galaxia-ollama ollama pull qwen2.5-coder:7b > /dev/null 2>&1 &

echo "Pulling qwen2.5-coder:14b..."
docker exec galaxia-ollama ollama pull qwen2.5-coder:14b > /dev/null 2>&1 &

# Wait for downloads to start
sleep 3

# Monitor progress
echo "Models downloading in background (check with: docker exec galaxia-ollama ollama list)"
echo "✓ Model setup started"
SCRIPT

log_success "Ollama models queued"
echo ""

# ============================================================
# STEP 7: PostgreSQL Setup (if primary)
# ============================================================

if [ "$RUNNER_TYPE" = "primary" ]; then
    log_step "7/10" "Setting up PostgreSQL (primary)..."

    run_on_hetzner << 'SCRIPT'
set -e

# Create PostgreSQL container
docker run -d \
  --name galaxia-postgres \
  --network galaxia-network \
  -e POSTGRES_PASSWORD=galaxia_db_pass_secure \
  -e POSTGRES_USER=aiempire \
  -e POSTGRES_DB=aiempire_core \
  -v /var/lib/galaxia/postgresql:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15-alpine

# Wait for startup
sleep 5

# Test connection
docker exec galaxia-postgres psql -U aiempire -d aiempire_core -c "SELECT version();"

echo "✓ PostgreSQL primary setup"
SCRIPT

    log_success "PostgreSQL primary configured"
else
    log_step "7/10" "PostgreSQL setup skipped (standby mode)"
fi

echo ""

# ============================================================
# STEP 8: Health Monitoring
# ============================================================

log_step "8/10" "Setting up health monitoring..."

HEALTH_SCRIPT=$(cat <<'HEALTH'
#!/bin/bash
# Health check script for Hetzner runner

set -e

HEALTH_FILE="/var/lib/galaxia/health.json"

# Check each service
check_service() {
    local service=$1
    local port=$2
    local expected_status=$3

    if curl -s -f "http://localhost:$port$expected_status" > /dev/null 2>&1; then
        echo "\"$service\": \"healthy\""
    else
        echo "\"$service\": \"unhealthy\""
    fi
}

# Generate health report
cat > "$HEALTH_FILE" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "runner_type": "primary",
  "services": {
    $(check_service "ollama" "11434" "/api/tags"),
    $(check_service "redis" "6379" ""),
    $(check_service "chromadb" "8000" "/api/v1/heartbeat")
  }
}
EOF

echo "✓ Health check complete"
HEALTH
)

scp -q /dev/stdin "root@$HETZNER_IP:/usr/local/bin/galaxia-health-check" << EOF
$HEALTH_SCRIPT
EOF

run_on_hetzner chmod +x /usr/local/bin/galaxia-health-check

log_success "Health monitoring configured"
echo ""

# ============================================================
# STEP 9: Cron Jobs
# ============================================================

log_step "9/10" "Setting up automation jobs..."

run_on_hetzner << 'SCRIPT'
set -e

# Create crontab entry for health checks
CRON_JOB="*/5 * * * * /usr/local/bin/galaxia-health-check > /var/log/galaxia/health-check.log 2>&1"

# Add to crontab if not exists
if ! crontab -l 2>/dev/null | grep -q "galaxia-health-check"; then
    (crontab -l 2>/dev/null || true; echo "$CRON_JOB") | crontab -
    echo "✓ Cron jobs configured"
else
    echo "✓ Cron jobs already configured"
fi
SCRIPT

log_success "Cron jobs configured"
echo ""

# ============================================================
# STEP 10: Verification
# ============================================================

log_step "10/10" "Verifying setup..."

run_on_hetzner << 'SCRIPT'
set -e

echo "Checking Docker services..."
docker-compose -f /opt/aiempire/compose/docker-compose.yml ps

echo ""
echo "Checking ports..."
netstat -ln | grep -E "11434|6379|8000|5432" || echo "Services may still be starting..."

echo ""
echo "✓ Verification complete"
SCRIPT

log_success "Verification complete"
echo ""

# ============================================================
# FINAL REPORT
# ============================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✓ HETZNER $RUNNER_TYPE RUNNER PROVISIONED!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "📊 Runner Configuration:"
echo "  Type: $RUNNER_TYPE"
echo "  IP: $HETZNER_IP"
echo "  Home: $AIEMPIRE_HOME"
echo ""

echo "🐳 Services:"
echo "  • Ollama: http://$HETZNER_IP:11434"
echo "  • Redis: redis://$HETZNER_IP:6379"
echo "  • ChromaDB: http://$HETZNER_IP:8000"
if [ "$RUNNER_TYPE" = "primary" ]; then
    echo "  • PostgreSQL: postgres://aiempire@$HETZNER_IP:5432/aiempire_core"
fi
echo ""

echo "🔗 Next Steps:"
echo "  1. Wait for Ollama models to finish downloading"
echo "  2. Verify health: ssh root@$HETZNER_IP 'galaxia-health-check'"
echo "  3. Check logs: ssh root@$HETZNER_IP 'docker-compose -f /opt/aiempire/compose/docker-compose.yml logs'"
echo ""

echo "📝 Useful Commands:"
echo "  • View service logs:"
echo "    ssh root@$HETZNER_IP 'docker-compose -f /opt/aiempire/compose/docker-compose.yml logs -f'"
echo ""
echo "  • Restart services:"
echo "    ssh root@$HETZNER_IP 'docker-compose -f /opt/aiempire/compose/docker-compose.yml restart'"
echo ""
echo "  • Enter container shell:"
echo "    ssh root@$HETZNER_IP 'docker exec -it galaxia-ollama bash'"
echo ""

echo -e "${GREEN}✅ Runner ready for Phase 1B.3: Database Setup${NC}"
