#!/bin/bash
# ============================================================
# Start All AIEmpire Services (Full Stack)
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║        AIEmpire Full Stack Startup                      ║"
echo "║        Redis + CRM + Atomic Reactor + Empire Engine    ║"
echo "╚══════════════════════════════════════════════════════════╝"

# Function to start service in background
start_service() {
    local name=$1
    local cmd=$2
    local logfile="$LOG_DIR/${name}.log"
    
    echo ""
    echo "  → Starting $name..."
    nohup $cmd > "$logfile" 2>&1 &
    local pid=$!
    echo "  ✓ $name started (PID: $pid)"
    echo "    Log: $logfile"
}

# Service: Redis
echo ""
echo "[1] Data Services"
if command -v redis-server &> /dev/null; then
    redis-server --daemonize yes --logfile "$LOG_DIR/redis.log" 2>/dev/null || true
    echo "  ✓ Redis started"
else
    echo "  ⚠ Redis not available"
fi

# Service: Atomic Reactor (async task runner)
echo ""
echo "[2] Atomic Reactor (Port 8888)"
if [ -f "$PROJECT_ROOT/atomic_reactor/run_tasks.py" ]; then
    start_service "atomic-reactor" \
        "python3 $PROJECT_ROOT/atomic_reactor/run_tasks.py"
fi

# Service: CRM (if Node.js available)
echo ""
echo "[3] CRM System (Port 3500)"
if command -v node &> /dev/null && [ -f "$PROJECT_ROOT/crm/package.json" ]; then
    start_service "crm" \
        "bash -c 'cd $PROJECT_ROOT/crm && npm start'"
else
    echo "  ⚠ CRM requires Node.js and npm"
fi

# Service: Empire Engine background cycle
echo ""
echo "[4] Empire Engine (Background)"
start_service "empire-engine" \
    "python3 $PROJECT_ROOT/empire_engine.py auto"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                ALL SERVICES STARTED                      ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Logs: $LOG_DIR/                                        ║"
echo "║                                                          ║"
echo "║  Check Status:                                           ║"
echo "║  $ python3 empire_engine.py                              ║"
echo "║  $ ps aux | grep python3                                 ║"
echo "║  $ tail -f logs/*.log                                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
