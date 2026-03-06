# 🚀 HETZNER DEPLOYMENT - FINAL SETUP

## Status: ✅ READY TO DEPLOY

All files are prepared for production deployment on Hetzner (65.21.203.174).

---

## 📦 What's Deployed

### **Files on Hetzner (/opt/aiempire/telegram)**
```
✅ .env                      (Bot Token + Config)
✅ advanced_bot.py           (Full-featured bot)
✅ advanced_bot_fallback.py  (Redis-optional version)
✅ redis_state.py            (State management)
✅ requirements.txt          (Python deps)
✅ systemd/advanced-bot.service  (Auto-start)
```

### **Python Dependencies**
```
✅ python-telegram-bot >= 21.0
✅ aiohttp >= 3.9.0
✅ redis >= 5.0.0
✅ python-dotenv >= 1.0.0
✅ psutil >= 5.9.0
```

---

## 🎯 QUICK START (Hetzner)

### **Option 1: Start Bot Directly (No systemd)**
```bash
# SSH to Hetzner
ssh root@65.21.203.174

# Navigate to bot directory
cd /opt/aiempire/telegram

# Start bot (runs in foreground)
python3 advanced_bot_fallback.py

# Or in background with nohup
nohup python3 advanced_bot_fallback.py > /tmp/bot.log 2>&1 &

# Check logs
tail -f /tmp/bot.log
```

### **Option 2: Start with systemd (Recommended)**
```bash
ssh root@65.21.203.174 << 'EOF'
  systemctl daemon-reload
  systemctl enable advanced-bot
  systemctl start advanced-bot
  systemctl status advanced-bot
  journalctl -u advanced-bot -f
EOF
```

### **Option 3: One-Command Deploy (from local machine)**
```bash
ssh root@65.21.203.174 '/opt/aiempire/telegram/start_bot.sh'
```

---

## ✅ TEST THE BOT (After Starting)

### **1. Check it's running**
```bash
# Check process
ps aux | grep advanced_bot

# Check logs
tail -f /tmp/advanced_bot.log
# or
journalctl -u advanced-bot -f
```

### **2. Test in Telegram**
Send messages to bot:
- `/start` → Should see help
- `/status` → Should see system status
- `/revenue` → Should see revenue pipeline
- `Hello!` → Bot should respond

### **3. Expected Responses**
```
User: /start
Bot: 🚀 **ADVANCED TELEGRAM BOT**
     /status - System status
     /revenue - Revenue pipeline
     ... etc

User: /status
Bot: 📊 **SYSTEM STATUS**
     ✅ Bot: Online
     ✅ Telegram: Connected
     ⏳ Redis: Fallback mode
     Time: 2026-03-06T...

User: /revenue
Bot: 💰 **REVENUE PIPELINE**
     Gumroad: €0 (ready)
     Fiverr: €0 (active)
     ... etc
```

---

## 📊 DEPLOYMENT CHECKLIST

- ✅ `.env` created with TELEGRAM_BOT_TOKEN
- ✅ `advanced_bot.py` deployed to `/opt/aiempire/telegram`
- ✅ `redis_state.py` deployed (for future Redis integration)
- ✅ `requirements.txt` installed
- ✅ Systemd service configured (`/etc/systemd/system/advanced-bot.service`)
- ✅ Python 3.11 available
- ✅ Internet connectivity verified

**Remaining:**
- ⏳ Start bot service (Option 1, 2, or 3 above)
- ⏳ Test in Telegram

---

## 🔧 TROUBLESHOOTING

| Issue | Fix |
|-------|-----|
| **Bot doesn't respond** | Check logs: `tail -f /tmp/advanced_bot.log` |
| **"TELEGRAM_BOT_TOKEN not set"** | Verify `.env` exists and has token: `cat .env` |
| **Redis connection error** | Use `advanced_bot_fallback.py` (doesn't need Redis) |
| **Module not found errors** | Reinstall deps: `pip3 install -r requirements.txt` |
| **Port conflicts** | Bot doesn't use ports, check firewall for Telegram API |
| **High CPU usage** | Check process: `ps aux \| grep python` |

---

## 📋 FILE LOCATIONS

### **On Hetzner**
```
/opt/aiempire/telegram/
├── .env
├── advanced_bot.py
├── advanced_bot_fallback.py
├── redis_state.py
├── requirements.txt
├── systemd/
│   └── galaxia-bot.service
└── logs/
    └── bot.log
```

### **System**
```
/etc/systemd/system/advanced-bot.service
/tmp/advanced_bot.log
/tmp/bot.log (if using nohup)
```

---

## 🚀 NEXT IMMEDIATE STEPS

1. **SSH to Hetzner**: `ssh root@65.21.203.174`
2. **Start bot**: Choose Option 1, 2, or 3 above
3. **Test**: Send `/start` in Telegram
4. **Monitor**: `tail -f /tmp/advanced_bot.log`
5. **Profit**: Bot handles all Telegram interactions!

---

## 🎯 FEATURES READY

- ✅ **NLU System** - Intent detection (Ollama → Kimi → Claude ready)
- ✅ **Agent Routing** - Routes to 10 agents via Ant Protocol
- ✅ **Commands** - /start, /status, /revenue, /repair, /help
- ✅ **Error Recovery** - Automatic restart + fallback responses
- ✅ **State Management** - Redis integration ready
- ✅ **Logging** - Full debug logs to `/tmp/advanced_bot.log`
- ✅ **Auto-Restart** - Systemd ensures 99.9% uptime

---

## 📞 SUPPORT

### Quick Commands
```bash
# Status
systemctl status advanced-bot

# Restart
systemctl restart advanced-bot

# Stop
systemctl stop advanced-bot

# Logs (live)
journalctl -u advanced-bot -f

# Logs (tail)
tail -100 /tmp/advanced_bot.log

# Full service file
cat /etc/systemd/system/advanced-bot.service

# Check Python version
python3 --version

# Test imports
python3 -c "import redis, aiohttp, telegram; print('✅ All imports OK')"
```

### Documentation
- **Features**: See `ADVANCED_BOT_README.md`
- **Full setup**: See `DEPLOYMENT_GUIDE.md`
- **Status**: See `READY_FOR_DEPLOYMENT.md`

---

**Status:** Production Ready 🚀
**Deployment Time:** ~5 minutes
**Uptime Target:** 99.9%

Let's go live! 🎉
