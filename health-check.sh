#!/bin/bash
# ============================================================
# Advanced Telegram Bot - Health Check Script
# ============================================================

HETZNER_IP="65.21.203.174"
HETZNER_USER="root"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Advanced Telegram Bot - Health Check                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check command success
check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

echo -e "${YELLOW}Checking bot on ${HETZNER_IP}...${NC}"
echo ""

# ============================================================
# CHECK 1: SSH Access
# ============================================================
echo "🔌 SSH Access:"
if ssh -o ConnectTimeout=3 $HETZNER_USER@$HETZNER_IP "echo 'ok'" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓${NC} SSH connection OK"
else
    echo -e "${RED}  ✗${NC} SSH connection failed"
    exit 1
fi
echo ""

# ============================================================
# CHECK 2: Bot Service Status
# ============================================================
echo "🤖 Bot Service:"
ssh $HETZNER_USER@$HETZNER_IP << 'SSH_CHECK'
    # Check if running
    if systemctl is-active --quiet advanced-bot; then
        echo -e "\033[0;32m  ✓\033[0m Bot is running"
    else
        echo -e "\033[0;31m  ✗\033[0m Bot is NOT running"
    fi

    # Check if enabled
    if systemctl is-enabled --quiet advanced-bot; then
        echo -e "\033[0;32m  ✓\033[0m Auto-start enabled"
    else
        echo -e "\033[0;33m  ⚠\033[0m Auto-start NOT enabled"
    fi

    # Get status
    echo ""
    echo "Status:"
    systemctl status advanced-bot --no-pager | head -n 3 | sed 's/^/    /'
SSH_CHECK
echo ""

# ============================================================
# CHECK 3: Resources
# ============================================================
echo "📊 Resource Usage:"
ssh $HETZNER_USER@$HETZNER_IP << 'SSH_RESOURCES'
    echo "Process info:"
    ps aux | grep "[a]dvanced_bot" | awk '{print "  CPU: "$3"% | MEM: "$4"% | PID: "$2}'

    if [ -z "$(ps aux | grep '[a]dvanced_bot')" ]; then
        echo "    (bot not running)"
    fi

    echo ""
    echo "Memory (system):"
    free -h | head -n 2 | tail -n 1 | awk '{print "  Used: "$3" / Total: "$2}'

    echo ""
    echo "Disk (bot logs):"
    if [ -f /tmp/advanced_bot.log ]; then
        du -h /tmp/advanced_bot.log | awk '{print "  Log size: "$1}'
    else
        echo "    No log file yet"
    fi
SSH_RESOURCES
echo ""

# ============================================================
# CHECK 4: Dependencies
# ============================================================
echo "📦 Dependencies:"
ssh $HETZNER_USER@$HETZNER_IP << 'SSH_DEPS'
    cd /opt/aiempire/telegram 2>/dev/null || {
        echo -e "\033[0;31m  ✗\033[0m Bot directory not found"
        exit 1
    }

    python3 -c "import aiohttp, redis, tenacity; print('\033[0;32m  ✓\033[0m All imports OK')" 2>/dev/null || \
        echo -e "\033[0;31m  ✗\033[0m Missing dependencies"
SSH_DEPS
echo ""

# ============================================================
# CHECK 5: Redis Connection
# ============================================================
echo "💾 Redis:"
ssh $HETZNER_USER@$HETZNER_IP << 'SSH_REDIS'
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping > /dev/null 2>&1; then
            echo -e "\033[0;32m  ✓\033[0m Redis is running"
            redis-cli DBSIZE | awk '{print "  Keys in DB: "$3}'
        else
            echo -e "\033[0;31m  ✗\033[0m Redis not responding"
        fi
    else
        echo -e "\033[0;33m  ⚠\033[0m redis-cli not installed"
    fi
SSH_REDIS
echo ""

# ============================================================
# CHECK 6: Ant Protocol
# ============================================================
echo "🐜 Ant Protocol (Port 8900):"
ssh $HETZNER_USER@$HETZNER_IP << 'SSH_ANT'
    if curl -s http://localhost:8900/health > /dev/null 2>&1; then
        echo -e "\033[0;32m  ✓\033[0m Ant Protocol responding"
    else
        echo -e "\033[0;33m  ⚠\033[0m Ant Protocol not accessible"
    fi
SSH_ANT
echo ""

# ============================================================
# CHECK 7: Recent Logs
# ============================================================
echo "📋 Recent Logs (last 5 lines):"
ssh $HETZNER_USER@$HETZNER_IP << 'SSH_LOGS'
    if journalctl -u advanced-bot -n 5 --no-pager > /dev/null 2>&1; then
        journalctl -u advanced-bot -n 5 --no-pager | sed 's/^/    /'
    else
        echo "    No logs available yet"
    fi
SSH_LOGS
echo ""

# ============================================================
# CHECK 8: Errors in Logs
# ============================================================
echo "🔍 Errors in last 100 log lines:"
ERROR_COUNT=$(ssh $HETZNER_USER@$HETZNER_IP "journalctl -u advanced-bot -n 100 | grep -i 'error\|critical\|exception' | wc -l")
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "${GREEN}  ✓${NC} No errors found"
else
    echo -e "${YELLOW}  ⚠${NC} Found $ERROR_COUNT error(s):"
    ssh $HETZNER_USER@$HETZNER_IP "journalctl -u advanced-bot -n 100 | grep -i 'error\|critical\|exception' | head -3" | sed 's/^/    /'
fi
echo ""

# ============================================================
# Summary
# ============================================================
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}Health check complete!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "📞 Troubleshooting:"
echo ""
echo "  Bot not running?"
echo "    ${BLUE}ssh root@$HETZNER_IP 'systemctl restart advanced-bot'${NC}"
echo ""
echo "  View full logs:"
echo "    ${BLUE}ssh root@$HETZNER_IP 'journalctl -u advanced-bot -f'${NC}"
echo ""
echo "  Check process:"
echo "    ${BLUE}ssh root@$HETZNER_IP 'ps aux | grep advanced_bot'${NC}"
echo ""
