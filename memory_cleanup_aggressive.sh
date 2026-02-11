#!/bin/bash
# Aggressive Memory Cleanup for Emergency Situations
# Use when system RAM is critically low (>90%)

echo "=========================================="
echo "AGGRESSIVE MEMORY CLEANUP"
echo "=========================================="

# Get current memory usage
FREE=$(free | awk 'NR==2 {print $4}')
TOTAL=$(free | awk 'NR==2 {print $2}')
PERCENT=$((($TOTAL - $FREE) * 100 / $TOTAL))

echo "Current RAM: $PERCENT% used"

if [ $PERCENT -lt 80 ]; then
    echo "System RAM usage is OK ($PERCENT%)"
    exit 0
fi

echo ""
echo "WARNING: System RAM usage critical ($PERCENT%)"
echo "Running aggressive cleanup..."
echo ""

# 1. Stop background services that aren't critical
echo "1. Stopping non-critical services..."
systemctl stop node-red 2>/dev/null
systemctl stop docker 2>/dev/null
pkill -f "redis" 2>/dev/null
pkill -f "ollama" 2>/dev/null
pkill -f "jupyter" 2>/dev/null
pkill -f "npm" 2>/dev/null

# 2. Clear caches
echo "2. Clearing system caches..."
sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null
pip cache purge 2>/dev/null
python -c "import compileall; compileall.compile_dir('.')" 2>/dev/null

# 3. Remove temp files
echo "3. Removing temporary files..."
rm -rf /tmp/* 2>/dev/null
rm -rf ~/.cache/* 2>/dev/null
rm -rf ~/.npm/_cacache 2>/dev/null

# 4. Kill Python processes using >5% memory
echo "4. Killing high-memory processes..."
ps aux | awk '$3 > 5 {print $2}' | grep -v "^1$\|^$$" | xargs -r kill -9 2>/dev/null

# 5. Compress log files
echo "5. Compressing old log files..."
find /var/log -name "*.log" -type f -exec gzip {} \; 2>/dev/null

# 6. Check final status
echo ""
echo "=========================================="
FREE2=$(free | awk 'NR==2 {print $4}')
PERCENT2=$((($TOTAL - $FREE2) * 100 / $TOTAL))
echo "RAM after cleanup: $PERCENT2% used"
echo "Freed: $((($FREE2 - $FREE) / 1024)) MB"
echo "=========================================="

if [ $PERCENT2 -gt 80 ]; then
    echo "WARNING: Still high after cleanup!"
    echo "Recommended: Restart system"
    exit 1
else
    echo "SUCCESS: Memory cleared!"
    exit 0
fi
