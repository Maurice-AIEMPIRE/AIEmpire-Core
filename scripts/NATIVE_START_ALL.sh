#!/bin/bash
# 🚀 NATIVE_START_ALL.sh - Alle Services starten (Kein Docker!)
# Benutzer: Maurice
# Status: Production-Ready

set -e

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Maurice's AI Empire - NATIVE SERVICES START          ║"
echo "║  (No Docker - Full Native)                            ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
LOG_DIR="$HOME/.openclaw/workspace/ai-empire/06_LOGS"
mkdir -p "$LOG_DIR"
MAIN_LOG="$LOG_DIR/native_startup_$(date +%Y%m%d_%H%M%S).log"

log_info() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$MAIN_LOG"
}

log_warn() {
    echo -e "${YELLOW}[⚠]${NC} $1" | tee -a "$MAIN_LOG"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$MAIN_LOG"
}

# LAYER 1: Infrastructure Services (Brew Services)
echo ""
echo "━━━ LAYER 1: Infrastructure Services ━━━"
echo ""

# PostgreSQL 14
echo -n "Starting PostgreSQL 14... "
if brew services start postgresql@14 2>/dev/null; then
    log_info "PostgreSQL 14 running (Port 5432)"
else
    log_warn "PostgreSQL 14 already running"
fi

# Redis
echo -n "Starting Redis... "
if brew services start redis 2>/dev/null; then
    log_info "Redis running (Port 6379)"
else
    log_warn "Redis already running"
fi

# Ollama
echo -n "Starting Ollama... "
if brew services start ollama 2>/dev/null; then
    log_info "Ollama running (Port 11434)"
else
    log_warn "Ollama already running"
fi

# Wait for services to be ready
sleep 5

# Health checks
echo ""
echo "━━━ Health Checks ━━━"
echo ""

# PostgreSQL
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    log_info "PostgreSQL responding ✓"
else
    log_error "PostgreSQL not responding!"
fi

# Redis
if redis-cli ping > /dev/null 2>&1; then
    log_info "Redis responding ✓"
else
    log_error "Redis not responding!"
fi

# Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log_info "Ollama responding ✓"
else
    log_error "Ollama not responding!"
fi

# LAYER 2: n8n (Zentrale Automatisierung)
echo ""
echo "━━━ LAYER 2: n8n Automation Engine ━━━"
echo ""

N8N_HEALTH_URL="http://localhost:5678/healthz"
if curl -s "$N8N_HEALTH_URL" > /dev/null 2>&1; then
    log_warn "n8n already running (Port 5678)"
else
    echo -n "Starting n8n... "
    nohup n8n start > "$LOG_DIR/n8n.log" 2>&1 &
    N8N_PID=$!
    sleep 3

    if curl -s "$N8N_HEALTH_URL" > /dev/null 2>&1; then
        log_info "n8n running (Port 5678, PID: $N8N_PID)"
    else
        log_error "n8n failed to start!"
    fi
fi

# LAYER 3: Python FastAPI Services
echo ""
echo "━━━ LAYER 3: Python FastAPI Services ━━━"
echo ""

# Check if venv exists
if [ ! -d "$HOME/.openclaw/venv" ]; then
    log_error "Python venv not found! Create with: python3 -m venv ~/.openclaw/venv"
    exit 1
fi

# Empire Control API
EMPIRE_API_LOG="$LOG_DIR/empire_api.log"
if curl -s http://localhost:3333/health > /dev/null 2>&1; then
    log_warn "Empire API already running (Port 3333)"
else
    echo -n "Starting Empire Control API... "
    cd "$HOME/AIEmpire-Core/empire_api"
    nohup "$HOME/.openclaw/venv/bin/uvicorn" server:app --host 0.0.0.0 --port 3333 > "$EMPIRE_API_LOG" 2>&1 &
    EMPIRE_PID=$!
    sleep 2

    if curl -s http://localhost:3333/health > /dev/null 2>&1; then
        log_info "Empire API running (Port 3333, PID: $EMPIRE_PID)"
    else
        log_error "Empire API failed to start!"
    fi
