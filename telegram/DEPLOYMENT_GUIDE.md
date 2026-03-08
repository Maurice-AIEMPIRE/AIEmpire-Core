# 🚀 Advanced Telegram Bot - Deployment Guide

## Quick Deployment Summary

```
LOCAL (Development):    python3 advanced_bot.py
LINUX (Production):     systemctl start advanced-bot
macOS (Development):    launchctl load ~/Library/LaunchAgents/...
HETZNER (Production):   SSH deploy + systemctl
```

---

## 🌐 HETZNER DEPLOYMENT (Production)

### Prerequisites
- SSH access to Hetzner: `ssh root@65.21.203.174`
- Port 8900 (Ant Protocol) accessible
- Redis running (`redis-cli ping`)

### Step 1: Deploy Files via SSH

```bash
# From your local machine:
HETZNER_IP="65.21.203.174"
BOT_SRC="./telegram"

# Create destination
ssh root@$HETZNER_IP "mkdir -p /opt/aiempire/telegram"

# Copy bot files
scp -r $BOT_SRC/advanced_bot.py \
        $BOT_SRC/agent_executor.py \
        $BOT_SRC/requirements.txt \
        $BOT_SRC/.env \
        $BOT_SRC/systemd/ \
        root@$HETZNER_IP:/opt/aiempire/telegram/
```

### Step 2: Install Dependencies on Hetzner

```bash
ssh root@65.21.203.174 << 'EOF'
cd /opt/aiempire/telegram

# Install Python dependencies
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Verify imports
python3 -c "import aiohttp, redis, tenacity; print('✅ OK')"
EOF
```

### Step 3: Install Systemd Service

```bash
ssh root@65.21.203.174 << 'EOF'
# Update service file path
sed -i 's|/home/user/AIEmpire-Core|/opt/aiempire|g' \
    /opt/aiempire/telegram/systemd/advanced-bot.service

# Install service
cp /opt/aiempire/telegram/systemd/advanced-bot.service /etc/systemd/system/
systemctl daemon-reload

# Enable auto-start
systemctl enable advanced-bot

# Start the bot
systemctl start advanced-bot

# Verify status
systemctl status advanced-bot
EOF
```

### Step 4: Verify Hetzner Deployment

```bash
ssh root@65.21.203.174 << 'EOF'
# Check if bot is running
systemctl status advanced-bot

# View recent logs
journalctl -u advanced-bot -n 20

# Check processes
ps aux | grep advanced_bot

# Test Redis connection from bot
redis-cli ping

# Test Ant Protocol
curl http://localhost:8900/health

# Check log file
tail -f /tmp/advanced_bot.log
EOF
```

---

## 🍎 macOS DEPLOYMENT (Development)

### Step 1: Install Dependencies

```bash
cd telegram
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

### Step 2: Install LaunchAgent

```bash
# Get your local AIEmpire-Core path
AIEMPIRE_PATH="$(pwd)/.."

# Update plist with correct path
sed "s|/path/to/AIEmpire-Core|$AIEMPIRE_PATH|g" \
    systemd/com.aiempire.advancedbot.plist > \
    ~/Library/LaunchAgents/com.aiempire.advancedbot.plist

# Set permissions
chmod 644 ~/Library/LaunchAgents/com.aiempire.advancedbot.plist

# Load the agent
launchctl load ~/Library/LaunchAgents/com.aiempire.advancedbot.plist
```

### Step 3: Start & Monitor (macOS)

```bash
# Check if running
launchctl list | grep aiempire

# View logs
tail -f /tmp/advanced_bot.log
tail -f /tmp/advanced_bot_error.log

# Stop the bot (if needed)
launchctl unload ~/Library/LaunchAgents/com.aiempire.advancedbot.plist

# Restart
launchctl unload ~/Library/LaunchAgents/com.aiempire.advancedbot.plist
launchctl load ~/Library/LaunchAgents/com.aiempire.advancedbot.plist
```

---

## 🐧 LINUX DEPLOYMENT (Local/Dev)

### Step 1: Install Dependencies

```bash
cd telegram
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

### Step 2: Install Systemd Service

```bash
# Update path in service file
TELEGRAM_PATH="/home/user/AIEmpire-Core/telegram"
sed "s|/home/user/AIEmpire-Core|${TELEGRAM_PATH%/telegram}|g" \
    systemd/advanced-bot.service > /tmp/advanced-bot.service

# Install to systemd
sudo cp /tmp/advanced-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable advanced-bot
```

### Step 3: Start & Monitor

```bash
# Start the bot
sudo systemctl start advanced-bot

# Check status
sudo systemctl status advanced-bot

# View logs
sudo journalctl -u advanced-bot -f

# Stop (if needed)
sudo systemctl stop advanced-bot
```

---

## 🧪 TESTING AFTER DEPLOYMENT

### Test 1: Check Bot is Running

```bash
# Hetzner
ssh root@65.21.203.174 "systemctl status advanced-bot"

# macOS
launchctl list | grep aiempire

# Linux
sudo systemctl status advanced-bot
```

### Test 2: Send Telegram Command

In your Telegram chat with the bot:
```
/start
```

Should see help message with commands.

### Test 3: Test NLU

```
What's the system status?
```

Should respond with system info.

### Test 4: Test Agent Routing

```
Run agent 2
```

Should trigger agent-02 via Ant Protocol.

### Test 5: Check Redis State

