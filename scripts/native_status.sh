#!/bin/bash
# 📊 native_status.sh - Status aller Services

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Maurice's AI Empire - SERVICE STATUS                 ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Farben
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local name=$1
    local port=$2
    local url=$3

    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name (Port $port)"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name (Port $port)"
        return 1
    fi
}

# Infrastructure
echo "📦 INFRASTRUCTURE:"
check_service "PostgreSQL" "5432" "postgresql://localhost:5432" || true
check_service "Redis" "6379" "http://localhost:6379" || true
check_service "Ollama" "11434" "http://localhost:11434/api/tags"

echo ""
echo "🤖 AUTOMATION:"
check_service "n8n" "5678" "http://localhost:5678/healthz"

echo ""
echo "🔌 APIs:"
check_service "Empire API" "3333" "http://localhost:3333/health"
check_service "CRM Server" "3500" "http://localhost:3500/health"
check_service "Atomic Reactor" "8888" "http://localhost:8888/health" || true

echo ""
echo "📊 DETAILED INFO:"
echo ""

# n8n Workflows
echo "  n8n Workflows:"
WORKFLOWS=$(curl -s http://localhost:5678/api/workflows 2>/dev/null | jq '.[] | {name: .name, active: .active}' 2>/dev/null | head -10)
if [ -n "$WORKFLOWS" ]; then
    echo "$WORKFLOWS" | while read line; do
        echo "    $line"
    done
else
    echo "    ${YELLOW}Nicht verfügbar${NC}"
fi

echo ""
echo "  Redis Queue:"
QUEUE_SIZE=$(redis-cli dbsize 2>/dev/null | grep -o '[0-9]*')
if [ -n "$QUEUE_SIZE" ]; then
    echo "    Größe: $QUEUE_SIZE Keys"
else
    echo "    Nicht verfügbar"
fi

echo ""
echo "  Ollama Models:"
MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | jq '.models | length')
if [ -n "$MODELS" ]; then
    echo "    Geladene Modelle: $MODELS"
else
    echo "    Nicht verfügbar"
fi

echo ""
echo "📝 LOGS:"
LOG_DIR="$HOME/.openclaw/workspace/ai-empire/06_LOGS"
if [ -d "$LOG_DIR" ]; then
    echo "    n8n:      $LOG_DIR/n8n.log"
    echo "    Empire:   $LOG_DIR/empire_api.log"
    echo "    CRM:      $LOG_DIR/crm.log"
    echo "    Main:     $LOG_DIR/native_startup_*.log"
fi

echo ""
echo "🎯 QUICK ACTIONS:"
echo "    Start:   bash ~/AIEmpire-Core/scripts/NATIVE_START_ALL.sh"
echo "    Stop:    bash ~/AIEmpire-Core/scripts/native_stop.sh"
echo "    Setup:   bash ~/AIEmpire-Core/scripts/n8n_setup_automation.sh"
echo ""
