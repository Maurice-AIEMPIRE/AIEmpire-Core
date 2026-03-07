#!/bin/bash
# Start Advanced Telegram Bot on Hetzner

set -e

WORK_DIR="/opt/aiempire/telegram"
BOT_FILE="$WORK_DIR/advanced_bot_fallback.py"
LOG_FILE="/tmp/advanced_bot.log"

echo "🚀 Starting Advanced Telegram Bot..."
echo "📁 Working directory: $WORK_DIR"
echo "📝 Log file: $LOG_FILE"

# Check if .env exists
if [ ! -f "$WORK_DIR/.env" ]; then
    echo "❌ ERROR: .env file not found at $WORK_DIR/.env"
    echo "Please create .env with TELEGRAM_BOT_TOKEN"
    exit 1
fi

# Check if Python file exists
if [ ! -f "$BOT_FILE" ]; then
    echo "❌ ERROR: Bot script not found at $BOT_FILE"
    exit 1
fi

# Check Python version
python3 --version

# Check imports
echo "🔍 Checking Python imports..."
python3 -c "import dotenv; print('✅ All imports OK')" || {
    echo "⚠️ Missing dependencies, installing..."
    pip3 install -q -r "$WORK_DIR/requirements.txt"
}

# Clear old logs if too large
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null) -gt 52428800 ]; then
    echo "🧹 Cleaning old logs (>50MB)"
    rm -f "$LOG_FILE"
fi

# Start bot
echo ""
echo "✅ Starting bot..."
echo "📌 Press Ctrl+C to stop"
echo ""

# Run in foreground (for systemd/docker)
cd "$WORK_DIR"
exec python3 "$BOT_FILE"