```bash
# From bot host
redis-cli KEYS "conv:*"       # List conversations
redis-cli LRANGE "conv:YOUR_USER_ID" 0 -1  # View messages
```

---

## 📊 MONITORING & LOGGING

### Hetzner Logging

```bash
ssh root@65.21.203.174 << 'EOF'
# Real-time logs
journalctl -u advanced-bot -f

# Last 50 lines
journalctl -u advanced-bot -n 50

# Errors only
journalctl -u advanced-bot -p err

# Since last hour
journalctl -u advanced-bot --since "1 hour ago"

# Export to file
journalctl -u advanced-bot > /tmp/bot_logs.txt
EOF
```

### macOS Logging

```bash
# Real-time
tail -f /tmp/advanced_bot.log

# Errors
tail -f /tmp/advanced_bot_error.log

# Check LaunchAgent logs
log stream --predicate 'process == "python3"' --level debug
```

### Health Check Script

```bash
#!/bin/bash
echo "🔍 Checking Advanced Bot Health..."

# Check process
echo -n "Bot Running: "
ps aux | grep advanced_bot | grep -v grep > /dev/null && echo "✅" || echo "❌"

# Check Redis
echo -n "Redis: "
redis-cli ping 2>/dev/null && echo "✅" || echo "❌"

# Check Ant Protocol
echo -n "Ant Protocol: "
curl -s http://localhost:8900/health > /dev/null && echo "✅" || echo "❌"

# Check bot port (if listening)
echo -n "Bot Socket: "
lsof -i :18789 > /dev/null 2>&1 && echo "✅" || echo "⚠️  (not listening on port)"

# Check log file size
echo "Log Size: $(du -h /tmp/advanced_bot.log 2>/dev/null | cut -f1 || echo "0B")"

# Recent errors
echo -n "Recent Errors: "
grep -c "ERROR\|CRITICAL" /tmp/advanced_bot.log 2>/dev/null || echo "0"
```

---

## ⚙️ CONFIGURATION MANAGEMENT

### Environment Variables (.env)

```env
# Telegram
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
DEVELOPER_ID=YOUR_USER_ID

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# NLU Providers
OLLAMA_URL=http://localhost:11434
KIMI_API_KEY=optional
CLAUDE_API_KEY=optional

# Agent Execution
ANT_PROTOCOL_URL=http://localhost:8900

# Remote SSH
HETZNER_SSH_HOST=65.21.203.174
HETZNER_SSH_USER=root
HETZNER_SSH_KEY=/path/to/key
```

### Update Configuration

```bash
# Hetzner
ssh root@65.21.203.174 "vim /opt/aiempire/telegram/.env"
ssh root@65.21.203.174 "systemctl restart advanced-bot"

# Local
vim telegram/.env
systemctl restart advanced-bot  # or launchctl reload
```

---

## 🔧 TROUBLESHOOTING

| Issue | Fix |
|-------|-----|
| Bot not starting | Check logs: `journalctl -u advanced-bot` |
| Redis connection failed | Verify Redis: `redis-cli ping` |
| Ant Protocol unreachable | Check: `curl http://localhost:8900/health` |
| NLU timeout | Check Ollama: `curl http://localhost:11434/api/tags` |
| High memory | Check: `ps aux \| grep advanced_bot`, restart if >500MB |
| Bot not responding | Check Telegram token in `.env` |
| SSH key permission denied | Fix: `chmod 600 ~/.ssh/id_rsa` |

---

## 🚀 FULL AUTOMATED DEPLOYMENT SCRIPT

Save as `deploy.sh`:

```bash
#!/bin/bash
set -e

HETZNER_IP="65.21.203.174"
BOT_DIR="/opt/aiempire/telegram"

echo "🚀 Automated Advanced Bot Deployment"

# 1. Create directories
ssh root@$HETZNER_IP "mkdir -p $BOT_DIR/systemd"

# 2. Copy files
scp -r telegram/* root@$HETZNER_IP:$BOT_DIR/

# 3. Install dependencies
ssh root@$HETZNER_IP "cd $BOT_DIR && pip3 install -r requirements.txt"

# 4. Install systemd
ssh root@$HETZNER_IP << 'EOF'
  sed -i 's|/home/user/AIEmpire-Core|/opt/aiempire|g' $BOT_DIR/systemd/advanced-bot.service
  cp $BOT_DIR/systemd/advanced-bot.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable advanced-bot
  systemctl start advanced-bot
EOF

# 5. Verify
ssh root@$HETZNER_IP "systemctl status advanced-bot && journalctl -u advanced-bot -n 5"

echo "✅ DEPLOYMENT COMPLETE!"
```

Usage:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📋 DEPLOYMENT CHECKLIST

- [ ] SSH access to Hetzner verified
- [ ] Bot files copied to `/opt/aiempire/telegram`
- [ ] Dependencies installed (`pip3 install -r requirements.txt`)
- [ ] `.env` file configured with BOT_TOKEN
- [ ] Systemd service installed and enabled
- [ ] Bot started: `systemctl start advanced-bot`
- [ ] Logs checked: `journalctl -u advanced-bot`
- [ ] Telegram command `/start` works
- [ ] NLU responds to natural language
- [ ] Agent routing triggered successfully
- [ ] Redis state persisting conversations
- [ ] Monitoring logs created

---

**Next:** Test the bot in your Telegram chat! Send `/start` 🎉
