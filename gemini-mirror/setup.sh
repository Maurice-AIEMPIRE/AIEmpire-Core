#!/bin/bash
# ============================================================
# Gemini Mirror - Setup Script
# ============================================================
# Sets up the dual-system architecture.
# Run this once on both Mac (Claude) and Cloud (Gemini).
# ============================================================

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              GEMINI MIRROR - SETUP                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 1. Check Python
echo -e "${YELLOW}[1/5] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON=$(command -v python3)
    echo -e "  ${GREEN}✓${NC} Python3 found: $($PYTHON --version)"
else
    echo -e "  ${RED}✗${NC} Python3 not found. Install it first."
    exit 1
fi

# 2. Check dependencies
echo -e "${YELLOW}[2/5] Checking dependencies...${NC}"
$PYTHON -c "import aiohttp" 2>/dev/null && echo -e "  ${GREEN}✓${NC} aiohttp" || {
    echo -e "  ${YELLOW}→${NC} Installing aiohttp..."
    pip3 install aiohttp --quiet
}
$PYTHON -c "import yaml" 2>/dev/null && echo -e "  ${GREEN}✓${NC} pyyaml" || {
    echo -e "  ${YELLOW}→${NC} Installing pyyaml..."
    pip3 install pyyaml --quiet
}

# 3. Check Gemini API Key
echo -e "${YELLOW}[3/5] Checking Gemini API Key...${NC}"
if [ -n "$GEMINI_API_KEY" ]; then
    echo -e "  ${GREEN}✓${NC} GEMINI_API_KEY is set (${GEMINI_API_KEY:0:8}...)"
else
    echo -e "  ${RED}✗${NC} GEMINI_API_KEY not set!"
    echo ""
    echo "  Get your key at: https://aistudio.google.com/apikey"
    echo ""
    echo "  Then add to your shell config:"
    echo "    export GEMINI_API_KEY='your-key-here'"
    echo ""
    echo "  Or create a .env file in the project root:"
    echo "    echo 'GEMINI_API_KEY=your-key-here' >> ${PROJECT_DIR}/.env"
    echo ""
fi

# 4. Create state directory
echo -e "${YELLOW}[4/5] Creating state directory...${NC}"
mkdir -p "$SCRIPT_DIR/state"
echo -e "  ${GREEN}✓${NC} State directory ready"

# 5. Seed initial knowledge
echo -e "${YELLOW}[5/5] Seeding initial knowledge...${NC}"
cd "$SCRIPT_DIR"
if [ -n "$GEMINI_API_KEY" ]; then
    $PYTHON -c "
import sys
sys.path.insert(0, '.')
from digital_memory import DigitalMemory
mem = DigitalMemory()
mem.seed_initial_knowledge()
stats = mem.stats()
print(f'  Seeded {stats[\"total_memories\"]} memories across {sum(1 for v in stats[\"by_category\"].values() if v[\"count\"] > 0)} categories')
"
else
    echo -e "  ${YELLOW}→${NC} Skipped (no API key). Run --seed manually later."
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  SETUP COMPLETE                                            ║"
echo "║                                                            ║"
echo "║  Quick Start:                                              ║"
echo "║    python gemini-mirror/mirror_daemon.py --status          ║"
echo "║    python gemini-mirror/mirror_daemon.py --seed            ║"
echo "║    python gemini-mirror/mirror_daemon.py --questions       ║"
echo "║    python gemini-mirror/mirror_daemon.py --daemon          ║"
echo "║                                                            ║"
echo "║  Or via Empire CLI:                                        ║"
echo "║    python workflow-system/empire.py gemini status          ║"
echo "║    python workflow-system/empire.py gemini questions       ║"
echo "║    python workflow-system/empire.py gemini evolve          ║"
echo "║    python workflow-system/empire.py gemini daemon          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
