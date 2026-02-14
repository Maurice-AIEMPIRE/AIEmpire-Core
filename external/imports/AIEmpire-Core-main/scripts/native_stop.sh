#!/bin/bash
# 🛑 native_stop.sh - Alle Services stoppen

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Maurice's AI Empire - STOP ALL SERVICES              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

echo "Stoppe alle Services..."
echo ""

# Stop FastAPI Services (Empire API, Atomic Reactor)
echo "Stoppe FastAPI Services..."
pkill -f "uvicorn server:app" 2>/dev/null && log_info "Empire API gestoppt" || echo "  Empire API nicht laufend"
pkill -f "python3 run_tasks.py" 2>/dev/null && log_info "Atomic Reactor gestoppt" || echo "  Atomic Reactor nicht laufend"

# Stop n8n
echo "Stoppe n8n..."
pkill -f "n8n start" 2>/dev/null && log_info "n8n gestoppt" || echo "  n8n nicht laufend"

# Stop CRM Server
echo "Stoppe CRM Server..."
pkill -f "npm start" 2>/dev/null && log_info "CRM Server gestoppt" || echo "  CRM Server nicht laufend"

# Brew Services (optional - können laufen gelassen werden)
read -p "Sollen auch Brew Services gestoppt werden? (PostgreSQL, Redis, Ollama) [y/N]: " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stoppe Brew Services..."
    brew services stop postgresql@14 2>/dev/null && log_info "PostgreSQL gestoppt"
    brew services stop redis 2>/dev/null && log_info "Redis gestoppt"
    brew services stop ollama 2>/dev/null && log_info "Ollama gestoppt"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ ALLE SERVICES GESTOPPT                            ║"
echo "╚════════════════════════════════════════════════════════╝"
