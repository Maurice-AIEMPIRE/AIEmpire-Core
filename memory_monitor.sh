#!/bin/bash

# memory_monitor.sh - Continuous memory monitoring
# Logs to memory_fix.log

LOG_FILE="memory_fix.log"

echo "🧠 Memory Monitor Started - $(date)" > $LOG_FILE
echo "=====================================" >> $LOG_FILE

while true; do
    # Get memory info
    MEM_INFO=$(free -m | grep '^Mem:')
    TOTAL=$(echo $MEM_INFO | awk '{print $2}')
    USED=$(echo $MEM_INFO | awk '{print $3}')
    FREE=$(echo $MEM_INFO | awk '{print $4}')
    PERCENT=$((USED * 100 / TOTAL))

    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # Log if high usage
    if [ $PERCENT -gt 80 ]; then
        echo "[$TIMESTAMP] ⚠️  HIGH MEMORY: ${PERCENT}% (${USED}MB used, ${FREE}MB free)" >> $LOG_FILE
    elif [ $PERCENT -gt 50 ]; then
        echo "[$TIMESTAMP] ℹ️  Memory: ${PERCENT}% (${USED}MB used, ${FREE}MB free)" >> $LOG_FILE
    fi

    # Check Ollama processes
    OLLAMA_PROCS=$(pgrep -f ollama | wc -l)
    if [ $OLLAMA_PROCS -gt 0 ]; then
        echo "[$TIMESTAMP] 🤖 Ollama running (${OLLAMA_PROCS} processes)" >> $LOG_FILE
    else
        echo "[$TIMESTAMP] ❌ Ollama not running" >> $LOG_FILE
    fi

    sleep 30
done