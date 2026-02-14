#!/usr/bin/env bash
# Continuous memory monitoring (cross-platform)
# Logs to memory_fix.log.

set -u

LOG_FILE="${LOG_FILE:-memory_fix.log}"

echo "Memory Monitor Started - $(date)" > "$LOG_FILE"
echo "=====================================" >> "$LOG_FILE"

mem_snapshot() {
  # Output: total_mb used_mb avail_mb percent
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY' 2>/dev/null && return 0
try:
    import psutil
except Exception:
    raise SystemExit(1)
vm = psutil.virtual_memory()
print(int(vm.total/1024/1024), int(vm.used/1024/1024), int(vm.available/1024/1024), int(vm.percent))
PY
  fi

  if command -v free >/dev/null 2>&1; then
    free -m | awk 'NR==2{print $2, $3, $7, int($3/$2*100)}'
    return 0
  fi

  return 1
}

while true; do
  TS=$(date '+%Y-%m-%d %H:%M:%S')

  if SNAP=$(mem_snapshot); then
    TOTAL=$(echo "$SNAP" | awk '{print $1}')
    USED=$(echo "$SNAP" | awk '{print $2}')
    FREE=$(echo "$SNAP" | awk '{print $3}')
    PERCENT=$(echo "$SNAP" | awk '{print $4}')

    if [ "$PERCENT" -gt 90 ]; then
      echo "[$TS] CRITICAL: ${PERCENT}% (${USED}MB used, ${FREE}MB free)" >> "$LOG_FILE"
      pkill -f "python.*test" 2>/dev/null || true
      pkill -f "node" 2>/dev/null || true
    elif [ "$PERCENT" -gt 80 ]; then
      echo "[$TS] HIGH MEMORY: ${PERCENT}% (${USED}MB used, ${FREE}MB free)" >> "$LOG_FILE"
    elif [ "$PERCENT" -gt 50 ]; then
      echo "[$TS] Memory: ${PERCENT}% (${USED}MB used, ${FREE}MB free)" >> "$LOG_FILE"
    fi

    OLLAMA_PROCS=$(pgrep -f ollama 2>/dev/null | wc -l | tr -d ' ')
    if [ "${OLLAMA_PROCS:-0}" -gt 0 ]; then
      echo "[$TS] Ollama running (${OLLAMA_PROCS} processes)" >> "$LOG_FILE"
    else
      echo "[$TS] Ollama not running" >> "$LOG_FILE"
    fi
  else
    echo "[$TS] Unable to read memory stats (need python3+psutil or free)" >> "$LOG_FILE"
  fi

  sleep 30
done
