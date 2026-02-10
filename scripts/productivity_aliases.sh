#!/bin/bash
# 🚀 AI Empire — Productivity Aliases
# Source this file in your ~/.zshrc or ~/.bashrc to get superpowers.

# 1. Smart Launcher (The "ai" command)
# Checks system health, memory, and launches the right model environment
alias ai="python3 $PWD/scripts/smart_ollama_launch.py"

# 2. Godmode Router shortcuts
# Quickly dispatch tasks to specific agents
alias fix="python3 $PWD/antigravity/godmode_router.py fix"
alias plan="python3 $PWD/antigravity/godmode_router.py architecture"
alias code="python3 $PWD/antigravity/godmode_router.py code"
alias qa="python3 $PWD/antigravity/godmode_router.py qa"

# 3. Mission Control
# One command to see everything
alias status="python3 $PWD/mission_control.py"
alias mission="python3 $PWD/mission_control.py"

# 4. Memory Management
# Quick access to the monitor and cleaning tools
alias mem="bash $PWD/scripts/memory_monitor.sh"
alias clean="python3 $PWD/scripts/smart_ollama_launch.py --clean"
alias fixmem="bash $PWD/QUICK_MEMORY_FIX.sh"

# 5. Git Productivity with AI
# Auto-generate commit messages (using local tiny model)
function gca() {
    diff=$(git diff --cached)
    if [ -z "$diff" ]; then
        echo "No staged changes."
        return 1
    fi
    msg=$(echo "$diff" | ollama run phi:q4 "Generate a short, semantic commit message (e.g. feat: ..., fix: ...) for this diff. Output ONLY the message.")
    echo "Commit message: $msg"
    git commit -m "$msg"
}

# 6. Quick Knowledge Retrieval
# Search your codebase/docs using embedding search (if configured) or grep
function ask() {
    # Simple grep-based search for now, can be upgraded to semantic search later
    grep -r "$1" docs/ src/ antigravity/ | head -n 20
}

echo "✅ AI Empire Aliases Loaded!"
echo "   ai    -> Smart Launcher"
echo "   fix   -> Fix Agent"
echo "   plan  -> Architect Agent"
echo "   code  -> Coding Agent"
echo "   qa    -> QA/Review Agent"
echo "   status-> Mission Control Dashboard"
echo "   mem   -> Memory Monitor"
echo "   clean -> Free RAM"
echo "   gca   -> AI Commit"
