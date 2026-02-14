#!/bin/bash

# ══════════════════════════════════════════════════════════════════════════════
# AIEmpire-Core - Service Status Checker
# Quick overview of all service status
# ══════════════════════════════════════════════════════════════════════════════

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to check if port is listening
check_port() {
    local port=$1
    if netstat -tuln 2>/dev/null | grep ":$port " &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to get process info
get_process_info() {
    local port=$1
    lsof -i ":$port" 2>/dev/null | grep -v "COMMAND" | awk '{print $1 " (" $9 ")"}' | head -1
}

# Function to print status
print_status() {
    local service=$1
    local port=$2
    local url=$3

    printf "%-25s " "$service"

    if check_port "$port"; then
        echo -ne "${GREEN}✅ UP${NC}"
        printf " (%-30s)" "Port $port"
        if [ -n "$url" ]; then
            echo -e "  ${CYAN}→ $url${NC}"
        else
            echo ""
        fi
    else
        echo -ne "${RED}❌ DOWN${NC}"
        printf " (%-30s)" "Port $port"
        echo ""
    fi
}

# Clear and show header
clear
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║      📊 AIEmpire-Core Service Status Monitor 📊              ║"
echo "║              $(date '+%Y-%m-%d %H:%M:%S')                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Infrastructure Layer
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 Infrastructure Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
print_status "Ollama" "11434" "http://localhost:11434"
print_status "Redis" "6379" "redis-cli"
print_status "PostgreSQL" "5432" "psql"
print_status "Docker" "2375" "docker ps"
echo ""

# Automation Layer
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🤖 Automation & Middleware${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
print_status "n8n" "5678" "http://localhost:5678"
print_status "OpenClaw" "18789" "http://localhost:18789"
echo ""

# Application Layer
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Application Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
print_status "CRM" "3500" "http://localhost:3500"
print_status "Atomic Reactor" "8888" "http://localhost:8888"
echo ""

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
UP_COUNT=$(netstat -tuln 2>/dev/null | grep -E ":(11434|6379|5432|2375|5678|18789|3500|8888) " | wc -l)
echo -e "${CYAN}Summary:${NC} $UP_COUNT/8 services running"
echo ""

# Quick commands reference
echo -e "${YELLOW}Quick Commands:${NC}"
echo "  scripts/start_all_services.sh    → Start all services"
echo "  scripts/stop_all_services.sh     → Stop all services"
echo "  scripts/check_status.sh          → Check this status (refreshes every 2 sec with 'watch')"
echo ""
echo "  watch -n 2 scripts/check_status.sh → Auto-refresh status every 2 seconds"
echo ""
