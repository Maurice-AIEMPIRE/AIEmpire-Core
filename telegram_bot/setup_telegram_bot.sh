#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# EMPIRE TELEGRAM BOT — One-Command Setup
# ═══════════════════════════════════════════════════════════════
# Dieses Script:
#   1. Installiert aiohttp (einzige Dependency)
#   2. Prueft .env auf TELEGRAM_BOT_TOKEN
#   3. Aktiviert SSH (fuer Terminus)
#   4. Startet den Bot als Background-Service
#
# Usage: bash telegram_bot/setup_telegram_bot.sh
# ═══════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BOT_SCRIPT="$SCRIPT_DIR/empire_bot.py"

echo ""
echo "══════════════════════════════════════════════"
echo "  EMPIRE TELEGRAM BOT — Setup"
echo "══════════════════════════════════════════════"
echo ""

# ─── Step 1: Python Dependencies ────────────────────────────────
echo "[1/5] Pruefe Python Dependencies..."
if python3 -c "import aiohttp" 2>/dev/null; then
    echo "  aiohttp: OK"
else
    echo "  Installiere aiohttp..."
    pip3 install aiohttp --quiet 2>/dev/null || pip install aiohttp --quiet
    echo "  aiohttp: Installiert"
fi

# ─── Step 2: Check .env ─────────────────────────────────────────
echo "[2/5] Pruefe .env..."
ENV_FILE="$PROJECT_ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "  .env nicht gefunden — erstelle aus .env.example..."
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
    else
        touch "$ENV_FILE"
    fi
fi

# Check for Telegram token
if grep -q "TELEGRAM_BOT_TOKEN=" "$ENV_FILE" && ! grep -q "your-telegram-bot-token" "$ENV_FILE"; then
    echo "  TELEGRAM_BOT_TOKEN: Gefunden"
else
    echo ""
    echo "  ╔═══════════════════════════════════════════════╗"
    echo "  ║  TELEGRAM TOKEN FEHLT!                        ║"
    echo "  ║                                               ║"
    echo "  ║  1. Oeffne Telegram → @BotFather              ║"
    echo "  ║  2. Sende: /newbot                            ║"
    echo "  ║  3. Name: AIEmpire Bot                        ║"
    echo "  ║  4. Kopiere den Token                         ║"
    echo "  ╚═══════════════════════════════════════════════╝"
    echo ""
    read -p "  Telegram Bot Token eingeben: " TOKEN
    if [ -n "$TOKEN" ]; then
        # Replace or add token
        if grep -q "TELEGRAM_BOT_TOKEN=" "$ENV_FILE"; then
            sed -i.bak "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$TOKEN|" "$ENV_FILE"
        else
            echo "" >> "$ENV_FILE"
            echo "# --- Telegram Bot ---" >> "$ENV_FILE"
            echo "TELEGRAM_BOT_TOKEN=$TOKEN" >> "$ENV_FILE"
        fi
        echo "  Token gespeichert!"
    else
        echo "  WARNUNG: Kein Token eingegeben. Bot kann nicht starten."
        echo "  Trage spaeter manuell ein: TELEGRAM_BOT_TOKEN=xxx in .env"
    fi
fi

# ─── Step 3: Enable SSH (for Terminus) ──────────────────────────
echo "[3/5] Pruefe SSH (fuer Terminus App)..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    SSH_STATUS=$(sudo systemsetup -getremotelogin 2>/dev/null || echo "unknown")
    if echo "$SSH_STATUS" | grep -qi "on"; then
        echo "  SSH: Bereits aktiv"
    else
        echo "  SSH aktivieren (fuer Terminus-Zugriff)..."
        echo "  (Braucht Admin-Passwort)"
        sudo systemsetup -setremotelogin on 2>/dev/null || echo "  SSH manuell aktivieren: Einstellungen → Teilen → Entfernte Anmeldung"
    fi

    # Show IP
    LOCAL_IP=$(ifconfig | grep "inet 192" | head -1 | awk '{print $2}' 2>/dev/null || echo "?")
    echo "  Mac IP: $LOCAL_IP"
    echo ""
    echo "  Terminus-Verbindung:"
    echo "    Host: $LOCAL_IP"
    echo "    Port: 22"
    echo "    User: $(whoami)"
else
    echo "  (Nicht macOS — SSH manuell pruefen)"
fi

# ─── Step 4: Create LaunchAgent (Auto-Start) ────────────────────
echo "[4/5] LaunchAgent einrichten (Auto-Start bei Boot)..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLIST_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$PLIST_DIR/com.aiempire.telegram-bot.plist"
    mkdir -p "$PLIST_DIR"

    cat > "$PLIST_FILE" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiempire.telegram-bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$BOT_SCRIPT</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_ROOT</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$PROJECT_ROOT/logs/telegram_bot.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_ROOT/logs/telegram_bot_error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
PLISTEOF

    mkdir -p "$PROJECT_ROOT/logs"

    # Load the agent
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    launchctl load "$PLIST_FILE" 2>/dev/null || true

    echo "  LaunchAgent installiert: $PLIST_FILE"
    echo "  Bot startet automatisch bei jedem Mac-Neustart"
else
    echo "  (Nicht macOS — systemd Service manuell einrichten)"
fi

# ─── Step 5: Start Bot ──────────────────────────────────────────
echo "[5/5] Starte Empire Telegram Bot..."
echo ""

# Kill any running instance
pkill -f "empire_bot.py" 2>/dev/null || true
sleep 1

# Start in foreground (or background with nohup)
if [ "$1" = "--background" ] || [ "$1" = "-b" ]; then
    nohup python3 "$BOT_SCRIPT" > "$PROJECT_ROOT/logs/telegram_bot.log" 2>&1 &
    BOT_PID=$!
    echo "  Bot laeuft im Hintergrund (PID: $BOT_PID)"
    echo "  Log: tail -f $PROJECT_ROOT/logs/telegram_bot.log"
else
    echo "══════════════════════════════════════════════"
    echo "  Bot startet jetzt im Vordergrund."
    echo "  Strg+C zum Beenden."
    echo ""
    echo "  Fuer Hintergrund: bash $0 --background"
    echo "══════════════════════════════════════════════"
    echo ""
    python3 "$BOT_SCRIPT"
fi
