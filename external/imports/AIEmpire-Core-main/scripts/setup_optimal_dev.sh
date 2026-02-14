#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# OPTIMAL DEV SETUP — AIEmpire-Core
# ══════════════════════════════════════════════════════════════════════════════
#
# Installiert alle Open-Source Tools die du brauchst.
# Kein Visual Studio noetig — alles laeuft ueber Terminal + Ollama + Claude.
#
# Stack:
#   Editor:      VSCodium (Open-Source VS Code ohne Microsoft Telemetry)
#   Terminal:     iTerm2 (besser als macOS Terminal)
#   AI Local:     Ollama + qwen2.5-coder (14B + 7B)
#   AI Cloud:     Claude Code CLI (fuer kritische Tasks)
#   Monitoring:   btop (System) + lazygit (Git TUI)
#   Automation:   n8n (Open-Source Zapier)
#   Database:     PostgreSQL + Redis
#   Container:    Docker Desktop oder Podman (Open-Source)
#   Python:       pyenv + Python 3.12
#
# Usage:
#   chmod +x scripts/setup_optimal_dev.sh
#   ./scripts/setup_optimal_dev.sh
#
# ══════════════════════════════════════════════════════════════════════════════

set -e

G='\033[0;32m'
Y='\033[1;33m'
B='\033[0;34m'
C='\033[0;36m'
W='\033[1;37m'
N='\033[0m'

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║    OPTIMAL DEV SETUP — AIEmpire-Core (100% Open Source)  ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""

# ─── Check Homebrew ───────────────────────────────────────────────────────────
if ! command -v brew &>/dev/null; then
    echo -e "${Y}Homebrew nicht gefunden — installiere...${N}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo -e "${C}═══ CORE TOOLS ═══${N}"

# ─── Git (falls nicht vorhanden) ──────────────────────────────────────────────
if command -v git &>/dev/null; then
    echo -e "  ${G}[OK]${N} git $(git --version | cut -d' ' -f3)"
else
    echo -e "  ${Y}[INSTALL]${N} git..."
    brew install git
fi

# ─── Python (via pyenv fuer Version-Management) ──────────────────────────────
if command -v pyenv &>/dev/null; then
    echo -e "  ${G}[OK]${N} pyenv $(pyenv --version | cut -d' ' -f2)"
else
    echo -e "  ${Y}[INSTALL]${N} pyenv..."
    brew install pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
    echo 'eval "$(pyenv init --path)"' >> ~/.zshrc
fi

if command -v python3 &>/dev/null; then
    echo -e "  ${G}[OK]${N} python3 $(python3 --version | cut -d' ' -f2)"
else
    echo -e "  ${Y}[INSTALL]${N} Python 3.12..."
    pyenv install 3.12
    pyenv global 3.12
fi

# ─── Node.js (fuer CRM + n8n) ────────────────────────────────────────────────
if command -v node &>/dev/null; then
    echo -e "  ${G}[OK]${N} node $(node --version)"
else
    echo -e "  ${Y}[INSTALL]${N} Node.js..."
    brew install node
fi

echo ""
echo -e "${C}═══ AI TOOLS (OPEN SOURCE + KOSTENLOS) ═══${N}"

# ─── Ollama (Lokale LLMs, kostenlos) ─────────────────────────────────────────
if command -v ollama &>/dev/null; then
    echo -e "  ${G}[OK]${N} ollama"
else
    echo -e "  ${Y}[INSTALL]${N} Ollama..."
    brew install ollama
fi

# ─── Ollama Models ────────────────────────────────────────────────────────────
echo -e "  ${B}[INFO]${N} Pulling AI Models (falls nicht vorhanden)..."
echo -e "  ${B}[INFO]${N} Das dauert beim ersten Mal 5-15 Minuten..."

# Start Ollama if not running
if ! curl -s http://localhost:11434/api/version &>/dev/null; then
    ollama serve &>/dev/null &
    sleep 3
fi

# Pull models (skip if already present)
for model in "qwen2.5-coder:7b" "qwen2.5-coder:14b" "deepseek-r1:7b"; do
    if ollama list 2>/dev/null | grep -q "$model"; then
        echo -e "  ${G}[OK]${N} Model: $model"
    else
        echo -e "  ${Y}[PULL]${N} Model: $model (einmalig)..."
        ollama pull "$model" || echo -e "  ${Y}[SKIP]${N} $model konnte nicht geladen werden"
    fi
done

echo ""
echo -e "${C}═══ EDITOR (OPEN SOURCE — KEIN VS CODE NOETIG) ═══${N}"

# ─── VSCodium (VS Code ohne Microsoft Telemetry) ─────────────────────────────
if [ -d "/Applications/VSCodium.app" ] || command -v codium &>/dev/null; then
    echo -e "  ${G}[OK]${N} VSCodium (Open-Source VS Code)"
else
    echo -e "  ${Y}[INSTALL]${N} VSCodium..."
    brew install --cask vscodium || echo -e "  ${Y}[SKIP]${N} VSCodium (optional)"
fi

echo ""
echo -e "${C}═══ TERMINAL TOOLS ═══${N}"

# ─── btop (System-Monitor) ───────────────────────────────────────────────────
if command -v btop &>/dev/null; then
    echo -e "  ${G}[OK]${N} btop (System-Monitor)"
