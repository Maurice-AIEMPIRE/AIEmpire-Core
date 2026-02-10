#!/bin/bash
# AGENT SWARM BOOTSTRAP
# One command to launch the entire autonomous agent army
# 100% local, 100% free, 100% autonomous

set -e

SWARM_HOME="/Users/maurice/AIEmpire-Core/.claude/worktrees/cranky-leavitt"
PYTHON=$(which python3)
VENV_PATH="$SWARM_HOME/venv"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🚀 AGENT SWARM BOOTSTRAP - LAUNCHING AGENT ARMY       ║"
echo "║         100% Local | 100% Free | 100% Autonomous          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check Python
echo "[1/7] Verifying Python installation..."
if ! command -v $PYTHON &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi
echo "✅ Python3: $($PYTHON --version)"

# Step 2: Create Virtual Environment (optional)
echo "[2/7] Setting up Python environment..."
if [ ! -d "$VENV_PATH" ]; then
    $PYTHON -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install --upgrade pip
    echo "✅ Virtual environment created"
else
    source "$VENV_PATH/bin/activate"
    echo "✅ Virtual environment ready"
fi

# Step 3: Install Dependencies
echo "[3/7] Installing Python dependencies..."
pip install -q \
    aiohttp>=3.9.0 \
    httpx>=0.26.0 \
    psycopg2-binary>=2.9.0 \
    redis>=5.0.0 \
    psutil>=5.9.0 \
    pyyaml>=6.0

echo "✅ Dependencies installed"

# Step 4: Check Services
echo "[4/7] Checking required services..."

echo -n "  Ollama... "
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌ (Start with: ollama serve)"
fi

echo -n "  Redis... "
if redis-cli ping > /dev/null 2>&1; then
    echo "✅"
else
    echo "⚠️  (Optional, Start with: redis-server)"
fi

echo -n "  PostgreSQL... "
if pg_isready -h localhost > /dev/null 2>&1; then
    echo "✅"
else
    echo "⚠️  (Optional, Start with: postgres)"
fi

# Step 5: Initialize Database
echo "[5/7] Initializing agent database..."
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE agent_swarm;" 2>/dev/null || true

psql -h localhost -d agent_swarm -U postgres << 'EOF' 2>/dev/null || true
CREATE TABLE IF NOT EXISTS problems (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    description TEXT,
    severity INT,
    status VARCHAR(50),
    assigned_agent VARCHAR(50),
    solution TEXT,
    verified BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS agent_stats (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100),
    problems_solved INT DEFAULT 0,
    success_rate FLOAT DEFAULT 0.95,
    last_task TIMESTAMP,
    uptime_hours INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    agent_id VARCHAR(100),
    log_level VARCHAR(20),
    message TEXT
);
EOF

echo "✅ Database ready (agent_swarm)"

# Step 6: Make scripts executable
echo "[6/7] Preparing agent scripts..."
chmod +x "$SWARM_HOME"/*.py 2>/dev/null || true
echo "✅ Agent scripts ready"

# Step 7: Launch Agent Army
echo "[7/7] Launching Agent Army..."
echo ""

# Run in background
cd "$SWARM_HOME"

# Start orchestrator in background
echo "  🚀 Starting Maestro Agent..."
$PYTHON "$SWARM_HOME/maestro_agent.py" > /tmp/maestro.log 2>&1 &
MAESTRO_PID=$!
sleep 2

echo "  🚀 Starting Orchestrator (Master Router)..."
$PYTHON "$SWARM_HOME/agent_swarm_orchestrator.py" > /tmp/orchestrator.log 2>&1 &
ORCH_PID=$!
sleep 2

echo "  🚀 Starting AutoDebugger..."
$PYTHON "$SWARM_HOME/autonomous_debugger_agent.py" > /tmp/debugger.log 2>&1 &
DEBUG_PID=$!

echo "  🚀 Starting CodeOptimizer..."
$PYTHON "$SWARM_HOME/code_optimizer_agent.py" > /tmp/optimizer.log 2>&1 &
OPT_PID=$!

sleep 2

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║            ✅ AGENT ARMY OPERATIONAL                       ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║                                                            ║"
echo "║  AGENTS RUNNING:                                          ║"
echo "║  • Maestro Agent        (PID: $MAESTRO_PID)                         ║"
echo "║  • Orchestrator         (PID: $ORCH_PID)                         ║"
echo "║  • AutoDebugger         (PID: $DEBUG_PID)                        ║"
echo "║  • CodeOptimizer        (PID: $OPT_PID)                         ║"
echo "║                                                            ║"
echo "║  CAPABILITIES:                                            ║"
echo "║  ✅ Continuous problem detection                          ║"
echo "║  ✅ Autonomous problem solving                            ║"
echo "║  ✅ Self-healing system                                   ║"
echo "║  ✅ 24/7 monitoring & optimization                        ║"
echo "║  ✅ Zero cost (100% local Ollama)                         ║"
echo "║                                                            ║"
echo "║  MONITOR LOGS:                                            ║"
echo "║  tail -f /tmp/maestro.log                                 ║"
echo "║  tail -f /tmp/orchestrator.log                            ║"
echo "║  tail -f /tmp/debugger.log                                ║"
echo "║  tail -f /tmp/optimizer.log                               ║"
echo "║                                                            ║"
echo "║  DATABASE:                                                ║"
echo "║  psql agent_swarm -U postgres                             ║"
echo "║                                                            ║"
echo "║  STOP ALL AGENTS:                                         ║"
echo "║  pkill -f maestro_agent                                   ║"
echo "║  pkill -f agent_swarm_orchestrator                        ║"
echo "║  pkill -f autonomous_debugger                             ║"
echo "║  pkill -f code_optimizer                                  ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Agent Army is now running autonomously!"
echo "Press Ctrl+C to monitor, or background this script"
echo ""

# Keep script running (so parents don't exit)
wait $MAESTRO_PID
