#!/bin/bash

# ══════════════════════════════════════════════════════════════════════════════
# AIEmpire-Core - Graceful Service Shutdown Script
# Stops all services in reverse dependency order
# ══════════════════════════════════════════════════════════════════════════════

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Helper Functions
print_header() {
    clear
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     🛑 AIEmpire-Core Service Shutdown Manager 🛑          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

check_port() {
    local port=$1
    netstat -tuln 2>/dev/null | grep ":$port " &>/dev/null
}

check_command() {
    command -v "$1" &>/dev/null
}

stop_service() {
    local service=$1
    local port=$2
    local brew_name=$3

    echo -ne "  ⏳ Stopping $service... "

    if ! check_port "$port"; then
        echo -e "${YELLOW}⚠️  Not running${NC}"
        return 0
    fi

    if [ -n "$brew_name" ] && check_command brew; then
        brew services stop "$brew_name" 2>/dev/null
        sleep 1
        if ! check_port "$port"; then
            echo -e "${GREEN}✅ Stopped${NC}"
            return 0
        fi
    fi

    # Generic port killing
    lsof -ti ":$port" 2>/dev/null | xargs -r kill -9 2>/dev/null
    sleep 1

    if ! check_port "$port"; then
        echo -e "${GREEN}✅ Stopped${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to stop${NC}"
        return 1
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Main Shutdown Sequence
# ─────────────────────────────────────────────────────────────────────────────

print_header

print_section "🛑 Shutting Down Services (reverse dependency order)..."

# Layer 4: Application Services (shutdown first)
echo -e "${CYAN}[Layer 4] Application Services${NC}"
stop_service "CRM" "3500" ""
stop_service "Atomic Reactor" "8888" ""

# Layer 3: AI & Automation
echo ""
echo -e "${CYAN}[Layer 3] AI & Automation Services${NC}"
stop_service "n8n" "5678" "n8n"
stop_service "Ollama" "11434" "ollama"
stop_service "OpenClaw" "18789" ""

# Layer 2: Container & Orchestration
echo ""
echo -e "${CYAN}[Layer 2] Container & Orchestration${NC}"
echo -ne "  ⏳ Stopping Docker... "
if check_command docker; then
    killall Docker 2>/dev/null || pkill -f Docker 2>/dev/null
    sleep 2
    echo -e "${GREEN}✅ Stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Not installed${NC}"
fi

# Layer 1: Core Infrastructure (shutdown last)
echo ""
echo -e "${CYAN}[Layer 1] Core Infrastructure${NC}"
stop_service "PostgreSQL" "5432" "postgresql@16"
stop_service "Redis" "6379" "redis"

# ─────────────────────────────────────────────────────────────────────────────
# Final Status Report
# ─────────────────────────────────────────────────────────────────────────────

print_section "✨ Shutdown Complete"

echo ""
echo -e "  ${GREEN}All services have been gracefully shut down.${NC}"
echo ""
echo "  💡 Tip: Run 'scripts/check_status.sh' to verify all services are stopped"
echo ""
