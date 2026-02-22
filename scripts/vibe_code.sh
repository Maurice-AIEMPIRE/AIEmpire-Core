#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Vibe Code Wrapper — OpenClaw → Codex CLI integration
# Instead of using Claude Code directly, tell your OpenClaw
# what to build and it uses Codex CLI to implement it.
# ═══════════════════════════════════════════════════════════════
#
# Usage:
#   ./scripts/vibe_code.sh "Build a FastAPI endpoint for user metrics"
#   ./scripts/vibe_code.sh "Fix the import error in empire_engine.py"
#   ./scripts/vibe_code.sh  # Interactive mode
#
# Requirements:
#   - Codex CLI installed (npm install -g @openai/codex)
#   - Or use local Ollama as backend
#
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VIBE_LOG="${PROJECT_ROOT}/logs/vibe_code.log"

mkdir -p "${PROJECT_ROOT}/logs"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}  VIBE CODE — OpenClaw Code Generator  ${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"

# Check for available coding tools
CODEX_AVAILABLE=false
CLAUDE_AVAILABLE=false
OLLAMA_AVAILABLE=false

if command -v codex &>/dev/null; then
    CODEX_AVAILABLE=true
    echo -e "${GREEN}  [OK] Codex CLI available${NC}"
fi

if command -v claude &>/dev/null; then
    CLAUDE_AVAILABLE=true
    echo -e "${GREEN}  [OK] Claude Code available${NC}"
fi

if curl -sf http://localhost:11434/api/tags &>/dev/null; then
    OLLAMA_AVAILABLE=true
    echo -e "${GREEN}  [OK] Ollama available (local, free)${NC}"
fi

echo ""

# Get the prompt
if [ $# -gt 0 ]; then
    PROMPT="$*"
else
    echo -e "${YELLOW}What should I build? (describe in natural language)${NC}"
    read -r PROMPT
fi

if [ -z "$PROMPT" ]; then
    echo "No prompt provided. Exiting."
    exit 1
fi

echo ""
echo -e "${BLUE}Prompt:${NC} $PROMPT"
echo -e "${BLUE}Project:${NC} $PROJECT_ROOT"
echo ""

# Log the request
echo "$(date -Iseconds) | VIBE: $PROMPT" >> "$VIBE_LOG"

# Route to best available tool
if [ "$CODEX_AVAILABLE" = true ]; then
    echo -e "${GREEN}Using Codex CLI...${NC}"
    cd "$PROJECT_ROOT"
    codex "$PROMPT"
elif [ "$CLAUDE_AVAILABLE" = true ]; then
    echo -e "${GREEN}Using Claude Code...${NC}"
    cd "$PROJECT_ROOT"
    claude -p "$PROMPT"
elif [ "$OLLAMA_AVAILABLE" = true ]; then
    echo -e "${GREEN}Using Ollama (qwen2.5-coder:14b)...${NC}"
    curl -sf http://localhost:11434/api/generate \
        -d "{
            \"model\": \"qwen2.5-coder:14b\",
            \"prompt\": \"You are a senior developer. Implement the following in the AIEmpire-Core project:\n\n$PROMPT\n\nProvide complete, working code with file paths.\",
            \"stream\": false
        }" | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','No response'))"
else
    echo "No coding tool available. Install one of:"
    echo "  npm install -g @openai/codex"
    echo "  brew install claude-code"
    echo "  brew install ollama && ollama pull qwen2.5-coder:14b"
    exit 1
fi

echo ""
echo -e "${GREEN}Done!${NC}"
echo "$(date -Iseconds) | VIBE COMPLETE: $PROMPT" >> "$VIBE_LOG"
