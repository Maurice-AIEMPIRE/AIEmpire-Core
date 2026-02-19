#!/bin/bash
# ============================================================
# AIEmpire Claude Code Launcher
# One-Click: Terminal CLI + Browser Web
# Double-click oder aus dem Dock starten
# ============================================================

REPO_DIR="$HOME/AIEmpire-Core"
CLAUDE_WEB_URL="https://claude.ai/code"
ICON="🚀"

# Farben
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

clear
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════╗"
echo "║       AIEmpire — Claude Code Launcher    ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "  ${CYAN}[1]${NC}  Terminal (CLI) — Claude im Repo oeffnen"
echo -e "  ${CYAN}[2]${NC}  Browser  (Web) — claude.ai/code oeffnen"
echo -e "  ${CYAN}[3]${NC}  Beides gleichzeitig"
echo -e "  ${CYAN}[4]${NC}  Terminal + iCloud ARAG Ordner lesen"
echo ""
echo -e "  ${YELLOW}[q]${NC}  Beenden"
echo ""
read -p "  Auswahl: " choice

launch_terminal() {
    echo -e "\n${GREEN}▶ Starte Claude Code CLI in ${REPO_DIR}...${NC}\n"
    if [ ! -d "$REPO_DIR" ]; then
        echo -e "${YELLOW}⚠ Repo nicht gefunden unter $REPO_DIR${NC}"
        echo "  Klone es zuerst: git clone https://github.com/Maurice-AIEMPIRE/AIEmpire-Core.git ~/AIEmpire-Core"
        return 1
    fi

    if ! command -v claude &> /dev/null; then
        echo -e "${YELLOW}⚠ Claude Code CLI nicht installiert.${NC}"
        echo "  Installiere: npm install -g @anthropic-ai/claude-code"
        return 1
    fi

    cd "$REPO_DIR"
    echo -e "${GREEN}✓ Verzeichnis: $(pwd)${NC}"
    echo -e "${GREEN}✓ Branch: $(git branch --show-current 2>/dev/null || echo 'kein git')${NC}"
    echo ""
    exec claude
}

launch_browser() {
    echo -e "\n${GREEN}▶ Oeffne Claude Code Web...${NC}\n"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$CLAUDE_WEB_URL"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$CLAUDE_WEB_URL" 2>/dev/null || echo "Oeffne: $CLAUDE_WEB_URL"
    fi
    echo -e "${GREEN}✓ Browser geoeffnet: ${CLAUDE_WEB_URL}${NC}"
}

launch_both() {
    launch_browser
    sleep 1
    launch_terminal
}

launch_terminal_arag() {
    echo -e "\n${GREEN}▶ Starte Claude Code CLI mit ARAG-Kontext...${NC}\n"
    if [ ! -d "$REPO_DIR" ]; then
        echo -e "${YELLOW}⚠ Repo nicht gefunden unter $REPO_DIR${NC}"
        return 1
    fi

    if ! command -v claude &> /dev/null; then
        echo -e "${YELLOW}⚠ Claude Code CLI nicht installiert.${NC}"
        echo "  Installiere: npm install -g @anthropic-ai/claude-code"
        return 1
    fi

    # iCloud ARAG Ordner finden
    ICLOUD_BASE="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
    ARAG_DIR=""

    if [ -d "$ICLOUD_BASE" ]; then
        # Suche nach ARAG / Rechtsschutz Ordner
        ARAG_DIR=$(find "$ICLOUD_BASE" -maxdepth 3 -type d \( -iname "*arag*" -o -iname "*rechtsschutz*" \) 2>/dev/null | head -1)
    fi

    cd "$REPO_DIR"

    if [ -n "$ARAG_DIR" ]; then
        echo -e "${GREEN}✓ ARAG-Ordner gefunden: ${ARAG_DIR}${NC}"
        echo -e "${GREEN}✓ Starte Claude mit Kontext...${NC}\n"
        exec claude "Lies alle Dateien in ${ARAG_DIR} und fuelle alle [MISSING]-Felder in legal/memory/RECHTSSTREIT_GEDAECHTNIS.md und legal/drafts/DRAFT_MAIL_RA_SEIDEL_GEGENANGEBOT_2026-02-19.md"
    else
        echo -e "${YELLOW}⚠ ARAG-Ordner nicht automatisch gefunden in iCloud.${NC}"
        echo -e "  Starte Claude normal — sag ihm manuell wo der Ordner liegt.\n"
        exec claude
    fi
}

case $choice in
    1) launch_terminal ;;
    2) launch_browser ;;
    3) launch_both ;;
    4) launch_terminal_arag ;;
    q|Q) echo -e "\n${GREEN}Bis spaeter! 👋${NC}\n"; exit 0 ;;
    *) echo -e "\n${YELLOW}Ungueltige Auswahl.${NC}\n"; exit 1 ;;
esac