else
    echo -e "  ${Y}[INSTALL]${N} btop..."
    brew install btop
fi

# ─── lazygit (Git TUI — viel besser als git CLI) ─────────────────────────────
if command -v lazygit &>/dev/null; then
    echo -e "  ${G}[OK]${N} lazygit (Git TUI)"
else
    echo -e "  ${Y}[INSTALL]${N} lazygit..."
    brew install lazygit
fi

# ─── jq (JSON processing) ────────────────────────────────────────────────────
if command -v jq &>/dev/null; then
    echo -e "  ${G}[OK]${N} jq (JSON processor)"
else
    echo -e "  ${Y}[INSTALL]${N} jq..."
    brew install jq
fi

# ─── ripgrep (schneller als grep) ────────────────────────────────────────────
if command -v rg &>/dev/null; then
    echo -e "  ${G}[OK]${N} ripgrep (rg)"
else
    echo -e "  ${Y}[INSTALL]${N} ripgrep..."
    brew install ripgrep
fi

# ─── fd (schneller als find) ─────────────────────────────────────────────────
if command -v fd &>/dev/null; then
    echo -e "  ${G}[OK]${N} fd (file finder)"
else
    echo -e "  ${Y}[INSTALL]${N} fd..."
    brew install fd
fi

echo ""
echo -e "${C}═══ DATABASES ═══${N}"

# ─── Redis ────────────────────────────────────────────────────────────────────
if command -v redis-server &>/dev/null; then
    echo -e "  ${G}[OK]${N} Redis"
else
    echo -e "  ${Y}[INSTALL]${N} Redis..."
    brew install redis
fi

# ─── PostgreSQL ───────────────────────────────────────────────────────────────
if command -v psql &>/dev/null; then
    echo -e "  ${G}[OK]${N} PostgreSQL"
else
    echo -e "  ${Y}[INSTALL]${N} PostgreSQL..."
    brew install postgresql@16
fi

echo ""
echo -e "${C}═══ PYTHON PACKAGES ═══${N}"

# ─── Core Python packages ────────────────────────────────────────────────────
pip3 install --quiet --break-system-packages \
    httpx aiohttp fastapi uvicorn \
    pyyaml python-dotenv \
    ruff pytest \
    2>/dev/null && echo -e "  ${G}[OK]${N} Python packages installiert" \
    || echo -e "  ${Y}[WARN]${N} Einige Python packages konnten nicht installiert werden"

echo ""
echo -e "${C}═══ BOMBPROOF AUTOSTART ═══${N}"

# ─── LaunchAgent installieren ─────────────────────────────────────────────────
PLIST_SRC="$(dirname "$0")/com.aiempire.bombproof.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.aiempire.bombproof.plist"

if [ -f "$PLIST_SRC" ]; then
    mkdir -p "$HOME/Library/LaunchAgents"

    # Update paths in plist
    REAL_PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
    sed "s|~/AIEmpire-Core|$REAL_PROJECT_DIR|g" "$PLIST_SRC" | \
    sed "s|/Users/maurice|$HOME|g" > "$PLIST_DEST"

    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    launchctl load "$PLIST_DEST" 2>/dev/null && \
        echo -e "  ${G}[OK]${N} LaunchAgent installiert (Autostart bei Boot)" || \
        echo -e "  ${Y}[WARN]${N} LaunchAgent konnte nicht geladen werden"
else
    echo -e "  ${Y}[SKIP]${N} LaunchAgent plist nicht gefunden"
fi

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${W}╔═══════════════════════════════════════════════════════════╗${N}"
echo -e "${W}║                 SETUP COMPLETE                            ║${N}"
echo -e "${W}╠═══════════════════════════════════════════════════════════╣${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}║  Dein Stack (100% Open Source):                           ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}║  AI Lokal:   Ollama + Qwen2.5 + DeepSeek R1              ║${N}"
echo -e "${W}║  AI Cloud:   Claude Pro + Google AI + ChatGPT             ║${N}"
echo -e "${W}║  Editor:     VSCodium (oder Claude Code CLI)              ║${N}"
echo -e "${W}║  Git:        lazygit + GitHub                             ║${N}"
echo -e "${W}║  Monitor:    btop + Resource Guard v2                     ║${N}"
echo -e "${W}║  DB:         PostgreSQL + Redis                           ║${N}"
echo -e "${W}║  Autostart:  LaunchAgent (bombensicher)                   ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}║  Du brauchst KEIN Visual Studio!                          ║${N}"
echo -e "${W}║  Claude Code + Ollama + VSCodium = alles was du brauchst  ║${N}"
echo -e "${W}║                                                           ║${N}"
echo -e "${W}╚═══════════════════════════════════════════════════════════╝${N}"
echo ""
echo -e "  Naechste Schritte:"
echo -e "  ${C}1.${N} Terminal neustarten (oder: source ~/.zshrc)"
echo -e "  ${C}2.${N} ./scripts/bombproof_startup.sh  (System starten)"
echo -e "  ${C}3.${N} python3 scripts/auto_repair.py   (System testen)"
echo -e "  ${C}4.${N} Geld verdienen!"
echo ""
