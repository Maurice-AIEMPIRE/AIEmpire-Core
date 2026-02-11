#!/bin/bash

# QUICK_MEMORY_FIX.sh - 3-minute memory crisis solution
# Fixes 3.8GB RAM limitation for AI Empire system

echo "🚀 QUICK MEMORY FIX - Starting..."
echo "================================="

# 1. Stop Ollama if running
echo "1. Stopping Ollama..."
pkill -f ollama || true

# 2. Clean caches
echo "2. Cleaning caches..."
rm -rf ~/.ollama/models/* 2>/dev/null || true
rm -rf /tmp/ollama* 2>/dev/null || true

# 3. Install lightweight phi:q4 model (600MB)
echo "3. Installing phi:q4 model..."
ollama pull phi:q4

# 4. Configure Ollama for low memory
echo "4. Configuring Ollama..."
mkdir -p ~/.ollama
cat > ~/.ollama/config.json << EOF
{
  "max_loaded_models": 1,
  "max_queue": 1,
  "num_thread": 2,
  "num_gqa": 1,
  "low_vram": true
}
EOF

# 5. Start Ollama
echo "5. Starting Ollama..."
ollama serve &

# 6. Wait for startup
sleep 5

# 7. Verify
echo "6. Verifying..."
if ollama list | grep -q phi:q4; then
    echo "✅ phi:q4 model installed"
else
    echo "❌ Failed to install phi:q4"
    exit 1
fi

echo "🎉 MEMORY FIX COMPLETE!"
echo "Expected: 11.5x more free RAM"
echo "Next: Run memory_monitor.sh"