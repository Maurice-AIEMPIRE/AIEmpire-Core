#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# AIEmpire — Telegram Bridge Setup (One-Click)
# Prueft alles, installiert was fehlt, startet den Bot
# ═══════════════════════════════════════════════════════════════
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}  AIEmpire Telegram Bridge — Setup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# ─── 1. System-Check ─────────────────────────────────────────
echo -e "${YELLOW}[1/6] System-Check...${NC}"

# Python
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1)
    echo -e "  ${GREEN}✓${NC} Python: $PY_VER"
else
    echo -e "  ${RED}✗ Python3 nicht gefunden!${NC}"
    exit 1
fi

# pip
if python3 -m pip --version &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} pip verfuegbar"
else
    echo -e "  ${RED}✗ pip nicht gefunden! Installiere: python3 -m ensurepip${NC}"
    exit 1
fi

# ─── 2. Service-Check ────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/6] Services pruefen...${NC}"

# LiteLLM Proxy
if curl -s --max-time 3 http://127.0.0.1:4000/health >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} LiteLLM Proxy (:4000) — ONLINE"
else
    echo -e "  ${RED}✗${NC} LiteLLM Proxy (:4000) — OFFLINE"
    echo -e "    ${YELLOW}→ Starte: docker compose -f openclaw-config/docker-compose.yaml up -d${NC}"
fi

# Ollama
if curl -s --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    MODELS=$(curl -s http://127.0.0.1:11434/api/tags 2>/dev/null | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    print(', '.join(m['name'] for m in d.get('models',[])))
except: print('?')
" 2>/dev/null)
    echo -e "  ${GREEN}✓${NC} Ollama (:11434) — ONLINE"
    echo -e "    Modelle: $MODELS"
else
    echo -e "  ${RED}✗${NC} Ollama (:11434) — OFFLINE"
    echo -e "    ${YELLOW}→ Starte: ollama serve${NC}"
fi

# OpenClaw
if curl -s --max-time 3 http://127.0.0.1:18789/ >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} OpenClaw (:18789) — ONLINE"
else
    echo -e "  ${YELLOW}~${NC} OpenClaw (:18789) — nicht erreichbar (evtl. Websocket-only)"
fi

# ─── 3. Dependencies ─────────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/6] Python Dependencies...${NC}"

if python3 -c "import telegram" 2>/dev/null; then
    TG_VER=$(python3 -c "import telegram; print(telegram.__version__)" 2>/dev/null)
    echo -e "  ${GREEN}✓${NC} python-telegram-bot $TG_VER"
else
    echo -e "  ${YELLOW}~${NC} python-telegram-bot nicht installiert"
    echo -e "    Installiere..."
    python3 -m pip install "python-telegram-bot>=21.0" --quiet
    echo -e "  ${GREEN}✓${NC} python-telegram-bot installiert"
fi

if python3 -c "import httpx" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} httpx verfuegbar"
else
    python3 -m pip install httpx --quiet
    echo -e "  ${GREEN}✓${NC} httpx installiert"
fi

# ─── 4. .env pruefen / Telegram Token ────────────────────────
echo ""
echo -e "${YELLOW}[4/6] Telegram Konfiguration...${NC}"

# Erstelle .env falls nicht vorhanden
if [ ! -f "$ENV_FILE" ]; then
    echo -e "  ${YELLOW}~${NC} Keine .env gefunden — erstelle aus .env.example"
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
fi

# Pruefe ob Token schon drin ist
EXISTING_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)

if [ -n "$EXISTING_TOKEN" ] && [ "$EXISTING_TOKEN" != "your-telegram-bot-token" ]; then
    echo -e "  ${GREEN}✓${NC} Telegram Token gefunden (${EXISTING_TOKEN:0:10}...)"
