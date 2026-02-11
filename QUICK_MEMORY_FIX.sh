#!/usr/bin/env bash
# QUICK MEMORY FIX - cross-platform (macOS/Linux)
# Goal: make Ollama usable on low-RAM machines by limiting parallelism/threads
# and ensuring a small model (phi:q4) is installed.

set -u

echo ""
echo "========================================"
echo "QUICK MEMORY FIX"
echo "Expected time: ~3 minutes"
echo "========================================"
echo ""

# Step 1: Kill any old Ollama processes
echo "Step 1: Cleaning up Ollama processes..."
pkill -f "ollama" 2>/dev/null || true
sleep 1

# Step 2: Clear lightweight caches
echo "Step 2: Clearing lightweight caches..."
rm -rf ~/.cache/pip 2>/dev/null || true
rm -rf ~/.npm/_cacache 2>/dev/null || true
find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true

# Step 3: Check current RAM (best-effort)
echo "Step 3: Checking RAM..."
if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY' 2>/dev/null || true
try:
    import psutil
except Exception:
    raise SystemExit(1)
vm = psutil.virtual_memory()
print(f"Current: {vm.percent:.0f}% used - FREE: {vm.available/1024/1024/1024:.2f} GB / TOTAL: {vm.total/1024/1024/1024:.2f} GB")
PY
elif command -v free >/dev/null 2>&1; then
  TOTAL=$(free -h | awk 'NR==2 {print $2}')
  USED=$(free -h | awk 'NR==2 {print $3}')
  FREE=$(free -h | awk 'NR==2 {print $4}')
  PERCENT=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')
  echo "Current: $USED used / $TOTAL total ($PERCENT%) - FREE: $FREE"
else
  echo "(Could not read RAM stats: install psutil or use Linux 'free')"
fi

echo ""

# Step 4: Setup Ollama environment
echo "Step 4: Configuring Ollama for low-RAM..."

SHELL_RC="$HOME/.zshrc"
if [ ! -f "$SHELL_RC" ]; then
  SHELL_RC="$HOME/.bashrc"
fi

if [ -f "$SHELL_RC" ]; then
  if ! grep -q "# OLLAMA Memory Optimization" "$SHELL_RC" 2>/dev/null; then
    cat >> "$SHELL_RC" << 'EOB'

# OLLAMA Memory Optimization
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_NUM_THREAD=2
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_MODELS_DIR=~/.ollama/models
EOB
    echo "✓ Updated $SHELL_RC"
  else
    echo "✓ $SHELL_RC already configured"
  fi
else
  echo "⚠ No shell rc file found (.zshrc/.bashrc). Skipping persistent env vars."
fi

# Also set for the current process
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_NUM_THREAD=2
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_MODELS_DIR="$HOME/.ollama/models"

# Step 5: Install ONLY phi:q4
echo "Step 5: Installing phi:q4 (small model)..."
if ! ollama list 2>/dev/null | grep -q "phi:q4"; then
  echo "Downloading phi:q4..."
  ollama pull phi:q4
  echo "✓ phi:q4 installed"
else
  echo "✓ phi:q4 already installed"
fi

# Step 6: Ensure Ollama API is running
echo "Step 6: Ensuring Ollama is running..."
if curl -s http://localhost:11434 >/dev/null 2>&1; then
  echo "✓ Ollama API responding"
else
  echo "Starting Ollama in background..."
  ollama serve >/dev/null 2>&1 &
  sleep 3
  if curl -s http://localhost:11434 >/dev/null 2>&1; then
    echo "✓ Ollama started"
  else
    echo "⚠ Ollama startup slow; try again in a few seconds"
  fi
fi

echo ""
echo "========================================"
echo "✓ MEMORY FIX COMPLETE"
echo "========================================"
echo "What's configured:"
echo "  - OLLAMA_NUM_PARALLEL=1"
echo "  - OLLAMA_NUM_THREAD=2"
echo "  - OLLAMA_KEEP_ALIVE=5m"
echo "  - phi:q4 installed"
echo ""
echo "Next steps:"
echo "  1) Start monitor: bash memory_monitor.sh &"
echo "  2) Start via launcher: python3 smart_ollama_launch.py"
echo ""
