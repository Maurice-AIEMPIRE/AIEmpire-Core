#!/bin/bash

# memory_cleanup_aggressive.sh - Emergency memory cleanup
# Kills non-essential processes and clears caches

echo "🧹 AGGRESSIVE MEMORY CLEANUP"
echo "============================"

# Kill heavy processes (be careful!)
echo "1. Killing heavy processes..."
pkill -f "ollama" || true
pkill -f "python.*ollama" || true
pkill -f "node.*server" || true
pkill -f "docker" || true

# Clear system caches
echo "2. Clearing system caches..."
sudo purge 2>/dev/null || true  # macOS
echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true  # Linux

# Clear temp files
echo "3. Clearing temp files..."
rm -rf /tmp/* 2>/dev/null || true
rm -rf ~/Library/Caches/* 2>/dev/null || true

# Kill background jobs
echo "4. Killing background jobs..."
jobs -p | xargs kill -9 2>/dev/null || true

echo "5. Memory after cleanup:"
free -m || vm_stat || true

echo "✅ Cleanup complete"