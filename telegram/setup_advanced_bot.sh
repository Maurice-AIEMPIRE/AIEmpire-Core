#!/bin/bash
set -e

# ============================================================================
# ADVANCED TELEGRAM BOT - SETUP SCRIPT
# Installs and configures the Advanced Bot on Linux/macOS
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOT_DIR="$SCRIPT_DIR"
OS_TYPE="$(uname)"

echo "🚀 Advanced Telegram Bot Setup"
echo "Platform: $OS_TYPE"
echo "Bot Dir: $BOT_DIR"

# ============================================================================
# 1. DEPENDENCIES
# ============================================================================

echo ""
echo "📦 Installing Python dependencies..."

# Create virtual environment (optional but recommended)
if [ ! -d "$BOT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$BOT_DIR/venv"
fi

# Install requirements
source "$BOT_DIR/venv/bin/activate" 2>/dev/null || true
pip3 install --upgrade pip setuptools wheel
pip3 install -r "$BOT_DIR/requirements.txt"

# ============================================================================
# 2. ENVIRONMENT CONFIGURATION
# ============================================================================

echo ""
echo "📝 Checking .env configuration..."

if [ ! -f "$BOT_DIR/.env" ]; then
    echo "⚠️  .env not found. Creating from example..."
    cp "$BOT_DIR/.env.example" "$BOT_DIR/.env"
    echo "⚠️  Please update .env with your credentials:"
    echo "   - BOT_TOKEN (from @BotFather)"
    echo "   - REDIS_HOST (default: localhost)"
    echo "   - ANT_PROTOCOL_URL (default: http://localhost:8900)"
    echo "   - HETZNER_SSH_* (for remote commands)"
    exit 1
else
    echo "✅ .env found"
fi

# ============================================================================
# 3. LINUX SETUP (systemd)
# ============================================================================

if [ "$OS_TYPE" = "Linux" ]; then
    echo ""
    echo "🐧 Linux setup..."

    # Install systemd service
    SERVICE_FILE="/etc/systemd/system/advanced-bot.service"

    if [ -f "$SCRIPT_DIR/systemd/advanced-bot.service" ]; then
        echo "Installing systemd service..."

        # Update path in service file
        sed "s|/home/user/AIEmpire-Core|$(dirname "$BOT_DIR")|g" \
            "$SCRIPT_DIR/systemd/advanced-bot.service" > /tmp/advanced-bot.service

        sudo cp /tmp/advanced-bot.service "$SERVICE_FILE"
        sudo chmod 644 "$SERVICE_FILE"

        # Reload systemd
        sudo systemctl daemon-reload

        echo ""
        echo "✅ Systemd service installed!"
        echo ""
        echo "To start the bot:"
        echo "  sudo systemctl start advanced-bot"
        echo ""
        echo "To enable auto-start on boot:"
        echo "  sudo systemctl enable advanced-bot"
        echo ""
        echo "To view logs:"
        echo "  sudo journalctl -u advanced-bot -f"
    else
        echo "⚠️  systemd service file not found"
    fi
fi

# ============================================================================
# 4. MACOS SETUP (LaunchAgent)
# ============================================================================

if [ "$OS_TYPE" = "Darwin" ]; then
    echo ""
    echo "🍎 macOS setup..."

    PLIST_PATH="$HOME/Library/LaunchAgents/com.aiempire.advancedbot.plist"
    PLIST_TEMPLATE="$SCRIPT_DIR/systemd/com.aiempire.advancedbot.plist"

    if [ -f "$PLIST_TEMPLATE" ]; then
        echo "Setting up LaunchAgent..."

        # Replace path placeholders
        sed "s|/path/to/AIEmpire-Core|$(dirname "$BOT_DIR")|g" \
            "$PLIST_TEMPLATE" > "$PLIST_PATH"

        chmod 644 "$PLIST_PATH"

        echo ""
        echo "✅ LaunchAgent installed!"
        echo ""
        echo "To start the bot:"
        echo "  launchctl load $PLIST_PATH"
        echo ""
        echo "To stop the bot:"
        echo "  launchctl unload $PLIST_PATH"
        echo ""
        echo "To view logs:"
        echo "  tail -f /tmp/advanced_bot.log"
    else
        echo "⚠️  LaunchAgent plist not found"
    fi
fi

# ============================================================================
# 5. VERIFICATION
# ============================================================================

echo ""
echo "🔍 Verification..."

# Check Python
python3 --version

# Check Redis
if command -v redis-cli &> /dev/null; then
    echo -n "Redis: "
    redis-cli ping 2>/dev/null && echo "✅ Connected" || echo "⚠️  Not accessible"
else
    echo "⚠️  redis-cli not installed"
fi

# Check Ant Protocol
echo -n "Ant Protocol: "
curl -s "http://localhost:8900/health" > /dev/null 2>&1 && \
    echo "✅ Online (http://localhost:8900)" || \
    echo "⚠️  Not accessible (http://localhost:8900)"

# ============================================================================
# 6. QUICK START
# ============================================================================

echo ""
echo "✨ Setup complete!"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. Update .env with your credentials"
echo "2. Ensure Redis is running: redis-server"
echo "3. Ensure Ant Protocol is accessible on port 8900"
echo ""

if [ "$OS_TYPE" = "Linux" ]; then
    echo "4. Start the bot:"
    echo "   sudo systemctl start advanced-bot"
    echo "   sudo systemctl enable advanced-bot  # Auto-start on boot"
elif [ "$OS_TYPE" = "Darwin" ]; then
    echo "4. Start the bot:"
    echo "   launchctl load ~/Library/LaunchAgents/com.aiempire.advancedbot.plist"
fi

echo ""
echo "🧪 For manual testing:"
echo "   cd $BOT_DIR"
echo "   python3 advanced_bot.py"
echo ""
echo "📊 To view logs (after systemd start):"
echo "   sudo journalctl -u advanced-bot -f"
echo ""
