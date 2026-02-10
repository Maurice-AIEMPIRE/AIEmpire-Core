#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# 🚀 AI Empire — Quick Launch (Optimized for M4 16GB)
# ═══════════════════════════════════════════════════════════════════
# One-command system health check + optimization + launch
#
# Usage:
#   bash scripts/quick_launch.sh          # Full check + interactive mode
#   bash scripts/quick_launch.sh --fast   # Skip checks, just launch
#   bash scripts/quick_launch.sh --bench  # Run benchmarks
#   bash scripts/quick_launch.sh --clean  # Unload all models + free RAM
#
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║            🏰 AI EMPIRE — SYSTEM LAUNCHER                  ║"
echo "║            Apple M4 • 16GB • Metal 4 • 100% Local          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Step 1: Ensure Ollama is running ───────────────────────────────
echo -e "${BOLD}1. Ollama Server${NC}"
if pgrep -q ollama 2>/dev/null; then
    echo -e "   ${GREEN}● Running${NC}"
else
    echo -e "   ${YELLOW}○ Starting Ollama...${NC}"
    ollama serve &>/dev/null &
    sleep 3
    if pgrep -q ollama 2>/dev/null; then
        echo -e "   ${GREEN}● Started${NC}"
    else
        echo -e "   ${RED}✗ Failed to start! Run: ollama serve${NC}"
        exit 1
    fi
fi

# ─── Step 2: Environment Check ─────────────────────────────────────
echo -e "\n${BOLD}2. Environment${NC}"

check_env() {
    local var=$1
    local expected=$2
    local actual="${!var:-}"
    if [ "$actual" = "$expected" ]; then
        echo -e "   ${GREEN}✓${NC} ${var}=${actual}"
    else
        echo -e "   ${YELLOW}→${NC} ${var}=${expected} ${DIM}(current: ${actual:-unset})${NC}"
        export "$var"="$expected"
    fi
}

check_env OLLAMA_NUM_PARALLEL 1
check_env OLLAMA_NUM_THREAD 4
check_env OLLAMA_FLASH_ATTENTION 1
check_env OLLAMA_KV_CACHE_TYPE q8_0
check_env OLLAMA_MAX_LOADED_MODELS 1

# ─── Step 3: Memory Check ──────────────────────────────────────────
echo -e "\n${BOLD}3. Memory Status${NC}"
MEM_FREE_PCT=$(memory_pressure -Q 2>/dev/null | grep "free percentage" | grep -oE '[0-9]+' || echo "50")
SWAP_LINE=$(sysctl -n vm.swapusage 2>/dev/null)
SWAP_USED_MB=$(echo "$SWAP_LINE" | grep -oE 'used = [0-9.]+' | grep -oE '[0-9.]+')
SWAP_USED_GB=$(echo "scale=1; ${SWAP_USED_MB:-0} / 1024" | bc)
MEM_USED_PCT=$((100 - MEM_FREE_PCT))

if [ "$MEM_USED_PCT" -ge 90 ]; then
    echo -e "   ${RED}⚠ RAM: ${MEM_USED_PCT}% used — CRITICAL!${NC}"
    echo -e "   ${DIM}Unloading all models to free memory...${NC}"
    python3 "${SCRIPT_DIR}/smart_ollama_launch.py" --clean 2>/dev/null || true
    sleep 2
elif [ "$MEM_USED_PCT" -ge 80 ]; then
    echo -e "   ${YELLOW}⚠ RAM: ${MEM_USED_PCT}% used — elevated${NC}"
else
    echo -e "   ${GREEN}✓ RAM: ${MEM_USED_PCT}% used${NC}"
fi

if [ "$(echo "$SWAP_USED_GB > 8" | bc)" -eq 1 ]; then
    echo -e "   ${YELLOW}⚠ Swap: ${SWAP_USED_GB}GB — consider restarting if sluggish${NC}"
else
    echo -e "   ${GREEN}✓ Swap: ${SWAP_USED_GB}GB${NC}"
fi

# ─── Step 4: Model Inventory ───────────────────────────────────────
echo -e "\n${BOLD}4. Available Models${NC}"
ollama list 2>/dev/null | while IFS= read -r line; do
    if echo "$line" | grep -qE "^(qwen3-coder|glm-4.7)"; then
        echo -e "   ${RED}✗${NC} $line ${DIM}(too large for 16GB)${NC}"
    elif echo "$line" | grep -qE "^(qwen2.5-coder:7b|deepseek-r1)"; then
        echo -e "   ${GREEN}⭐${NC} $line"
    elif echo "$line" | grep -qE "^NAME"; then
        continue
    else
        echo -e "   ${DIM}  ${NC} $line"
    fi
done

# ─── Step 5: Handle CLI args ───────────────────────────────────────
case "${1:-}" in
    --fast)
        echo -e "\n${GREEN}✅ System ready. Use smart_ollama_launch.py for model management.${NC}"
        ;;
    --bench)
        echo -e "\n${BOLD}Running benchmarks...${NC}"
        python3 "${SCRIPT_DIR}/smart_ollama_launch.py" --benchmark
        ;;
    --clean)
        echo -e "\n${BOLD}Cleaning up...${NC}"
        python3 "${SCRIPT_DIR}/smart_ollama_launch.py" --clean
        echo -e "${GREEN}✅ All models unloaded.${NC}"
        ;;
    --monitor)
        echo -e "\n${BOLD}Starting monitor...${NC}"
        bash "${SCRIPT_DIR}/memory_monitor.sh"
        ;;
    *)
        echo -e "\n${BOLD}5. Quick Test${NC}"
        python3 "${SCRIPT_DIR}/smart_ollama_launch.py"
        ;;
esac

echo -e "\n${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${DIM}Commands:${NC}"
echo -e "  ${DIM}python3 scripts/smart_ollama_launch.py --optimize   # Auto-configure${NC}"
echo -e "  ${DIM}python3 scripts/smart_ollama_launch.py --benchmark  # Speed test${NC}"
echo -e "  ${DIM}python3 scripts/smart_ollama_launch.py --clean      # Free RAM${NC}"
echo -e "  ${DIM}python3 scripts/smart_ollama_launch.py --select qa  # Pick model for task${NC}"
echo -e "  ${DIM}bash scripts/memory_monitor.sh                      # Live dashboard${NC}"
echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
