#!/bin/bash
# MEMORY MONITOR - Ueberwacht RAM-Nutzung (besonders fuer Ollama)
# Usage: bash memory_monitor.sh &

INTERVAL=30  # Sekunden zwischen Checks
LOG_FILE="/home/user/AIEmpire-Core/workflow-system/state/memory_log.txt"
WARN_THRESHOLD=80  # Prozent

echo "Memory Monitor gestartet (Intervall: ${INTERVAL}s)"
echo "Log: ${LOG_FILE}"
echo "---"

mkdir -p "$(dirname "$LOG_FILE")"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    MEM_INFO=$(free -m | awk 'NR==2{printf "Total: %sMB | Used: %sMB | Free: %sMB | Usage: %.1f%%", $2, $3, $4, $3*100/$2}')
    MEM_PCT=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')

    # Log
    echo "${TIMESTAMP} | ${MEM_INFO}" >> "$LOG_FILE"

    # Warnung bei hoher Nutzung
    if [ "$MEM_PCT" -gt "$WARN_THRESHOLD" ]; then
        echo "[WARN] ${TIMESTAMP} | RAM: ${MEM_PCT}% | ${MEM_INFO}"
    fi

    # Ollama Prozess checken
    OLLAMA_PID=$(pgrep -x ollama 2>/dev/null)
    if [ -n "$OLLAMA_PID" ]; then
        OLLAMA_MEM=$(ps -o rss= -p "$OLLAMA_PID" 2>/dev/null | awk '{printf "%.0f", $1/1024}')
        echo "${TIMESTAMP} | Ollama PID: ${OLLAMA_PID} | RAM: ${OLLAMA_MEM}MB" >> "$LOG_FILE"
    fi

    sleep "$INTERVAL"
done
