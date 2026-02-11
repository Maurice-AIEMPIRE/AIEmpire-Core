#!/usr/bin/env bash
# Aggressive memory cleanup (cross-platform-ish)
# Use when RAM is critically low.

set -u

echo "=========================================="
echo "AGGRESSIVE MEMORY CLEANUP"
echo "=========================================="

mem_percent() {
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY' 2>/dev/null && return 0
try:
    import psutil
except Exception:
    raise SystemExit(1)
vm = psutil.virtual_memory()
print(int(vm.percent))
PY
  fi
  if command -v free >/dev/null 2>&1; then
    free | awk 'NR==2 {printf "%.0f", $3/$2*100}'
    return 0
  fi
  echo "0"
}

PERCENT=$(mem_percent || echo "0")
echo "Current RAM: ${PERCENT}% used"

if [ "${PERCENT}" -lt 80 ]; then
  echo "System RAM usage is OK (${PERCENT}%). Exiting."
  exit 0
fi

echo ""
echo "WARNING: System RAM usage critical (${PERCENT}%)"
echo "Running aggressive cleanup..."
echo ""

echo "1. Stopping non-critical processes/services..."
# Linux services (ignore failures on macOS)
command -v systemctl >/dev/null 2>&1 && systemctl stop docker 2>/dev/null || true
command -v systemctl >/dev/null 2>&1 && systemctl stop node-red 2>/dev/null || true

# Generic kills
pkill -f "docker" 2>/dev/null || true
pkill -f "ollama" 2>/dev/null || true
pkill -f "jupyter" 2>/dev/null || true
pkill -f "redis" 2>/dev/null || true
pkill -f "npm" 2>/dev/null || true
pkill -f "node" 2>/dev/null || true

echo "2. Clearing caches..."
# macOS (if available). Avoid sudo prompts; if it fails, ignore.
command -v purge >/dev/null 2>&1 && purge 2>/dev/null || true

# Linux page cache (if available)
if [ -w /proc/sys/vm/drop_caches ]; then
  sync 2>/dev/null || true
  echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
fi

# Tool caches
pip cache purge 2>/dev/null || true

echo "3. Removing temporary files..."
rm -rf /tmp/* 2>/dev/null || true
rm -rf ~/.cache/* 2>/dev/null || true
rm -rf ~/.npm/_cacache 2>/dev/null || true

echo "4. Killing high-memory processes (best-effort)..."
# Kill processes using >5% CPU as a crude proxy when tools differ.
pids=$(ps aux 2>/dev/null | awk '$3 > 5 {print $2}' | grep -v "^1$" || true)
if [ -n "${pids:-}" ]; then
  echo "$pids" | xargs kill -9 2>/dev/null || true
fi

echo ""
echo "=========================================="
echo "Memory after cleanup:"
if command -v free >/dev/null 2>&1; then
  free -h
elif command -v vm_stat >/dev/null 2>&1; then
  vm_stat
fi
echo "=========================================="
