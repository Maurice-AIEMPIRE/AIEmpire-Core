#!/bin/bash
# AIEmpire-Core Session Start Hook
# Zeigt System-Status bei jedem Claude Code Start
# Konfiguriert in .claude/settings.json hooks.SessionStart

echo "================================================"
echo "  AI EMPIRE - SESSION START"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"

# Resource status
CPU_IDLE=$(top -bn1 2>/dev/null | grep "Cpu(s)" | awk '{print $8}' || echo "N/A")
RAM_INFO=$(free -h 2>/dev/null | grep Mem | awk '{printf "%s/%s (%s used)", $3, $2, $5}' || echo "N/A")
DISK_INFO=$(df -h / 2>/dev/null | tail -1 | awk '{printf "%s/%s (%s)", $3, $2, $5}' || echo "N/A")

echo ""
echo "  System:"
echo "    CPU idle: ${CPU_IDLE}%"
echo "    RAM: ${RAM_INFO}"
echo "    Disk: ${DISK_INFO}"

# Workflow status
if [ -f "/home/user/AIEmpire-Core/workflow-system/state/current_state.json" ]; then
    CYCLE=$(python3 -c "import json; d=json.load(open('/home/user/AIEmpire-Core/workflow-system/state/current_state.json')); print(d.get('cycle',0))" 2>/dev/null || echo "?")
    STEPS=$(python3 -c "import json; d=json.load(open('/home/user/AIEmpire-Core/workflow-system/state/current_state.json')); print(len(d.get('steps_completed',[])))" 2>/dev/null || echo "?")
    PATTERNS=$(python3 -c "import json; d=json.load(open('/home/user/AIEmpire-Core/workflow-system/state/current_state.json')); print(len(d.get('patterns',[])))" 2>/dev/null || echo "?")
    echo ""
    echo "  Workflow: Cycle #${CYCLE} | Steps: ${STEPS} | Patterns: ${PATTERNS}"
else
    echo ""
    echo "  Workflow: Not initialized (run: python workflow-system/orchestrator.py)"
fi

# Cowork status
if [ -f "/home/user/AIEmpire-Core/workflow-system/state/cowork_state.json" ]; then
    COWORK_CYCLES=$(python3 -c "import json; d=json.load(open('/home/user/AIEmpire-Core/workflow-system/state/cowork_state.json')); print(d.get('total_cycles',0))" 2>/dev/null || echo "?")
    COWORK_FOCUS=$(python3 -c "import json; d=json.load(open('/home/user/AIEmpire-Core/workflow-system/state/cowork_state.json')); print(d.get('active_focus','?'))" 2>/dev/null || echo "?")
    echo "  Cowork: ${COWORK_CYCLES} cycles | Focus: ${COWORK_FOCUS}"
else
    echo "  Cowork: Not started (run: python workflow-system/cowork.py)"
fi

# Git status
BRANCH=$(git -C /home/user/AIEmpire-Core branch --show-current 2>/dev/null || echo "?")
UNCOMMITTED=$(git -C /home/user/AIEmpire-Core status --porcelain 2>/dev/null | wc -l | tr -d ' ')
echo ""
echo "  Git: ${BRANCH} | ${UNCOMMITTED} uncommitted changes"

echo ""
echo "  Quick commands:"
echo "    python workflow-system/orchestrator.py --status"
echo "    python workflow-system/cowork.py --status"
echo "    python workflow-system/resource_guard.py"
echo "================================================"
