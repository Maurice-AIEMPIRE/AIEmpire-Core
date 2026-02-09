#!/bin/bash
# AI Empire - Automation Dashboard
# Zeigt Status aller Automation-Systeme

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}             AI EMPIRE - AUTOMATION DASHBOARD                ${CYAN}║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# System Info
echo -e "${BLUE}SYSTEM${NC}"
echo "  Time:     $(date)"
echo "  Python:   $(python3 --version 2>/dev/null || echo 'Not found')"
echo "  Docker:   $(docker --version 2>/dev/null | cut -d' ' -f3 || echo 'Not installed')"
echo ""

# Git Status
echo -e "${BLUE}GIT${NC}"
cd "${PROJECT_ROOT}"
echo "  Branch:   $(git branch --show-current 2>/dev/null || echo 'Unknown')"
echo "  Commit:   $(git log -1 --pretty=format:'%h - %s' 2>/dev/null || echo 'No commits')"
echo "  Changes:  $(git status --short 2>/dev/null | wc -l) files"
echo ""

# Workflow System
echo -e "${BLUE}WORKFLOW SYSTEM${NC}"
if [ -f "${PROJECT_ROOT}/workflow-system/state/current_state.json" ]; then
    echo -e "  ${GREEN}OK${NC} State file exists"
else
    echo -e "  ${YELLOW}--${NC} Not initialized (run: python workflow-system/orchestrator.py)"
fi

# Empire Brain
echo -e "${BLUE}EMPIRE BRAIN${NC}"
if [ -f "${PROJECT_ROOT}/workflow-system/state/brain_state.json" ]; then
    echo -e "  ${GREEN}OK${NC} Brain state exists"
else
    echo -e "  ${YELLOW}--${NC} Not started (run: python workflow-system/empire_brain.py)"
fi

# Ollama
echo -e "${BLUE}OLLAMA${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    models=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; [print(f'  - {m[\"name\"]}') for m in json.load(sys.stdin).get('models',[])]" 2>/dev/null || echo "  Could not list")
    echo -e "  ${GREEN}ONLINE${NC}"
    echo "$models"
else
    echo -e "  ${RED}OFFLINE${NC} (start: ollama serve)"
fi
echo ""

# Key Files
echo -e "${BLUE}KEY FILES${NC}"
files=(
    "workflow-system/ollama_engine.py:Ollama Engine"
    "workflow-system/agent_manager.py:Agent Manager"
    "workflow-system/knowledge_harvester.py:Knowledge Harvester"
    "workflow-system/empire_brain.py:Empire Brain"
    "workflow-system/orchestrator.py:Orchestrator"
    "workflow-system/cowork.py:Cowork Engine"
    "workflow-system/resource_guard.py:Resource Guard"
    "workflow-system/empire.py:Empire CLI"
)

for f in "${files[@]}"; do
    IFS=':' read -r path name <<< "$f"
    if [ -f "${PROJECT_ROOT}/${path}" ]; then
        echo -e "  ${GREEN}OK${NC} ${name}"
    else
        echo -e "  ${RED}!!${NC} ${name} MISSING"
    fi
done
echo ""

# Quick Commands
echo -e "${BLUE}COMMANDS${NC}"
echo "  python workflow-system/empire_brain.py --connect   # System Check"
echo "  python workflow-system/empire_brain.py --think     # Denk-Zyklus"
echo "  python workflow-system/empire_brain.py --revenue   # Revenue Analyse"
echo "  python workflow-system/empire.py status            # Empire Status"
echo "  python workflow-system/orchestrator.py --status    # Workflow Status"
echo "  python workflow-system/knowledge_harvester.py      # Knowledge Harvest"
echo ""
