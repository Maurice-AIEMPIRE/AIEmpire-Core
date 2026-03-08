#!/bin/bash
# ============================================================
# AIEmpire Telegram Bot — Deploy auf Hetzner-Server
# ============================================================
# Einmalig ausführen auf dem Hetzner-Server:
#   chmod +x telegram_bot/deploy.sh
#   ./telegram_bot/deploy.sh
# ============================================================

set -e
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOT_DIR="$REPO_DIR/telegram_bot"

echo "🚀 AIEmpire Telegram Bot Deploy"
echo "================================"
echo "Repo: $REPO_DIR"

# 1. Dependencies installieren
echo ""
echo "📦 Installiere Dependencies..."
pip3 install python-telegram-bot==20.7 PyPDF2 aiofiles redis --quiet
pip3 install python-telegram-bot[job-queue] --quiet 2>/dev/null || true

# pdftotext (optional)
if ! command -v pdftotext &>/dev/null; then
    echo "   Installiere pdftotext..."
    apt-get install -y poppler-utils 2>/dev/null || \
    yum install -y poppler-utils 2>/dev/null || \
    echo "   (optional, skip)"
fi

# 2. Upload-Verzeichnis
mkdir -p "$BOT_DIR/uploads"
echo "📁 Upload-Verzeichnis: $BOT_DIR/uploads"

# 3. Token prüfen
if [ -f "$REPO_DIR/.env" ]; then
    TOKEN=$(grep "TELEGRAM_BOT_TOKEN" "$REPO_DIR/.env" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    if [ -z "$TOKEN" ]; then
        echo "⚠️  TELEGRAM_BOT_TOKEN nicht in .env gefunden"
        echo "   Füge hinzu: TELEGRAM_BOT_TOKEN=dein_token"
    else
        echo "✅ Token gefunden: ${TOKEN:0:20}..."
    fi
else
    echo "⚠️  Keine .env Datei gefunden"
    echo "   Erstelle: echo 'TELEGRAM_BOT_TOKEN=dein_token' >> $REPO_DIR/.env"
fi

# 4. Systemd Service installieren (falls systemd verfügbar)
if command -v systemctl &>/dev/null; then
    echo ""
    echo "⚙️  Installiere systemd Service..."

    cat > /etc/systemd/system/aiempire-telegram.service << EOF
[Unit]
Description=AIEmpire Telegram Bot
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$REPO_DIR
ExecStart=/usr/bin/python3 $BOT_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
EnvironmentFile=$REPO_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable aiempire-telegram
    systemctl restart aiempire-telegram

    echo "✅ Service installiert und gestartet"
    echo "   Status:  systemctl status aiempire-telegram"
    echo "   Logs:    journalctl -u aiempire-telegram -f"
    echo "   Stopp:   systemctl stop aiempire-telegram"
else
    # Kein systemd → nohup
    echo ""
    echo "🔄 Starte Bot mit nohup..."
    pkill -f "telegram_bot/bot.py" 2>/dev/null || true
    sleep 1
    nohup python3 "$BOT_DIR/bot.py" > /tmp/aiempire_telegram.log 2>&1 &
    echo "✅ Bot gestartet (PID: $!)"
    echo "   Logs: tail -f /tmp/aiempire_telegram.log"
fi

echo ""
echo "================================"
echo "✅ Deploy abgeschlossen!"
echo ""
echo "📱 Bot testen: Sende /start an @YourBotName"
echo "📄 Logs: tail -f /tmp/aiempire_telegram.log"
echo "================================"
