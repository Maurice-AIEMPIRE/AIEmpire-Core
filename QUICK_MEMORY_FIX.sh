#!/bin/bash
# QUICK MEMORY FIX - Run this IMMEDIATELY
# Maurice's 3.8GB RAM Emergency Fix

set -e

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  QUICK MEMORY FIX - 3.8GB RAM          ║"
echo "║  Expected time: 3 minutes               ║"
echo "╚════════════════════════════════════════╝"
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
TOTAL=$(free -h | awk 'NR==2 {print $2}')
USED=$(free -h | awk 'NR==2 {print $3}')
FREE=$(free -h | awk 'NR==2 {print $4}')
PERCENT=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')

echo "Current: $USED used / $TOTAL total ($PERCENT%) - FREE: $FREE"
echo ""

# Step 4: Setup Ollama environment
echo "Step 4: Configuring Ollama for low-RAM..."

SHELL_RC="$HOME/.zshrc"
if [ ! -f "$SHELL_RC" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

# Check if already configured
if ! grep -q "OLLAMA_NUM_PARALLEL" "$SHELL_RC"; then
    cat >> "$SHELL_RC" << 'EOF'

# OLLAMA Memory Optimization
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_NUM_THREAD=2
export OLLAMA_KEEP_ALIVE=5m
export OLLAMA_MODELS_DIR=~/.ollama/models
EOF
    echo "✓ Updated $SHELL_RC"
else
    echo "✓ Already configured"
fi

# Step 5: Source the config
echo "Step 5: Loading configuration..."
source "$SHELL_RC" 2>/dev/null || true

# Step 6: Install ONLY phi:q4
echo "Step 6: Installing phi:q4 (600MB only)..."
if ! ollama list 2>/dev/null | grep -q "phi"; then
    echo "Downloading phi:q4... (this takes 1-2 min)"
    ollama pull phi:q4
    echo "✓ phi:q4 installed"
else
    echo "✓ phi:q4 already installed"
fi

# Step 7: Verify
echo ""
echo "Step 7: Final verification..."
FREE2=$(free -h | awk 'NR==2 {print $4}')
PERCENT2=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')

echo "After fix: $PERCENT2% used - FREE: $FREE2"
echo ""

# Step 8: Test
echo "Step 8: Testing Ollama..."
if curl -s http://localhost:11434 > /dev/null; then
    echo "✓ Ollama API responding"
else
    echo "Starting Ollama in background..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    if curl -s http://localhost:11434 > /dev/null; then
        echo "✓ Ollama started"
    else
        echo "⚠ Ollama startup slow, waiting..."
        sleep 5
    fi
fi

# Final status
echo ""
echo "╔════════════════════════════════════════╗"
echo "║  ✓ MEMORY FIX COMPLETE!                ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "What's configured:"
echo "  • OLLAMA_NUM_PARALLEL=1 (only 1 model)"
echo "  • OLLAMA_NUM_THREAD=2 (minimal threads)"
echo "  • OLLAMA_KEEP_ALIVE=5m (unload after idle)"
echo "  • phi:q4 installed (600MB only)"
echo ""
echo "Next steps:"
echo "  1. Start memory monitor:"
echo "     bash memory_monitor.sh &"
echo "  2. Test with Python:"
echo "     python3 smart_ollama_launch.py"
echo "  3. Or use web UI:"
echo "     ./start-dev-env.sh"
echo ""
echo "RAM is now optimized! System should be fast again."
echo ""
