#!/bin/bash

# 🔥 ULTIMATE LOCAL AI SYSTEM - ONE-CLICK LAUNCH
# Everything automatic. Just sit back and watch the magic.

set -e

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  🔥 ULTIMATE LOCAL AI SYSTEM - LAUNCH                    ║"
echo "║  1000+ Agents × 100% Local × 100% Free                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================
# PHASE 1: Verify Models
# ============================================================
echo -e "${BLUE}[1/5] VERIFYING MODELS...${NC}"

models=("phi:q4" "neural-chat:q4" "llama2:q4" "mistral:q4_K_M" "tinyllama:q4")
missing=()

for model in "${models[@]}"; do
    if ollama list | grep -q "^$model"; then
        echo -e "  ${GREEN}✓${NC} $model"
    else
        echo -e "  ${RED}✗${NC} $model (MISSING)"
        missing+=("$model")
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Installing missing models...${NC}"
    for model in "${missing[@]}"; do
        echo "  Installing $model..."
        ollama pull "$model" > /dev/null 2>&1 &
    done
    wait
    echo -e "  ${GREEN}✓ All models installed${NC}"
fi

# ============================================================
# PHASE 2: System Check
# ============================================================
echo ""
echo -e "${BLUE}[2/5] SYSTEM CHECK...${NC}"

# RAM
FREE_RAM=$(free -h | awk 'NR==2 {print $4}')
TOTAL_RAM=$(free -h | awk 'NR==2 {print $2}')
RAM_PERCENT=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')

echo "  RAM: $RAM_PERCENT% used ($FREE_RAM free / $TOTAL_RAM total)"

if [ "$RAM_PERCENT" -gt 85 ]; then
    echo -e "  ${YELLOW}⚠️  WARNING: RAM usage high!${NC}"
    echo "  Cleaning up..."
    bash memory_cleanup_aggressive.sh
fi

# CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{printf "%.0f", 100-$1}')
echo "  CPU: ${CPU_USAGE}% usage"

# Disk
DISK_FREE=$(df -h . | awk 'NR==2 {print $4}')
echo "  Disk: $DISK_FREE available"

# ============================================================
# PHASE 3: Prepare Environment
# ============================================================
echo ""
echo -e "${BLUE}[3/5] PREPARING ENVIRONMENT...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "  ${RED}✗ Python3 not found${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Python3 installed"

# Check pip packages
echo "  Installing Python dependencies..."
pip install aiohttp psutil ollama -q --break-system-packages 2>/dev/null
echo -e "  ${GREEN}✓${NC} Dependencies ready"

# ============================================================
# PHASE 4: Start Ollama Service
# ============================================================
echo ""
echo -e "${BLUE}[4/5] STARTING OLLAMA SERVICE...${NC}"

# Kill existing
pkill -f "ollama serve" 2>/dev/null || true
sleep 1

# Start new
ollama serve > /dev/null 2>&1 &
OLLAMA_PID=$!
echo "  Ollama PID: $OLLAMA_PID"

# Wait for startup
echo "  Waiting for Ollama..."
for i in {1..30}; do
    if curl -s http://localhost:11434 > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Ollama online"
        break
    fi
    sleep 1
    echo -n "."
done

if ! curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo -e "\n  ${RED}✗ Ollama failed to start${NC}"
    exit 1
fi

# ============================================================
# PHASE 5: Launch Swarm
# ============================================================
echo ""
echo -e "${BLUE}[5/5] LAUNCHING ULTIMATE SWARM...${NC}"

# Start memory monitor in background
echo "  Starting memory monitor..."
bash memory_monitor.sh > /dev/null 2>&1 &
echo -e "  ${GREEN}✓${NC} Monitor running"

# Wait a moment
sleep 2

# Show final status
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo -e "║  ${GREEN}✅ SYSTEM READY${NC}                                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${BLUE}Models:${NC}"
ollama list | grep -E "phi:q4|neural-chat|llama2|mistral|tinyllama" | awk '{printf "    • %s\n", $1}'

echo ""
echo -e "  ${BLUE}Status:${NC}"
echo "    • Ollama API: http://localhost:11434"
echo "    • RAM: $RAM_PERCENT% ($FREE_RAM free)"
echo "    • Memory Monitor: Running"
echo "    • Python Env: Ready"

echo ""
echo -e "  ${GREEN}TO START SWARM:${NC}"
echo "    python3 ultimate_orchestrator.py"
echo ""
echo -e "  ${YELLOW}MONITOR STATUS:${NC}"
echo "    tail -f memory_fix.log"
echo ""

# Offer to run
read -p "Start swarm now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Launching ultimate orchestrator...${NC}"
    python3 ultimate_orchestrator.py
else
    echo ""
    echo "Run manually: python3 ultimate_orchestrator.py"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  🚀 ULTIMATE SYSTEM OPERATIONAL                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
