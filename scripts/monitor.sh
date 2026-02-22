#!/bin/bash
# ============================================================
# AIEmpire System Monitor (Real-time Dashboard)
# ============================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

while true; do
    clear
    
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║          AIEmpire System Monitor                         ║"
    echo "║          $(date '+%Y-%m-%d %H:%M:%S')                              ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    
    echo ""
    echo "📊 SYSTEM STATUS"
    python3 "$PROJECT_ROOT/empire_engine.py" 2>/dev/null | head -30
    
    echo ""
    echo "🔄 RUNNING PROCESSES"
    ps aux | grep -E "python3|node|redis" | grep -v grep | awk '{print "  " $11 " (PID: " $2 ")"}'
    
    echo ""
    echo "🌐 PORT STATUS"
    for PORT in 8900 8901 4000 3500 8888 18789; do
        if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
            echo "  ✓ Port $PORT (ACTIVE)"
        else
            echo "  - Port $PORT (free)"
        fi
    done
    
    echo ""
    echo "📝 RECENT LOGS"
    if [ -d "$PROJECT_ROOT/logs" ]; then
        tail -5 "$PROJECT_ROOT/logs"/*.log 2>/dev/null | head -15
    fi
    
    echo ""
    echo "⏰ Next update in 10 seconds (Ctrl+C to exit)..."
    sleep 10
done
