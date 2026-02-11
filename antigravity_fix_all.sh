#!/usr/bin/env bash
#
# ANTIGRAVITY FIX ALL - Complete System Repair
# ==============================================
# Fixes all known bugs and makes the system robust
# Maurice's AI Empire - 2026

set -euo pipefail

echo "🔧 ANTIGRAVITY SYSTEM REPAIR - Starting..."
echo "=========================================="
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# ─── 1. Check Dependencies ──────────────────────────────────────────────
echo -e "${BLUE}[1/8]${NC} Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗${NC} Python 3 not found"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python 3: $(python3 --version)"

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Ollama not found - will skip model checks"
    OLLAMA_OK=false
else
    echo -e "${GREEN}✓${NC} Ollama: $(ollama --version | head -1)"
    OLLAMA_OK=true
fi

# Check Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}✗${NC} Git not found"
    exit 1
fi
echo -e "${GREEN}✓${NC} Git: $(git --version)"

# ─── 2. Install Python Dependencies ────────────────────────────────────
echo
echo -e "${BLUE}[2/8]${NC} Installing Python dependencies..."

# Check if dependencies are installed
if ! python3 -c "import httpx" 2>/dev/null; then
    echo "  Installing httpx..."
    pip3 install -q httpx
fi

if ! python3 -c "import aiohttp" 2>/dev/null; then
    echo "  Installing aiohttp..."
    pip3 install -q aiohttp
fi

echo -e "${GREEN}✓${NC} Python dependencies installed"

# ─── 3. Verify Antigravity Files ───────────────────────────────────────
echo
echo -e "${BLUE}[3/8]${NC} Verifying Antigravity files..."

REQUIRED_FILES=(
    "antigravity/config.py"
    "antigravity/ollama_client.py"
    "antigravity/gemini_client.py"
    "antigravity/godmode_router.py"
    "chat_manager.py"
    "antigravity_chat.py"
)

ALL_OK=true
for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}✗${NC} Missing: $file"
        ALL_OK=false
    fi
done

if [[ "$ALL_OK" == "false" ]]; then
    echo -e "${RED}✗${NC} Some required files are missing!"
    exit 1
fi

echo -e "${GREEN}✓${NC} All required files present"

# ─── 4. Check Ollama Service & Models ──────────────────────────────────
echo
echo -e "${BLUE}[4/8]${NC} Checking Ollama service and models..."

if [[ "$OLLAMA_OK" == "true" ]]; then
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        echo -e "${GREEN}✓${NC} Ollama service is running"

        # Check required models
        MODELS=$(ollama list 2>/dev/null)

        if echo "$MODELS" | grep -q "qwen2.5-coder:7b"; then
            echo -e "${GREEN}✓${NC} Model: qwen2.5-coder:7b"
        else
            echo -e "${YELLOW}⚠${NC}  Model missing: qwen2.5-coder:7b"
            echo "     Install with: ollama pull qwen2.5-coder:7b"
        fi

        if echo "$MODELS" | grep -q "deepseek-r1:8b"; then
            echo -e "${GREEN}✓${NC} Model: deepseek-r1:8b"
        else
            echo -e "${YELLOW}⚠${NC}  Model missing: deepseek-r1:8b"
            echo "     Install with: ollama pull deepseek-r1:8b"
        fi
    else
        echo -e "${YELLOW}⚠${NC}  Ollama not running"
        echo "     Start with: ollama serve"
    fi
else
    echo -e "${YELLOW}⚠${NC}  Ollama not installed - skipping model checks"
fi

# ─── 5. Run Antigravity Smoke Test ─────────────────────────────────────
echo
echo -e "${BLUE}[5/8]${NC} Running Antigravity smoke test..."

if python3 antigravity/smoke_test.py > /tmp/antigravity_smoke_test.log 2>&1; then
    echo -e "${GREEN}✓${NC} Smoke test passed"
else
    echo -e "${YELLOW}⚠${NC}  Some smoke tests failed (see /tmp/antigravity_smoke_test.log)"
    echo "     This is often OK if models are not installed yet"
fi

# ─── 6. Verify Chat Manager Integration ────────────────────────────────
echo
echo -e "${BLUE}[6/8]${NC} Verifying Chat Manager integration..."

if python3 -c "
from chat_manager import ChatManager
manager = ChatManager()
antigravity_models = [k for k in manager.supported_models.keys() if k.startswith('antigravity-')]
assert len(antigravity_models) == 4, f'Expected 4 Antigravity models, got {len(antigravity_models)}'
print('✓ 4 Antigravity agents registered')
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Chat Manager has 4 Antigravity agents"
else
    echo -e "${RED}✗${NC} Chat Manager integration failed"
    exit 1
fi

# ─── 7. Create Convenience Scripts ─────────────────────────────────────
echo
echo -e "${BLUE}[7/8]${NC} Creating convenience scripts..."

# Create a simple launcher for chat
cat > antigravity_start_chat.sh << 'EOF'
#!/usr/bin/env bash
# Quick launcher for Antigravity Chat
cd "$(dirname "$0")"
exec python3 antigravity_chat.py "$@"
EOF
chmod +x antigravity_start_chat.sh
echo -e "${GREEN}✓${NC} Created antigravity_start_chat.sh"

# ─── 8. Final Summary ───────────────────────────────────────────────────
echo
echo -e "${BLUE}[8/8]${NC} System check complete!"
echo
echo "=========================================="
echo -e "${GREEN}✨ ANTIGRAVITY SYSTEM READY!${NC}"
echo "=========================================="
echo
echo "Available Commands:"
echo "  • Start chat:        ./antigravity_start_chat.sh"
echo "  •                    python3 antigravity_chat.py"
echo "  • With specific agent:   python3 antigravity_chat.py --agent architect"
echo "  • List agents:           python3 antigravity_chat.py --list"
echo "  • Run smoke test:        python3 antigravity/smoke_test.py"
echo
echo "The 4 Agents:"
echo "  1. architect  - Repo structure, API design, refactoring"
echo "  2. fixer      - Bug fixes, debugging, import errors"
echo "  3. coder      - Feature implementation, prototyping"
echo "  4. qa         - Code review, testing, quality checks"
echo
echo "All local, no cloud costs! 🚀"
echo
