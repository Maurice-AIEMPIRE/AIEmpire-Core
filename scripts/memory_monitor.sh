#!/bin/bash
# MEMORY MONITOR - Ueberwacht RAM-Nutzung fuer 3.8GB System
# Warnt bei hoher Auslastung und killt Ollama bei Notfall
#
# Usage: bash memory_monitor.sh &

WARN_THRESHOLD=80    # % RAM -> Warnung
CRITICAL_THRESHOLD=90 # % RAM -> Ollama neustart
EMERGENCY_THRESHOLD=95 # % RAM -> Ollama kill
INTERVAL=30           # Sekunden zwischen Checks

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%H:%M:%S')] $1"
}

get_ram_percent() {
    free | awk '/Mem:/ {printf("%.0f", $3/$2 * 100)}'
}

get_ram_mb() {
    free -m | awk '/Mem:/ {print $3"/"$2"MB"}'
}

get_ollama_mem() {
    if pgrep -x ollama > /dev/null 2>&1; then
        ps -o rss= -p $(pgrep -x ollama) 2>/dev/null | awk '{printf("%.0f", $1/1024)}'
    else
        echo "0"
    fi
}

log "${GREEN}Memory Monitor gestartet${NC}"
log "Thresholds: WARN=${WARN_THRESHOLD}% CRITICAL=${CRITICAL_THRESHOLD}% EMERGENCY=${EMERGENCY_THRESHOLD}%"
log "Interval: ${INTERVAL}s"
echo ""

while true; do
    RAM_PCT=$(get_ram_percent)
    RAM_MB=$(get_ram_mb)
    OLLAMA_MB=$(get_ollama_mem)

    if [ "$RAM_PCT" -ge "$EMERGENCY_THRESHOLD" ]; then
        log "${RED}EMERGENCY${NC} RAM: ${RAM_PCT}% (${RAM_MB}) | Ollama: ${OLLAMA_MB}MB"
        if pgrep -x ollama > /dev/null 2>&1; then
            log "${RED}Killing Ollama to free memory...${NC}"
            pkill -9 ollama 2>/dev/null
            sleep 2
            log "RAM nach Kill: $(get_ram_percent)% ($(get_ram_mb))"
        fi
    elif [ "$RAM_PCT" -ge "$CRITICAL_THRESHOLD" ]; then
        log "${RED}CRITICAL${NC} RAM: ${RAM_PCT}% (${RAM_MB}) | Ollama: ${OLLAMA_MB}MB"
        if pgrep -x ollama > /dev/null 2>&1; then
            log "${YELLOW}Restarting Ollama with limits...${NC}"
            pkill ollama 2>/dev/null
            sleep 3
            OLLAMA_NUM_PARALLEL=1 OLLAMA_NUM_THREAD=2 ollama serve &
            log "Ollama neugestartet mit Limits"
        fi
    elif [ "$RAM_PCT" -ge "$WARN_THRESHOLD" ]; then
        log "${YELLOW}WARN${NC} RAM: ${RAM_PCT}% (${RAM_MB}) | Ollama: ${OLLAMA_MB}MB"
    else
        log "${GREEN}OK${NC} RAM: ${RAM_PCT}% (${RAM_MB}) | Ollama: ${OLLAMA_MB}MB"
    fi

    sleep "$INTERVAL"
done
