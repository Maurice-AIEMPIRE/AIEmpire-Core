#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# 🧠 AI Empire Memory Monitor
# ═══════════════════════════════════════════════════════════════════
# Real-time monitoring for Ollama + system resources on M4 16GB
# Usage: bash memory_monitor.sh           (interactive dashboard)
#        bash memory_monitor.sh --once     (single snapshot, for scripts)
#        bash memory_monitor.sh --watch    (log to file, background use)
#
# Designed for: Apple M4, 16GB Unified Memory, macOS
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$REPO_ROOT/logs/memory_monitor.log"
ALERT_THRESHOLD_RAM_PCT=85
ALERT_THRESHOLD_SWAP_GB=8
REFRESH_INTERVAL=3

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

get_memory_info() {
    local mem_total_bytes
    mem_total_bytes=$(sysctl -n hw.memsize)
    local mem_total_gb
    mem_total_gb=$(echo "scale=1; $mem_total_bytes / 1073741824" | bc)

    # Get memory pressure percentage (free pages)
    local mem_free_pct
    mem_free_pct=$(memory_pressure -Q 2>/dev/null | grep "free percentage" | grep -oE '[0-9]+' || echo "0")

    local mem_used_pct=$((100 - mem_free_pct))

    # Swap info
    local swap_line
    swap_line=$(sysctl -n vm.swapusage 2>/dev/null)
    local swap_total_mb swap_used_mb
    swap_total_mb=$(echo "$swap_line" | grep -oE 'total = [0-9.]+' | grep -oE '[0-9.]+')
    swap_used_mb=$(echo "$swap_line" | grep -oE 'used = [0-9.]+' | grep -oE '[0-9.]+')
    local swap_used_gb
    swap_used_gb=$(echo "scale=1; ${swap_used_mb:-0} / 1024" | bc)
    local swap_total_gb
    swap_total_gb=$(echo "scale=1; ${swap_total_mb:-0} / 1024" | bc)

    echo "$mem_total_gb|$mem_used_pct|$mem_free_pct|$swap_used_gb|$swap_total_gb"
}

get_cpu_info() {
    # CPU usage via top (sampled over 1 second)
    local cpu_idle
    cpu_idle=$(top -l 1 -n 0 2>/dev/null | grep "CPU usage" | grep -oE '[0-9.]+% idle' | grep -oE '[0-9.]+' || echo "0")
    local cpu_used
    cpu_used=$(echo "scale=1; 100 - ${cpu_idle:-0}" | bc)
    echo "$cpu_used"
}

