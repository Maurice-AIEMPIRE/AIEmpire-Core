#!/bin/bash

# ══════════════════════════════════════════════════════════════════════════════
# AIEmpire-Core - Comprehensive Service Startup Script
# Starts all required services in correct dependency order
# macOS with Homebrew compatible
# ══════════════════════════════════════════════════════════════════════════════

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Service status tracking
declare -A SERVICE_STATUS

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

print_header() {
    clear
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     🚀 AIEmpire-Core Service Startup Manager 🚀           ║"
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
    # macOS-friendly check first
    if command -v lsof >/dev/null 2>&1; then
        lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
        return $?
    fi

    # Fallback for Linux/other environments
    if command -v netstat >/dev/null 2>&1; then
        netstat -an 2>/dev/null | grep -E "[\.\:]$port .*LISTEN" >/dev/null 2>&1
        return $?
    fi

    return 1
}

check_command() {
    command -v "$1" &>/dev/null
}

start_service() {
    local service=$1
    local port=$2
    local brew_name=$3
    local command=$4

    echo -ne "  ⏳ Starting $service... "

    if check_port "$port"; then
        echo -e "${GREEN}✅ Already running (port $port)${NC}"
        SERVICE_STATUS[$service]="UP"
        return 0
    fi

    if [ -n "$brew_name" ]; then
        if ! check_command brew; then
            echo -e "${YELLOW}⚠️  Homebrew not installed${NC}"
            SERVICE_STATUS[$service]="NOT_INSTALLED"
            return 1
        fi

        if ! brew list "$brew_name" >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Not installed${NC}"
            SERVICE_STATUS[$service]="NOT_INSTALLED"
            return 1
        fi

        brew services start "$brew_name" 2>/dev/null
        sleep 2

        if check_port "$port"; then
            echo -e "${GREEN}✅ Started${NC}"
            SERVICE_STATUS[$service]="UP"
            return 0
        else
            echo -e "${RED}❌ Failed to start${NC}"
            SERVICE_STATUS[$service]="DOWN"
            return 1
        fi
    elif [ -n "$command" ]; then
        eval "$command" 2>/dev/null &
        sleep 3

        if check_port "$port"; then
            echo -e "${GREEN}✅ Started${NC}"
            SERVICE_STATUS[$service]="UP"
            return 0
        else
            echo -e "${RED}❌ Failed to start${NC}"
            SERVICE_STATUS[$service]="DOWN"
            return 1
        fi
    fi
}

check_service_status() {
    local service=$1
    local port=$2

    if check_port "$port"; then
        SERVICE_STATUS[$service]="UP"
        echo -e "${GREEN}✅${NC}"
    else
        SERVICE_STATUS[$service]="DOWN"
        echo -e "${RED}❌${NC}"
    fi
}

print_status_line() {
    local service=$1
    local port=$2
    local status=${SERVICE_STATUS[$service]}

    printf "  %-20s (port %-5s) " "$service:" "$port"

    case $status in
        "UP")
            echo -e "${GREEN}✅ UP${NC}"
            ;;
        "DOWN")
            echo -e "${RED}❌ DOWN${NC}"
            ;;
        "NOT_INSTALLED")
            echo -e "${YELLOW}⚠️  NOT INSTALLED${NC}"
            ;;
        *)
            echo -e "${YELLOW}? UNKNOWN${NC}"
            ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────────────
# Main Startup Sequence
# ─────────────────────────────────────────────────────────────────────────────

print_header

print_section "🔍 Checking current service status..."

check_service_status "Ollama" "11434"
check_service_status "Redis" "6379"
check_service_status "PostgreSQL" "5432"
check_service_status "Docker" "2375"
check_service_status "n8n" "5678"
check_service_status "OpenClaw" "18789"
check_service_status "CRM" "3500"
check_service_status "Atomic Reactor" "8888"

print_section "🚀 Starting Services (dependency order)..."

# Layer 1: Core Infrastructure
echo -e "${CYAN}[Layer 1] Core Infrastructure${NC}"
start_service "Redis" "6379" "redis" ""
start_service "PostgreSQL" "5432" "postgresql@16" ""

# Layer 2: Container & Orchestration
echo ""
echo -e "${CYAN}[Layer 2] Container & Orchestration${NC}"
if check_command docker; then
    echo -ne "  ⏳ Starting Docker... "
    open -a Docker 2>/dev/null || docker --version &>/dev/null
    sleep 5
    if check_port "2375"; then
        echo -e "${GREEN}✅ Started${NC}"
        SERVICE_STATUS["Docker"]="UP"
    else
        echo -e "${YELLOW}⚠️  Not responding on standard port${NC}"
        SERVICE_STATUS["Docker"]="UP"
    fi
else
    echo -e "  ${YELLOW}⚠️  Docker not installed${NC}"
    SERVICE_STATUS["Docker"]="NOT_INSTALLED"
fi

