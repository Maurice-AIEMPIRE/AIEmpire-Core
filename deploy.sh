#!/bin/bash
# ============================================================
# Advanced Telegram Bot - One-Click Deployment to Hetzner
# ============================================================

set -e

HETZNER_IP="65.21.203.174"
HETZNER_USER="root"
BOT_DIR="/opt/aiempire/telegram"
LOCAL_BOT_DIR="./telegram"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Advanced Telegram Bot - Hetzner Deployment            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================
# STEP 1: Verify SSH Access
# ============================================================
echo -e "${YELLOW}[1/5]${NC} Verifying SSH access to Hetzner..."
if ! ssh -o ConnectTimeout=5 $HETZNER_USER@$HETZNER_IP "echo 'SSH OK'" > /dev/null 2>&1; then
    echo -e "${RED}✗ Cannot SSH to $HETZNER_IP${NC}"
    echo "Make sure you have SSH access configured:"
    echo "  ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519"
    echo "  ssh-copy-id -i ~/.ssh/id_ed25519.pub root@$HETZNER_IP"
    exit 1
fi
echo -e "${GREEN}✓ SSH access OK${NC}"
echo ""

# ============================================================
# STEP 2: Create directories on Hetzner
# ============================================================
echo -e "${YELLOW}[2/5]${NC} Creating directories on Hetzner..."
ssh $HETZNER_USER@$HETZNER_IP << 'SSH_CREATE'
    mkdir -p /opt/aiempire/telegram/systemd
    mkdir -p /var/log/galaxia-bot
    mkdir -p /var/lib/galaxia-bot
    echo "Directories created"
SSH_CREATE
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# ============================================================
# STEP 3: Copy bot files to Hetzner
# ============================================================
echo -e "${YELLOW}[3/5]${NC} Uploading bot files..."
scp -r \
    $LOCAL_BOT_DIR/advanced_bot.py \
    $LOCAL_BOT_DIR/agent_executor.py \
    $LOCAL_BOT_DIR/requirements.txt \
    $LOCAL_BOT_DIR/.env \
    $LOCAL_BOT_DIR/systemd/ \
    $HETZNER_USER@$HETZNER_IP:$BOT_DIR/

echo -e "${GREEN}✓ Files uploaded${NC}"
echo ""

# ============================================================
# STEP 4: Install dependencies & configure on Hetzner
# ============================================================
echo -e "${YELLOW}[4/5]${NC} Installing dependencies and configuring systemd..."
ssh $HETZNER_USER@$HETZNER_IP << SSH_INSTALL
    set -e
    cd $BOT_DIR

    # Install Python dependencies
    echo "Installing Python packages..."
    pip3 install --upgrade pip > /dev/null 2>&1
    pip3 install -q -r requirements.txt

    # Update systemd service path
    echo "Configuring systemd service..."
    sed -i 's|/home/user/AIEmpire-Core|/opt/aiempire|g' systemd/advanced-bot.service

    # Copy systemd service
    cp systemd/advanced-bot.service /etc/systemd/system/

    # Reload systemd daemon
    systemctl daemon-reload
    systemctl enable advanced-bot

    # Set permissions
    chmod 644 /etc/systemd/system/advanced-bot.service

    echo "✓ Systemd configured"
SSH_INSTALL
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# ============================================================
# STEP 5: Start the bot
# ============================================================
echo -e "${YELLOW}[5/5]${NC} Starting bot service..."
ssh $HETZNER_USER@$HETZNER_IP << SSH_START
    # Start the service
    systemctl start advanced-bot

    # Wait a moment for startup
    sleep 2

    # Check status
    if systemctl is-active --quiet advanced-bot; then
        echo "✓ Bot started successfully"
    else
        echo "✗ Bot failed to start - checking logs..."
        journalctl -u advanced-bot -n 10
        exit 1
    fi
SSH_START
echo -e "${GREEN}✓ Bot started${NC}"
echo ""

# ============================================================
# Final Verification
# ============================================================
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✓ DEPLOYMENT COMPLETE!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "📊 Verification Commands:"
echo ""
echo "  Check status:"
echo "    ${BLUE}ssh root@$HETZNER_IP 'systemctl status advanced-bot'${NC}"
echo ""
echo "  View live logs:"
echo "    ${BLUE}ssh root@$HETZNER_IP 'journalctl -u advanced-bot -f'${NC}"
echo ""
echo "  Restart bot:"
echo "    ${BLUE}ssh root@$HETZNER_IP 'systemctl restart advanced-bot'${NC}"
echo ""

echo "🧪 Testing:"
echo "  1. Open Telegram and find your bot"
echo "  2. Send: ${YELLOW}/start${NC}"
echo "  3. Should see help menu"
echo ""

echo "📝 Useful commands:"
echo "  - View logs:     ${BLUE}ssh root@$HETZNER_IP 'journalctl -u advanced-bot -f'${NC}"
echo "  - Stop bot:      ${BLUE}ssh root@$HETZNER_IP 'systemctl stop advanced-bot'${NC}"
echo "  - Restart bot:   ${BLUE}ssh root@$HETZNER_IP 'systemctl restart advanced-bot'${NC}"
echo "  - Full logs:     ${BLUE}ssh root@$HETZNER_IP 'journalctl -u advanced-bot'${NC}"
echo ""

echo -e "${GREEN}✅ Bot is now LIVE on Hetzner!${NC}"
