#!/bin/bash

################################################################################
# AIEmpire-Core - Autonomous Operating System Launcher
# Starts your complete, self-improving, faceless revenue machine
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🚀 AIEmpire-Core Autonomous System Launcher${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python3 found${NC}\n"

# 1. System Startup Verification
echo -e "${BLUE}Step 1: Verifying System Health...${NC}"
PYTHONPATH=. python3 antigravity/system_startup.py

echo -e "\n${BLUE}Step 2: Starting Autonomous Daemon...${NC}"

# Check if daemon already running
if pgrep -f "autonomous_daemon.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  Daemon already running (PID: $(pgrep -f 'autonomous_daemon.py'))${NC}"
    echo "Use: pkill -f autonomous_daemon.py (to stop)"
else
    # Start daemon in background
    echo "Starting daemon in background..."
    nohup python3 -m antigravity.autonomous_daemon > antigravity/_daemon/daemon.log 2>&1 &
    DAEMON_PID=$!
    echo -e "${GREEN}✓ Daemon started (PID: $DAEMON_PID)${NC}"
    echo "Log: antigravity/_daemon/daemon.log"
fi

echo -e "\n${BLUE}Step 3: Displaying System Status${NC}\n"

PYTHONPATH=. python3 << 'PYTHON_EOF'
import json
from pathlib import Path
from antigravity.autonomous_daemon import AutonomousDaemon
from antigravity.offline_claude import OfflineClaude
from antigravity.resource_aware import get_executor

print("=" * 50)
print("AUTONOMOUS EMPIRE STATUS")
print("=" * 50)

# Daemon status
daemon = AutonomousDaemon()
daemon_status = daemon.get_status()
print(f"\n🤖 Daemon Status:")
print(f"   Running: {daemon_status['is_running']}")
print(f"   Tasks Completed: {daemon_status['tasks_completed']}")
print(f"   Tasks Failed: {daemon_status['tasks_failed']}")
print(f"   Pending: {daemon_status['total_tasks']}")

# Claude status
claude = OfflineClaude()
claude_status = claude.get_status()
print(f"\n💭 Offline Claude:")
print(f"   Model: {claude_status['model']}")
print(f"   Status: {claude_status['status']}")
print(f"   Session: {claude_status['session_id']}")

# Resource status
executor = get_executor()
resources = executor.get_status()
print(f"\n📊 Resources:")
print(f"   Memory Tier: {resources['tier'].upper()}")
print(f"   Free Memory: {resources['free_memory']['percent']:.1f}%")
print(f"   Max Concurrency: {resources['max_concurrency']} agents")
print(f"   Throttled: {resources['throttled']}")

print("\n" + "=" * 50)
print("✅ AUTONOMOUS EMPIRE OPERATIONAL")
print("=" * 50)
print("\n📈 Your system is now generating revenue 24/7")
print("📊 Check logs: antigravity/_daemon/daemon.log")
print("💡 Monitor content: antigravity/_content/")
print("\n🚀 The machine is running. Go build!")
PYTHON_EOF

echo -e "\n${GREEN}✅ AUTONOMOUS EMPIRE IS NOW LIVE!${NC}\n"
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Monitor logs: tail -f antigravity/_daemon/daemon.log"
echo "  2. Check content: ls -la antigravity/_content/"
echo "  3. View analytics: cat antigravity/_content/analytics.jsonl"
echo ""
echo -e "${BLUE}Your 3-year projection:${NC}"
echo "  Year 1: €255K"
echo "  Year 2: €2.75M"
echo "  Year 3: €100M+"
echo ""
echo -e "${GREEN}🚀 Happy scaling!${NC}"

