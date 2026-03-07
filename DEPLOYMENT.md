# 🚀 DEPLOYMENT SCRIPTS - QUICK START

## Three Steps to LIVE Deployment

### **Step 1: Make scripts executable**
```bash
chmod +x deploy.sh health-check.sh
```

### **Step 2: Deploy!**
```bash
./deploy.sh
```

This will:
1. ✅ Verify SSH access to Hetzner
2. ✅ Create bot directories
3. ✅ Upload bot files
4. ✅ Install Python dependencies
5. ✅ Configure systemd service
6. ✅ Start the bot

**Time:** ~3-5 minutes

### **Step 3: Test**
After deployment, in Telegram:
```
/start
```

You should see the bot menu!

---

## 🧪 Health Check (Anytime)

```bash
./health-check.sh
```

Shows:
- ✅ SSH access
- ✅ Bot running status
- ✅ Resource usage (CPU, RAM)
- ✅ Dependencies
- ✅ Redis status
- ✅ Ant Protocol connectivity
- ✅ Recent logs
- ✅ Error summary

---

## ⚡ Manual Commands (if needed)

**Check bot status:**
```bash
ssh root@65.21.203.174 'systemctl status advanced-bot'
```

**View live logs:**
```bash
ssh root@65.21.203.174 'journalctl -u advanced-bot -f'
```

**Restart bot:**
```bash
ssh root@65.21.203.174 'systemctl restart advanced-bot'
```

**Stop bot:**
```bash
ssh root@65.21.203.174 'systemctl stop advanced-bot'
```

**Check processes:**
```bash
ssh root@65.21.203.174 'ps aux | grep advanced_bot'
```

---

## 🔍 Troubleshooting

| Problem | Solution |
|---------|----------|
| `Permission denied (publickey)` | Setup SSH key: `ssh-keygen -t ed25519` then `ssh-copy-id root@65.21.203.174` |
| Bot won't start | Check logs: `./health-check.sh` or `journalctl -u advanced-bot` |
| Redis connection error | Verify Redis running: `redis-cli ping` |
| Ant Protocol unreachable | Not critical for basic commands - will fallback to Ollama |
| High memory usage | Normal - will stabilize after initial load |

---

## 📊 Expected Output from `./deploy.sh`

```
╔════════════════════════════════════════════════════════╗
║  Advanced Telegram Bot - Hetzner Deployment            ║
╚════════════════════════════════════════════════════════╝

[1/5] Verifying SSH access to Hetzner...
✓ SSH access OK

[2/5] Creating directories on Hetzner...
✓ Directories created

[3/5] Uploading bot files...
✓ Files uploaded

[4/5] Installing dependencies and configuring systemd...
✓ Dependencies installed

[5/5] Starting bot service...
✓ Bot started

╔════════════════════════════════════════════════════════╗
✓ DEPLOYMENT COMPLETE!
╚════════════════════════════════════════════════════════╝
```

---

## ✅ After Deployment Checklist

- [ ] Ran `./deploy.sh` successfully
- [ ] `systemctl status advanced-bot` shows "active (running)"
- [ ] `./health-check.sh` shows all green ✓
- [ ] Sent `/start` to bot in Telegram
- [ ] Bot responded with help menu
- [ ] Tested `/status` command
- [ ] Tested natural language: "What's the system status?"
- [ ] Tested agent routing: "Run agent 1"

---

## 📞 Need Help?

**See full deployment guide:**
```bash
cat telegram/DEPLOYMENT_GUIDE.md
```

**Check status anytime:**
```bash
./health-check.sh
```

**View bot features:**
```bash
cat telegram/ADVANCED_BOT_README.md
```

---

**Ready?** 🚀
```bash
./deploy.sh
```
