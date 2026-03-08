#!/bin/bash

echo ""
echo "🌌 ═══════════════════════════════════════════"
echo "   GALAXIA Configuration Setup"
echo "═══════════════════════════════════════════"
echo ""
echo "ℹ️  Your secrets will NOT be displayed on screen"
echo ""

# Prompt für ANTHROPIC_API_KEY
read -sp "▶ ANTHROPIC_API_KEY (sk-ant-...): " ANTHROPIC_API_KEY
echo ""

# Prompt für TELEGRAM_BOT_TOKEN
read -sp "▶ TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
echo ""

# Prompt für TELEGRAM_CHAT_ID
read -p "▶ TELEGRAM_CHAT_ID: " TELEGRAM_CHAT_ID
echo ""

# Optional: TELEGRAM_ADMIN_IDS (default = TELEGRAM_CHAT_ID)
read -p "▶ TELEGRAM_ADMIN_IDS (default: $TELEGRAM_CHAT_ID): " TELEGRAM_ADMIN_IDS
TELEGRAM_ADMIN_IDS=${TELEGRAM_ADMIN_IDS:-$TELEGRAM_CHAT_ID}

echo ""
echo "💾 Writing to .env..."

# In .env schreiben (im aktuellen Directory)
cat > .env << ENVEOF
# Telegram Bot Configuration (GALAXIA)
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
TELEGRAM_ADMIN_IDS=$TELEGRAM_ADMIN_IDS
TELEGRAM_USER_ID=$TELEGRAM_CHAT_ID

# Claude API
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# System Configuration
REDIS_URL=redis://127.0.0.1:6379/0
LOG_LEVEL=INFO
ENVIRONMENT=production

# Empire Engine Integration
EMPIRE_BRIDGE_URL=http://localhost:8000
ENABLE_ASYNC=true
ENVEOF

echo "✅ .env configured successfully!"
echo ""
echo "📋 Configuration saved to: $(pwd)/.env"
echo ""
echo "🚀 Next: Start Galaxia with:"
echo "   python3 empire_engine.py"
echo ""