# Layer 3: AI & Automation
echo ""
echo -e "${CYAN}[Layer 3] AI & Automation Services${NC}"
start_service "Ollama" "11434" "ollama" "ollama serve"

# Check if n8n should be started (optional)
if check_command n8n; then
    echo -ne "  ⏳ Starting n8n... "
    n8n start --skip-webhook-validation 2>/dev/null &
    sleep 4
    if check_port "5678"; then
        echo -e "${GREEN}✅ Started${NC}"
        SERVICE_STATUS["n8n"]="UP"
    else
        echo -e "${YELLOW}⚠️  Not responding${NC}"
        SERVICE_STATUS["n8n"]="DOWN"
    fi
else
    SERVICE_STATUS["n8n"]="NOT_INSTALLED"
fi

# Layer 4: Application Services
echo ""
echo -e "${CYAN}[Layer 4] Application Services${NC}"

# OpenClaw check
echo -ne "  ⏳ Checking OpenClaw... "
if check_port "18789"; then
    echo -e "${GREEN}✅ Already running${NC}"
    SERVICE_STATUS["OpenClaw"]="UP"
else
    echo -e "${YELLOW}⚠️  Not running (manual start may be required)${NC}"
    SERVICE_STATUS["OpenClaw"]="DOWN"
fi

# CRM Server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CRM_DIR="$PROJECT_DIR/crm"

if [ -d "$CRM_DIR" ]; then
    echo -ne "  ⏳ Starting CRM Server... "
    cd "$CRM_DIR"
    npm start 2>/dev/null &
    sleep 3
    if check_port "3500"; then
        echo -e "${GREEN}✅ Started${NC}"
        SERVICE_STATUS["CRM"]="UP"
    else
        echo -e "${YELLOW}⚠️  Failed to start${NC}"
        SERVICE_STATUS["CRM"]="DOWN"
    fi
    cd - &>/dev/null
else
    echo -e "  ${YELLOW}⚠️  CRM directory not found${NC}"
    SERVICE_STATUS["CRM"]="NOT_FOUND"
fi

# Atomic Reactor (FastAPI)
REACTOR_DIR="$PROJECT_DIR/atomic-reactor"
if [ -d "$REACTOR_DIR" ]; then
    echo -ne "  ⏳ Starting Atomic Reactor (FastAPI)... "
    cd "$REACTOR_DIR"
    if [ -f "requirements.txt" ]; then
        python3 -m uvicorn main:app --host 0.0.0.0 --port 8888 2>/dev/null &
        sleep 3
        if check_port "8888"; then
            echo -e "${GREEN}✅ Started${NC}"
            SERVICE_STATUS["Atomic Reactor"]="UP"
        else
            echo -e "${YELLOW}⚠️  Failed to start${NC}"
            SERVICE_STATUS["Atomic Reactor"]="DOWN"
        fi
    else
        echo -e "${YELLOW}⚠️  requirements.txt not found${NC}"
        SERVICE_STATUS["Atomic Reactor"]="NOT_FOUND"
    fi
    cd - &>/dev/null
else
    echo -e "  ${YELLOW}⚠️  Atomic Reactor directory not found${NC}"
    SERVICE_STATUS["Atomic Reactor"]="NOT_FOUND"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Final Status Report
# ─────────────────────────────────────────────────────────────────────────────

print_section "📊 Final Service Status Report"

echo -e "  ${CYAN}Infrastructure Services:${NC}"
print_status_line "Ollama" "11434"
print_status_line "Redis" "6379"
print_status_line "PostgreSQL" "5432"
print_status_line "Docker" "2375"

echo ""
echo -e "  ${CYAN}Automation & Middleware:${NC}"
print_status_line "n8n" "5678"
print_status_line "OpenClaw" "18789"

echo ""
echo -e "  ${CYAN}Application Services:${NC}"
print_status_line "CRM" "3500"
print_status_line "Atomic Reactor" "8888"

# Count services
UP_COUNT=0
DOWN_COUNT=0
for service in "${!SERVICE_STATUS[@]}"; do
    if [ "${SERVICE_STATUS[$service]}" = "UP" ]; then
        ((UP_COUNT++))
    elif [ "${SERVICE_STATUS[$service]}" = "DOWN" ]; then
        ((DOWN_COUNT++))
    fi
done

echo ""
print_section "✨ Startup Complete"

echo -e "  ${GREEN}Services UP: $UP_COUNT${NC}"
echo -e "  ${RED}Services DOWN: $DOWN_COUNT${NC}"
echo ""

if [ $UP_COUNT -ge 5 ]; then
    echo -e "  ${GREEN}🎉 AIEmpire-Core is ready for operations!${NC}"
else
    echo -e "  ${YELLOW}⚠️  Some services may need manual attention${NC}"
fi

echo ""
echo "  Run 'scripts/check_status.sh' anytime to check service status"
echo "  Run 'scripts/stop_all_services.sh' to gracefully shut down services"
echo ""
