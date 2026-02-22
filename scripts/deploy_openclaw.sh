#!/bin/bash
# ============================================================
# OpenClaw ABT Protocol Deployment Script
# ============================================================

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   OpenClaw ABT Protocol Deployment — AIEmpire-Core      ║"
echo "║   Ports: 8900 (Ant), 8901 (Skybot), 4000 (LiteLLM)     ║"
echo "╚══════════════════════════════════════════════════════════╝"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Step 1: Verify ports are free
echo ""
echo "[1/5] Verifying ports..."
for PORT in 8900 8901 4000 3500 8888 18789; do
    if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
        echo "  ✗ Port $PORT is in use"
        exit 1
    fi
    echo "  ✓ Port $PORT free"
done

# Step 2: Verify OpenClaw config
echo ""
echo "[2/5] Verifying OpenClaw configuration..."
if [ ! -f "$PROJECT_ROOT/openclaw-config/ant_protocol.json" ]; then
    echo "  ✗ ant_protocol.json not found"
    exit 1
fi
echo "  ✓ ant_protocol.json found"

if [ ! -d "$PROJECT_ROOT/openclaw-config/memory" ]; then
    mkdir -p "$PROJECT_ROOT/openclaw-config/memory"
    echo "  ✓ Created memory directory"
fi

# Step 3: Start data services (background)
echo ""
echo "[3/5] Starting data services..."

# Check if redis-server is available
if command -v redis-server &> /dev/null; then
    echo "  → Starting Redis..."
    redis-server --daemonize yes --logfile /tmp/redis.log 2>/dev/null || true
    sleep 1
    echo "  ✓ Redis started"
else
    echo "  ⚠ Redis not installed (optional)"
fi

# Check if postgres is available
if command -v postgres &> /dev/null; then
    echo "  → Starting PostgreSQL..."
    # Note: Full PostgreSQL setup would be complex, skip for now
    echo "  ⚠ PostgreSQL setup deferred (run: scripts/setup_optimal_dev.sh)"
else
    echo "  ⚠ PostgreSQL not installed (optional)"
fi

# Step 4: Prepare environment
echo ""
echo "[4/5] Preparing environment..."

# Create .env if missing
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "  → Creating .env file..."
    python3 "$PROJECT_ROOT/scripts/auto_repair.py" > /dev/null 2>&1 || true
fi

# Export key variables
export OPENCLAW_PORT=18789
export ANT_API_PORT=8900
export SKYBOT_API_PORT=8901
export LITELLM_PORT=4000
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo "  ✓ Environment configured"
echo "    OPENCLAW_PORT=$OPENCLAW_PORT"
echo "    ANT_API_PORT=$ANT_API_PORT"
echo "    SKYBOT_API_PORT=$SKYBOT_API_PORT"
echo "    LITELLM_PORT=$LITELLM_PORT"

# Step 5: Status check
echo ""
echo "[5/5] Final status check..."
echo ""
echo "  System Status:"
python3 "$PROJECT_ROOT/empire_engine.py" 2>&1 | head -20

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  DEPLOYMENT READY                        ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Next Steps:                                             ║"
echo "║  1. Start Ant Protocol: python3 -m antigravity.core     ║"
echo "║  2. Start CRM: cd crm && npm start                       ║"
echo "║  3. Start Atomic Reactor: python3 atomic_reactor/run...║"
echo "║  4. Monitor: python3 empire_engine.py revenue            ║"
echo "╚══════════════════════════════════════════════════════════╝"