get_ollama_info() {
    # Check if Ollama is running
    if ! pgrep -q ollama 2>/dev/null; then
        echo "NOT_RUNNING|0|0"
        return
    fi

    # Get loaded models
    local models_json
    models_json=$(curl -s http://127.0.0.1:11434/api/ps 2>/dev/null || echo '{"models":[]}')

    local model_count
    model_count=$(echo "$models_json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = data.get('models', [])
    print(len(models))
except:
    print(0)
" 2>/dev/null || echo "0")

    # Get total VRAM used by loaded models
    local vram_gb
    vram_gb=$(echo "$models_json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = data.get('models', [])
    total = sum(m.get('size_vram', m.get('size', 0)) for m in models)
    print(f'{total / 1073741824:.1f}')
except:
    print('0.0')
" 2>/dev/null || echo "0.0")

    # Get model details
    local model_details
    model_details=$(echo "$models_json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = data.get('models', [])
    for m in models:
        name = m.get('name', 'unknown')
        size_gb = m.get('size_vram', m.get('size', 0)) / 1073741824
        expires = m.get('expires_at', 'N/A')
        print(f'  {name}: {size_gb:.1f}GB')
except:
    pass
" 2>/dev/null || echo "  (none loaded)")

    echo "RUNNING|$model_count|$vram_gb|$model_details"
}

get_gpu_info() {
    # Apple GPU utilization via powermetrics (requires sudo for full data)
    # Fallback to ioreg for basic GPU info
    local gpu_cores=10  # M4 has 10 GPU cores
    # We can check GPU utilization from the Metal performance HUD
    echo "$gpu_cores"
}

health_bar() {
    local pct=$1
    local width=30
    local filled=$((pct * width / 100))
    local empty=$((width - filled))
    local color

    if [ "$pct" -lt 60 ]; then
        color=$GREEN
    elif [ "$pct" -lt 80 ]; then
        color=$YELLOW
    else
        color=$RED
    fi

    printf "${color}"
    for ((i = 0; i < filled; i++)); do printf "█"; done
    printf "${DIM}"
    for ((i = 0; i < empty; i++)); do printf "░"; done
    printf "${NC} %3d%%" "$pct"
}

print_dashboard() {
    clear
    local mem_info cpu_used ollama_info

    mem_info=$(get_memory_info)
    cpu_used=$(get_cpu_info)
    ollama_info=$(get_ollama_info)

    IFS='|' read -r mem_total mem_used_pct mem_free_pct swap_used swap_total <<< "$mem_info"
    IFS='|' read -r ollama_status model_count vram_gb model_details <<< "$ollama_info"

    local timestamp
    timestamp=$(date "+%H:%M:%S")

    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║${NC}  ${BOLD}🧠 AI EMPIRE MEMORY MONITOR${NC}          ${DIM}${timestamp}${NC}  ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}║${NC}  ${DIM}Apple M4 • 16GB Unified • Metal 4${NC}                        ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"

    # RAM
    echo -e "${BOLD}${CYAN}║${NC}  ${BOLD}RAM${NC}    $(health_bar "${mem_used_pct%%.*}")  ${DIM}${mem_total}GB total${NC}"

    # Swap
    local swap_pct=0
    if [ "$(echo "$swap_total > 0" | bc)" -eq 1 ]; then
        swap_pct=$(echo "scale=0; $swap_used * 100 / $swap_total" | bc 2>/dev/null || echo "0")
    fi
    echo -e "${BOLD}${CYAN}║${NC}  ${BOLD}SWAP${NC}   $(health_bar "$swap_pct")  ${DIM}${swap_used}/${swap_total}GB${NC}"

    # CPU
    local cpu_int=${cpu_used%%.*}
    echo -e "${BOLD}${CYAN}║${NC}  ${BOLD}CPU${NC}    $(health_bar "$cpu_int")  ${DIM}4P+6E cores${NC}"

    echo -e "${BOLD}${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"

    # Ollama Status
    if [ "$ollama_status" = "RUNNING" ]; then
        echo -e "${BOLD}${CYAN}║${NC}  ${GREEN}● Ollama${NC}  ${BOLD}${model_count}${NC} model(s) loaded  ${MAGENTA}${vram_gb}GB VRAM${NC}"
        if [ -n "$model_details" ] && [ "$model_details" != "  (none loaded)" ]; then
            while IFS= read -r line; do
                echo -e "${BOLD}${CYAN}║${NC}  ${DIM}$line${NC}"
            done <<< "$model_details"
        fi
    else
        echo -e "${BOLD}${CYAN}║${NC}  ${RED}○ Ollama NOT RUNNING${NC}"
    fi

    echo -e "${BOLD}${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"

    # Alerts
    local alert=false
    if [ "${mem_used_pct%%.*}" -ge "$ALERT_THRESHOLD_RAM_PCT" ]; then
        echo -e "${BOLD}${CYAN}║${NC}  ${RED}⚠ HIGH MEMORY PRESSURE!${NC} Consider unloading models"
        alert=true
    fi
    if [ "$(echo "$swap_used > $ALERT_THRESHOLD_SWAP_GB" | bc)" -eq 1 ]; then
        echo -e "${BOLD}${CYAN}║${NC}  ${RED}⚠ EXCESSIVE SWAP (${swap_used}GB)!${NC} Run: ollama stop \$MODEL"
        alert=true
    fi
    if [ "$alert" = false ]; then
        echo -e "${BOLD}${CYAN}║${NC}  ${GREEN}✓ System healthy${NC}"
    fi

    # Recommendations
    echo -e "${BOLD}${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BOLD}${CYAN}║${NC}  ${DIM}Optimal config for 16GB M4:${NC}"
    echo -e "${BOLD}${CYAN}║${NC}  ${DIM}  • Max 1 model loaded at a time${NC}"
    echo -e "${BOLD}${CYAN}║${NC}  ${DIM}  • Use 7B quant models (≤5GB VRAM)${NC}"
    echo -e "${BOLD}${CYAN}║${NC}  ${DIM}  • OLLAMA_NUM_PARALLEL=1${NC}"
    echo -e "${BOLD}${CYAN}║${NC}  ${DIM}  • OLLAMA_NUM_THREAD=4 (perf cores only)${NC}"
    echo -e "${BOLD}${CYAN}║${NC}  ${DIM}  Press Ctrl+C to exit${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
}

snapshot() {
    local mem_info cpu_used ollama_info
    mem_info=$(get_memory_info)
    cpu_used=$(get_cpu_info)
    ollama_info=$(get_ollama_info)

    IFS='|' read -r mem_total mem_used_pct mem_free_pct swap_used swap_total <<< "$mem_info"
    IFS='|' read -r ollama_status model_count vram_gb _ <<< "$ollama_info"

    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    echo "[$timestamp] RAM: ${mem_used_pct}% | SWAP: ${swap_used}/${swap_total}GB | CPU: ${cpu_used}% | Ollama: ${ollama_status} (${model_count} models, ${vram_gb}GB VRAM)"
}

# ─── Main ───────────────────────────────────────────────────────────
case "${1:-}" in
    --once)
        snapshot
        ;;
    --watch)
        mkdir -p "$(dirname "$LOG_FILE")"
        echo "📝 Logging to $LOG_FILE (Ctrl+C to stop)"
        while true; do
            snapshot >> "$LOG_FILE"
            sleep "$REFRESH_INTERVAL"
        done
        ;;
    --help|-h)
        echo "Usage: bash memory_monitor.sh [--once|--watch|--help]"
        echo ""
        echo "  (default)  Interactive dashboard with auto-refresh"
        echo "  --once     Single snapshot (for scripts/cron)"
        echo "  --watch    Log to file in background"
        echo "  --help     This message"
        ;;
    *)
        trap 'echo -e "\n${GREEN}Monitor stopped.${NC}"; exit 0' INT
        while true; do
            print_dashboard
            sleep "$REFRESH_INTERVAL"
        done
        ;;
esac
