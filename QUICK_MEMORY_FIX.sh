#!/bin/bash
# QUICK MEMORY FIX - Run this IMMEDIATELY
# Maurice's 3.8GB RAM Emergency Fix

set -e

echo ""
echo "QUICK MEMORY FIX - 3.8GB RAM"
echo ""

# Step 1: Kill any old Ollama processes
echo "Step 1: Cleaning up Ollama processes..."
pkill -f "ollama" 2>/dev/null || true
sleep 1

# Step 2: Clear caches
echo "Step 2: Clearing caches..."
rm -rf ~/.cache/pip 2>/dev/null || true
rm -rf ~/.npm/_cacache 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Step 3: Check current RAM
echo "Step 3: Checking RAM..."
free -h 2>/dev/null || echo "free command not available"

# Step 4: Setup Ollama environment
echo "Step 4: Configuring Ollama for low-RAM..."
SHELL_RC="$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if ! grep -q "OLLAMA_NUM_PARALLEL" "$SHELL_RC" 2>/dev/null; then
    cat >> "$SHELL_RC" << 'INNEREOF'

# OLLAMA Memory Optimization
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_NUM_THREAD=2
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_MODELS_DIR=~/.ollama/models
INNEREOF
    echo "Updated $SHELL_RC"
else
    echo "Already configured"
fi

echo ""
echo "MEMORY FIX COMPLETE!"
echo ""
echo "Next steps:"
echo "  1. bash memory_monitor.sh &"
echo "  2. python3 smart_ollama_launch.py"
echo ""
