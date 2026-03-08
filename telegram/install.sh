#!/bin/bash
# ============================================
# GALAXIA OS TELEGRAM BOT INSTALLATION SCRIPT
# Installs complete control infrastructure on Mac or Hetzner
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${1:-.}"
PLATFORM=$(uname -s)

echo "🌌 GALAXIA OS BOT INSTALLATION"
echo "Platform: $PLATFORM"
echo "Install directory: $INSTALL_DIR"
echo ""

# ==================== DETECT PLATFORM ====================

if [[ "$PLATFORM" == "Darwin" ]]; then
    echo "🍎 macOS detected"
    IS_MAC=true
    PYTHON_CMD="python3"
elif [[ "$PLATFORM" == "Linux" ]]; then
    echo "🐧 Linux detected (Hetzner)"
    IS_MAC=false
    PYTHON_CMD="python3"
else
    echo "❌ Unsupported platform: $PLATFORM"
    exit 1
fi

# ==================== PREREQUISITES ====================

echo ""
echo "📦 Checking prerequisites..."

# Python 3
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi
echo "✅ Python 3: $($PYTHON_CMD --version)"

# Redis
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️ Redis not found. Install with:"
    if [[ $IS_MAC == true ]]; then
        echo "   brew install redis"
    else
        echo "   sudo apt install redis-server"
    fi
    exit 1
fi
echo "✅ Redis: $(redis-cli --version)"

# ==================== INSTALL DEPENDENCIES ====================

echo ""
echo "📥 Installing Python dependencies..."

if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
    $PYTHON_CMD -m pip install --upgrade pip setuptools wheel
    $PYTHON_CMD -m pip install -r "$SCRIPT_DIR/requirements.txt"
    echo "✅ Dependencies installed"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# ==================== SETUP DIRECTORIES ====================

echo ""
echo "📁 Setting up directories..."

mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/state"

if [[ $IS_MAC == false ]]; then
    sudo mkdir -p /var/log/galaxia-bot
    sudo mkdir -p /var/lib/galaxia-bot
    sudo chown -R $USER:$USER /var/log/galaxia-bot
    sudo chown -R $USER:$USER /var/lib/galaxia-bot
fi

echo "✅ Directories created"

# ==================== ENVIRONMENT CONFIGURATION ====================

echo ""
echo "🔧 Setting up environment..."

if [[ -f "$INSTALL_DIR/.env" ]]; then
    echo "⚠️ .env already exists, skipping"
else
    if [[ -f "$SCRIPT_DIR/.env.example" ]]; then
        cp "$SCRIPT_DIR/.env.example" "$INSTALL_DIR/.env"
        echo "✅ Created .env from template"
        echo ""
        echo "⚠️ IMPORTANT: Edit .env and add:"
        echo "   - BOT_TOKEN (get from @BotFather on Telegram)"
        echo "   - DEVELOPER_CHAT_ID (your chat ID)"
        echo "   - ALLOWED_CHAT_IDS (comma-separated)"
        echo ""
        echo "   nano $INSTALL_DIR/.env"
    else
        echo "❌ .env.example not found"
        exit 1
    fi
fi

# ==================== SYSTEMD SERVICES (Linux only) ====================

if [[ $IS_MAC == false ]]; then
    echo ""
    echo "⚙️ Installing systemd services..."

    for service in galaxia-bot galaxia-orchestrator galaxia-watchdog; do
        SERVICE_FILE="/etc/systemd/system/$service.service"
        SCRIPT_FILE="$SCRIPT_DIR/systemd/$service.service"

        if [[ -f "$SCRIPT_FILE" ]]; then
            echo "Installing $service..."
            sudo cp "$SCRIPT_FILE" "$SERVICE_FILE"
            sudo systemctl daemon-reload
            sudo systemctl enable "$service"
            echo "✅ $service installed"
        else
            echo "⚠️ $service.service not found"
        fi
    done
fi

# ==================== LAUNCHD (macOS only) ====================

if [[ $IS_MAC == true ]]; then
    echo ""
    echo "🚀 Installing macOS Launch Agents..."

    LAUNCH_DIR="$HOME/Library/LaunchAgents"
    mkdir -p "$LAUNCH_DIR"

    # Create launch agent plist
    cat > "$LAUNCH_DIR/com.galaxia.bot.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.galaxia.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/opt/galaxia/bot/bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/opt/galaxia/bot</string>
    <key>StandardOutPath</key>
    <string>/var/log/galaxia-bot.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/galaxia-bot-error.log</string>
    <key>KeepAlive</key>
    <true/>
    <key>RunAtLoad</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
EOF

    launchctl load "$LAUNCH_DIR/com.galaxia.bot.plist"
    echo "✅ Launch agent installed"
fi

# ==================== VERIFICATION ====================

echo ""
echo "✅ INSTALLATION COMPLETE"
echo ""
echo "Next steps:"
echo "1️⃣  Edit .env with your Telegram Bot Token:"
echo "   nano $INSTALL_DIR/.env"
echo ""
echo "2️⃣  Start services:"

if [[ $IS_MAC == true ]]; then
    echo "   launchctl start com.galaxia.bot"
else
    echo "   sudo systemctl start galaxia-bot"
    echo "   sudo systemctl start galaxia-orchestrator"
    echo "   sudo systemctl start galaxia-watchdog"
fi

echo ""
echo "3️⃣  Check status:"

if [[ $IS_MAC == true ]]; then
    echo "   launchctl list | grep galaxia"
else
    echo "   sudo systemctl status galaxia-bot"
fi

echo ""
echo "4️⃣  View logs:"

if [[ $IS_MAC == true ]]; then
    echo "   tail -f /var/log/galaxia-bot.log"
else
    echo "   sudo journalctl -u galaxia-bot -f"
fi

echo ""
echo "🌌 Bot ready to control Galaxia OS!"