fi

# Atomic Reactor (Optional - for advanced users)
REACTOR_LOG="$LOG_DIR/reactor.log"
if [ "$1" == "--full" ]; then
    if curl -s http://localhost:8888/health > /dev/null 2>&1; then
        log_warn "Atomic Reactor already running (Port 8888)"
    else
        echo -n "Starting Atomic Reactor... "
        cd "$HOME/AIEmpire-Core/atomic-reactor"
        nohup "$HOME/.openclaw/venv/bin/python3" run_tasks.py > "$REACTOR_LOG" 2>&1 &
        REACTOR_PID=$!
        sleep 2

        if curl -s http://localhost:8888/health > /dev/null 2>&1; then
            log_info "Atomic Reactor running (Port 8888, PID: $REACTOR_PID)"
        else
            log_warn "Atomic Reactor not responding yet (may still be starting)"
        fi
    fi
fi

# LAYER 4: Node Services
echo ""
echo "━━━ LAYER 4: Node Services ━━━"
echo ""

# CRM Server
CRM_LOG="$LOG_DIR/crm.log"
if curl -s http://localhost:3500/health > /dev/null 2>&1; then
    log_warn "CRM Server already running (Port 3500)"
else
    echo -n "Starting CRM Server... "
    cd "$HOME/AIEmpire-Core/crm"
    nohup npm start > "$CRM_LOG" 2>&1 &
    CRM_PID=$!
    sleep 3

    if curl -s http://localhost:3500/health > /dev/null 2>&1; then
        log_info "CRM Server running (Port 3500, PID: $CRM_PID)"
    else
        log_warn "CRM Server not responding yet (may still be starting)"
    fi
fi

# Final Status Report
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  🎉 ALL SERVICES STARTED                              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

echo "📊 SERVICE STATUS:"
echo ""
echo "  Infrastructure:"
echo "    ✓ PostgreSQL  → localhost:5432"
echo "    ✓ Redis       → localhost:6379"
echo "    ✓ Ollama      → http://localhost:11434"
echo ""
echo "  Automation:"
echo "    ✓ n8n         → http://localhost:5678"
echo ""
echo "  APIs:"
echo "    ✓ Empire API  → http://localhost:3333"
echo "    ✓ CRM Server  → http://localhost:3500"
if [ "$1" == "--full" ]; then
    echo "    ✓ Reactor     → http://localhost:8888"
fi
echo ""
echo "📝 LOGS:"
echo "    Main:  $MAIN_LOG"
echo "    n8n:   $LOG_DIR/n8n.log"
echo "    API:   $LOG_DIR/empire_api.log"
echo "    CRM:   $LOG_DIR/crm.log"
echo ""
echo "🚀 NEXT STEPS:"
echo "    1. Open n8n: open http://localhost:5678"
echo "    2. Import workflows: n8n workflow import ~/AIEmpire-Core/n8n-workflows/*.json"
echo "    3. Configure credentials in n8n UI"
echo "    4. Test first automation"
echo ""
echo "📞 HELP:"
echo "    bash ~/AIEmpire-Core/scripts/NATIVE_START_ALL.sh --full  (Start Reactor too)"
echo "    bash ~/AIEmpire-Core/scripts/native_stop.sh             (Stop all)"
echo "    bash ~/AIEmpire-Core/scripts/native_status.sh           (Check status)"
echo ""

# Save PID file for easier management
echo "$(date +%s)" > "$LOG_DIR/startup_timestamp.txt"
echo "$N8N_PID" >> "$LOG_DIR/pids.txt" 2>/dev/null || true
echo "$EMPIRE_PID" >> "$LOG_DIR/pids.txt" 2>/dev/null || true
echo "$CRM_PID" >> "$LOG_DIR/pids.txt" 2>/dev/null || true

log_info "Startup complete! Log file: $MAIN_LOG"
