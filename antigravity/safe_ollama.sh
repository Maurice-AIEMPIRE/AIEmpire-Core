#!/bin/bash
# ═══════════════════════════════════════════════════════════
# safe_ollama — Run Ollama models safely
# Checks RAM before loading. Stops existing models first.
# REPLACES direct 'ollama run' calls.
# ═══════════════════════════════════════════════════════════

GUARDIAN="$(dirname "$0")/system_guardian.py"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo ""
    echo -e "${BLUE}🛡️  safe_ollama — Safe Ollama Model Runner${NC}"
    echo ""
    echo "Usage:"
    echo "  safe_ollama run <model> [prompt]    Run model safely"
    echo "  safe_ollama chat <model>            Interactive chat safely"
    echo "  safe_ollama stop [model]            Stop model(s)"
    echo "  safe_ollama status                  Show what's loaded + RAM"
    echo "  safe_ollama check <model>           Check if safe to load"
    echo ""
    echo "Examples:"
    echo "  safe_ollama run qwen2.5-coder:7b 'Write hello world'"
    echo "  safe_ollama chat qwen2.5-coder:14b"
    echo "  safe_ollama stop"
    echo ""
}

get_free_ram_mb() {
    # Use vm_stat for accurate free RAM on macOS
    local page_size=$(vm_stat | head -1 | grep -o '[0-9]*' | tail -1)
    local free_pages=$(vm_stat | grep "Pages free" | awk '{print $NF}' | tr -d '.')
    local inactive=$(vm_stat | grep "Pages inactive" | awk '{print $NF}' | tr -d '.')
    local free_bytes=$(( (free_pages + inactive) * page_size ))
    echo $(( free_bytes / 1024 / 1024 ))
}

get_loaded_models() {
    ollama ps 2>/dev/null | tail -n +2 | awk '{print $1}'
}

check_safety() {
    local model="$1"
    local free_ram=$(get_free_ram_mb)
    local free_gb=$(echo "scale=1; $free_ram / 1024" | bc 2>/dev/null || echo "0")
    local loaded=$(get_loaded_models)
    
    # Check if models already loaded
    if [ -n "$loaded" ]; then
        echo -e "${YELLOW}⚠️  Models already loaded:${NC}"
        echo "$loaded" | while read m; do echo "   → $m"; done
        echo ""
        echo -e "${YELLOW}Stopping existing models first...${NC}"
        echo "$loaded" | while read m; do
            ollama stop "$m" 2>/dev/null
            echo -e "  ${GREEN}✅ Stopped: $m${NC}"
        done
        sleep 2
        free_ram=$(get_free_ram_mb)
        free_gb=$(echo "scale=1; $free_ram / 1024" | bc 2>/dev/null || echo "0")
    fi
    
    # Check RAM requirements
    local required_gb=6
    if echo "$model" | grep -qE "14b|32b|70b"; then
        required_gb=11
    fi
    
    echo -e "${BLUE}📊 RAM Check:${NC}"
    echo -e "   Free: ${free_gb}GB (${free_ram}MB)"
    echo -e "   Need: ${required_gb}GB for $model"
    
    if [ "$free_ram" -lt $((required_gb * 1024)) ]; then
        echo ""
        echo -e "${RED}❌ NOT SAFE: Not enough RAM to load $model${NC}"
        echo -e "${YELLOW}   Close some apps or use a smaller model (7b instead of 14b)${NC}"
        return 1
    fi
    
    echo -e "   ${GREEN}✅ SAFE to load $model${NC}"
    return 0
}

cmd_run() {
    local model="$1"
    shift
    local prompt="$*"
    
    if [ -z "$model" ]; then
        echo -e "${RED}❌ No model specified. Usage: safe_ollama run <model> [prompt]${NC}"
        return 1
    fi
    
    if ! check_safety "$model"; then
        return 1
    fi
    
    echo ""
    echo -e "${GREEN}🚀 Loading $model...${NC}"
    echo ""
    
    if [ -n "$prompt" ]; then
        ollama run "$model" "$prompt"
    else
        ollama run "$model"
    fi
}

cmd_chat() {
    local model="$1"
    
    if [ -z "$model" ]; then
        echo -e "${RED}❌ No model specified. Usage: safe_ollama chat <model>${NC}"
        return 1
    fi
    
    if ! check_safety "$model"; then
        return 1
    fi
    
    echo ""
    echo -e "${GREEN}🚀 Starting chat with $model...${NC}"
    echo -e "${BLUE}Type /bye to exit${NC}"
    echo ""
    
    ollama run "$model"
}

cmd_stop() {
    local model="$1"
    
    if [ -n "$model" ]; then
        ollama stop "$model" 2>/dev/null
        echo -e "${GREEN}✅ Stopped: $model${NC}"
    else
        local loaded=$(get_loaded_models)
        if [ -z "$loaded" ]; then
            echo -e "${GREEN}✅ No models currently loaded.${NC}"
            return
        fi
        echo "$loaded" | while read m; do
            ollama stop "$m" 2>/dev/null
            echo -e "${GREEN}✅ Stopped: $m${NC}"
        done
    fi
}

cmd_status() {
    local free_ram=$(get_free_ram_mb)
    local free_gb=$(echo "scale=1; $free_ram / 1024" | bc 2>/dev/null || echo "?")
    local load=$(sysctl -n vm.loadavg 2>/dev/null | tr -d '{ }' | awk '{print $1}')
    local loaded=$(get_loaded_models)
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}🛡️  System Status${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "  RAM free:  ${free_gb}GB (${free_ram}MB)"
    echo -e "  CPU load:  ${load}"
    
    if [ -n "$loaded" ]; then
        echo -e "  Models:    $(echo "$loaded" | wc -l | tr -d ' ') loaded"
        echo "$loaded" | while read m; do echo -e "    → $m"; done
    else
        echo -e "  Models:    None loaded ✅"
    fi
    
    # Health
    if [ "$free_ram" -lt 500 ]; then
        echo -e "\n  ${RED}🚨 CRITICAL: System near crash!${NC}"
    elif [ "$free_ram" -lt 1000 ]; then
        echo -e "\n  ${YELLOW}⚠️  WARNING: RAM low${NC}"
    elif [ "$free_ram" -lt 2000 ]; then
        echo -e "\n  ${YELLOW}ℹ️  FAIR: Tight but OK${NC}"
    else
        echo -e "\n  ${GREEN}✅ HEALTHY${NC}"
    fi
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

case "${1:-}" in
    run)    shift; cmd_run "$@";;
    chat)   shift; cmd_chat "$@";;
    stop)   shift; cmd_stop "$@";;
    status) cmd_status;;
    check)  shift; check_safety "$@";;
    *)      show_help;;
esac
