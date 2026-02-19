#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# SKYBOT — One-Command Setup
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo ""
echo "══════════════════════════════════════════════"
echo "  SKYBOT — AI Agent Setup"
echo "══════════════════════════════════════════════"
echo ""

# ─── 1. Install Dependencies ────────────────────────────────────
echo "[1/4] Installing dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet 2>/dev/null || \
pip install -r "$SCRIPT_DIR/requirements.txt" --quiet
echo "  Dependencies: OK"

# ─── 2. Check .env ──────────────────────────────────────────────
echo "[2/4] Checking .env..."
ENV_FILE="$PROJECT_ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE" 2>/dev/null || touch "$ENV_FILE"
fi

# Check Telegram token
if grep -q "TELEGRAM_BOT_TOKEN=" "$ENV_FILE" && ! grep -q "your-telegram-bot-token" "$ENV_FILE"; then
    echo "  TELEGRAM_BOT_TOKEN: Found"
else
    echo ""
    echo "  Telegram Bot Token fehlt!"
    echo "  1. Telegram → @BotFather → /newbot"
    echo "  2. Token kopieren"
    echo ""
    read -p "  Token eingeben: " TOKEN
    if [ -n "$TOKEN" ]; then
        if grep -q "TELEGRAM_BOT_TOKEN=" "$ENV_FILE"; then
            sed -i.bak "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$TOKEN|" "$ENV_FILE"
        else
            echo "TELEGRAM_BOT_TOKEN=$TOKEN" >> "$ENV_FILE"
        fi
        echo "  Token gespeichert!"
    fi
fi

# Check Anthropic key
if grep -q "ANTHROPIC_API_KEY=sk-ant" "$ENV_FILE"; then
    echo "  ANTHROPIC_API_KEY: Found (Tool Use aktiv!)"
else
    echo "  ANTHROPIC_API_KEY: Nicht gesetzt"
    echo "    Ohne Key: Nur Chat (Ollama/Kimi)"
    echo "    Mit Key:  Voller Agent + 5 Tools"
    echo ""
    read -p "  Anthropic API Key eingeben (oder Enter zum Ueberspringen): " AKEY
    if [ -n "$AKEY" ]; then
        if grep -q "ANTHROPIC_API_KEY=" "$ENV_FILE"; then
            sed -i.bak "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$AKEY|" "$ENV_FILE"
        else
            echo "ANTHROPIC_API_KEY=$AKEY" >> "$ENV_FILE"
        fi
        echo "  Key gespeichert!"
    fi
fi

# ─── 3. Create Workspace ────────────────────────────────────────
echo "[3/4] Creating workspace..."
mkdir -p "$PROJECT_ROOT/skybot_workspace/websites"
echo "  Workspace: $PROJECT_ROOT/skybot_workspace/"

# ─── 4. Test Import ─────────────────────────────────────────────
echo "[4/4] Testing SkyBot import..."
cd "$PROJECT_ROOT"
if python3 -c "from skybot.agent import SkyBotAgent; print('  Import: OK')" 2>/dev/null; then
    echo ""
else
    echo "  Import failed — check error above"
    exit 1
fi

# ─── Start ───────────────────────────────────────────────────────
echo "══════════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  Starten:"
echo "    python3 -m skybot.bot"
echo ""
echo "  Oder im Hintergrund:"
echo "    nohup python3 -m skybot.bot > logs/skybot.log 2>&1 &"
echo "══════════════════════════════════════════════"
echo ""

if [ "$1" = "--start" ] || [ "$1" = "-s" ]; then
    echo "Starting SkyBot..."
    python3 -m skybot.bot
fi