else
    echo ""
    echo -e "  ${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "  ${BLUE}║  TELEGRAM BOT TOKEN BENOETIGT             ║${NC}"
    echo -e "  ${BLUE}║                                            ║${NC}"
    echo -e "  ${BLUE}║  1. Oeffne Telegram auf dem iPhone         ║${NC}"
    echo -e "  ${BLUE}║  2. Suche: @BotFather                      ║${NC}"
    echo -e "  ${BLUE}║  3. Sende: /newbot                         ║${NC}"
    echo -e "  ${BLUE}║  4. Name: AIEmpire                         ║${NC}"
    echo -e "  ${BLUE}║  5. Username: aiempire_maurice_bot          ║${NC}"
    echo -e "  ${BLUE}║  6. Kopiere den Token hier rein            ║${NC}"
    echo -e "  ${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
    read -rp "  Telegram Bot Token: " NEW_TOKEN

    if [ -z "$NEW_TOKEN" ]; then
        echo -e "  ${RED}Kein Token eingegeben. Abbruch.${NC}"
        exit 1
    fi

    # Token in .env schreiben/updaten
    if grep -q "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE" 2>/dev/null; then
        sed -i.bak "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$NEW_TOKEN|" "$ENV_FILE"
    else
        echo "TELEGRAM_BOT_TOKEN=$NEW_TOKEN" >> "$ENV_FILE"
    fi
    echo -e "  ${GREEN}✓${NC} Token gespeichert"
fi

# ─── 5. Chat-ID pruefen ──────────────────────────────────────
EXISTING_CHATID=$(grep "^TELEGRAM_ADMIN_CHAT_ID=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)

if [ -n "$EXISTING_CHATID" ] && [ "$EXISTING_CHATID" != "your-chat-id" ]; then
    echo -e "  ${GREEN}✓${NC} Admin Chat-ID: $EXISTING_CHATID"
else
    echo ""
    echo -e "  ${BLUE}Deine Telegram Chat-ID wird benoetigt.${NC}"
    echo -e "  ${BLUE}→ Suche @userinfobot in Telegram, sende /start${NC}"
    echo ""
    read -rp "  Deine Chat-ID (Zahl): " NEW_CHATID

    if [ -n "$NEW_CHATID" ]; then
        if grep -q "^TELEGRAM_ADMIN_CHAT_ID=" "$ENV_FILE" 2>/dev/null; then
            sed -i.bak "s|^TELEGRAM_ADMIN_CHAT_ID=.*|TELEGRAM_ADMIN_CHAT_ID=$NEW_CHATID|" "$ENV_FILE"
        else
            echo "TELEGRAM_ADMIN_CHAT_ID=$NEW_CHATID" >> "$ENV_FILE"
        fi
        echo -e "  ${GREEN}✓${NC} Chat-ID gespeichert"
    else
        echo -e "  ${YELLOW}~${NC} Keine Chat-ID — Bot ist fuer ALLE offen!"
    fi
fi

# Sicherstellen dass LiteLLM env vars drin sind
grep -q "^OPENAI_API_BASE=" "$ENV_FILE" 2>/dev/null || echo "OPENAI_API_BASE=http://127.0.0.1:4000" >> "$ENV_FILE"
grep -q "^OLLAMA_API_KEY=" "$ENV_FILE" 2>/dev/null || echo "OLLAMA_API_KEY=ollama-local" >> "$ENV_FILE"

# ─── 6. Bot starten ──────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/6] Telegram Bridge starten...${NC}"
echo ""

# Cleanup .env.bak
rm -f "$ENV_FILE.bak"

echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup komplett! Starte Bot...${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "  Stoppen:   Ctrl+C"
echo -e "  Permanent: ./scripts/telegram_service.sh start"
echo -e "  Logs:      ./scripts/telegram_service.sh logs"
echo ""

cd "$PROJECT_ROOT"

# Load .env
set -a
# shellcheck source=/dev/null
. "$ENV_FILE"
set +a

exec python3 telegram_bridge.py
