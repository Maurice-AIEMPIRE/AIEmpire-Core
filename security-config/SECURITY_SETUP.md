# 🛡️ SECURITY CONFIGURATION
## Complete Security Setup for Maurice's AI Empire

**Priority:** CRITICAL  
**Status:** Implementation Ready

---

## 🎯 SECURITY OBJECTIVES

1. **Protect Mac Mini** - Main infrastructure
2. **Secure API Keys** - Prevent unauthorized access
3. **Backup Everything** - 3-2-1 rule
4. **Monitor 24/7** - Detect threats early
5. **Quick Recovery** - Minimize downtime

---

## 🔒 LAYER 1: MAC MINI HARDENING

### Firewall Configuration

```bash
# Enable macOS firewall
sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 1

# Allow specific ports only
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /opt/homebrew/bin/openclaw
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3

# Block all incoming by default
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setblockall on
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsigned on

# Verify
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

### Port Configuration

```
ALLOWED PORTS (Local Only):
- 18789: OpenClaw Gateway
- 8888: Atomic Reactor API
- 3500: CRM Server
- 6379: Redis
- 5432: PostgreSQL
- 11434: Ollama

BLOCKED:
- All other inbound ports
- Public internet access only via VPN
```

### System Updates

```bash
# Enable automatic updates
sudo softwareupdate --schedule on

# Check for updates daily
softwareupdate --list

# Install security updates immediately
sudo softwareupdate --install --recommended
```

---

## 🔐 LAYER 2: API KEY MANAGEMENT

### Using macOS Keychain

```bash
# Store API keys securely
security add-generic-password \
  -s "moonshot-api" \
  -a "maurice" \
  -w "sk-your-kimi-key-here" \
  -U

security add-generic-password \
  -s "anthropic-api" \
  -a "maurice" \
  -w "sk-your-claude-key-here" \
  -U

security add-generic-password \
  -s "github-token" \
  -a "maurice" \
  -w "ghp-your-github-token" \
  -U

# Retrieve in scripts
export MOONSHOT_API_KEY=$(security find-generic-password -s "moonshot-api" -a "maurice" -w)
export ANTHROPIC_API_KEY=$(security find-generic-password -s "anthropic-api" -a "maurice" -w)
```

### Environment Variables (Alternative)

```bash
# Add to ~/.zshrc
echo 'export MOONSHOT_API_KEY="sk-your-key"' >> ~/.zshrc
echo 'export ANTHROPIC_API_KEY="sk-your-key"' >> ~/.zshrc
echo 'export GITHUB_TOKEN="ghp-your-token"' >> ~/.zshrc

# Secure the file
chmod 600 ~/.zshrc

# Reload
source ~/.zshrc
```

### .env Files (For Projects)

```bash
# Create .env file
cat > /path/to/project/.env << EOF
MOONSHOT_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-your-key
GITHUB_TOKEN=ghp-your-token
EOF

# Secure it
chmod 600 .env

# Add to .gitignore
echo ".env" >> .gitignore
```

**CRITICAL:** Never commit .env files to Git!

---

## 💾 LAYER 3: 3-2-1 BACKUP STRATEGY

### The 3-2-1 Rule

```
3 COPIES of data:
  1. Production (Mac Mini)
  2. Local backup (External SSD)
  3. Cloud backup (Offsite)

2 DIFFERENT MEDIA:
  1. SSD/HDD (local)
  2. Cloud storage

1 OFFSITE:
  1. Cloud backup (Backblaze/iCloud)
```

### Time Machine Setup (Local Backup)

```bash
# Connect external SSD

# Enable Time Machine via GUI:
# System Preferences → Time Machine → Select Disk

# Or via command line:
sudo tmutil setdestination /Volumes/BackupDrive

# Enable automatic backups
sudo tmutil enable

# Start backup immediately
sudo tmutil startbackup

# Verify
tmutil status
```

### Cloud Backup Options

#### Option A: Backblaze (Recommended)

```bash
# Sign up: backblaze.com
# $7/month unlimited

# Download & install client
# Select folders to backup:
- ~/Documents
- ~/Desktop
- ~/.openclaw
- ~/work/AIEmpire-Core

# Exclude (too large):
- node_modules/
- .git/
- *.log
```

#### Option B: iCloud

```bash
# Enable iCloud Drive
# System Preferences → Apple ID → iCloud → iCloud Drive

# Sync folders:
- Documents
- Desktop
- OpenClaw config (~/.openclaw)

# Upgrade to 200GB: €2.99/month
```

#### Option C: Rsync to Remote Server

```bash
# Setup rsync script
cat > ~/backup.sh << 'EOF'
#!/bin/bash
rsync -avz --delete \
  --exclude 'node_modules' \
  --exclude '.git' \
  ~/work/AIEmpire-Core/ \
  user@remote-server:/backups/ai-empire/
EOF

chmod +x ~/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * ~/backup.sh") | crontab -
```

### Database Backups

```bash
# PostgreSQL backup script
cat > ~/backup-postgres.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/backups/postgres
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup all databases
pg_dumpall > $BACKUP_DIR/all_databases_$DATE.sql

# Compress
gzip $BACKUP_DIR/all_databases_$DATE.sql

# Keep last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
EOF

chmod +x ~/backup-postgres.sh

# Daily at 3 AM
(crontab -l 2>/dev/null; echo "0 3 * * * ~/backup-postgres.sh") | crontab -
```

```bash
# Redis backup
cat > ~/backup-redis.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/backups/redis
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Trigger save
redis-cli BGSAVE

# Wait for save to complete
LAST_SAVE=$(redis-cli LASTSAVE)
while [ $(redis-cli LASTSAVE) -eq $LAST_SAVE ]; do
  sleep 1
done

# Copy dump.rdb
cp /usr/local/var/db/redis/dump.rdb $BACKUP_DIR/dump_$DATE.rdb

# Compress
gzip $BACKUP_DIR/dump_$DATE.rdb

# Keep last 7 days
find $BACKUP_DIR -name "*.rdb.gz" -mtime +7 -delete
EOF

chmod +x ~/backup-redis.sh

# Every 6 hours
(crontab -l 2>/dev/null; echo "0 */6 * * * ~/backup-redis.sh") | crontab -
```

---

## 🚨 LAYER 4: MONITORING & ALERTS

### Security Monitoring Script

```python
#!/usr/bin/env python3
# security_monitor.py

import subprocess
import time
import smtplib
from email.message import EmailMessage

def check_firewall():
    """Check if firewall is enabled"""
    result = subprocess.run(
        ['sudo', '/usr/libexec/ApplicationFirewall/socketfilterfw', '--getglobalstate'],
        capture_output=True, text=True
    )
    return 'enabled' in result.stdout.lower()

def check_failed_logins():
    """Check for failed SSH login attempts"""
    result = subprocess.run(
        ['log', 'show', '--predicate', 'eventMessage contains "failed"', '--last', '1h'],
        capture_output=True, text=True
    )
    failed_count = result.stdout.count('failed')
    return failed_count

def check_disk_space():
    """Check available disk space"""
    result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    if len(lines) > 1:
        parts = lines[1].split()
        usage = int(parts[4].replace('%', ''))
        return usage

def check_api_rate_limits():
    """Check API usage against limits"""
    # Placeholder - implement based on your API tracking
    return {"kimi": 85, "claude": 45}

def send_alert(subject, message):
    """Send email alert"""
    msg = EmailMessage()
    msg['Subject'] = f'[SECURITY ALERT] {subject}'
    msg['From'] = 'alerts@mauriceai.com'
    msg['To'] = 'maurice@email.com'
    msg.set_content(message)
    
    # Use your email service
    # with smtplib.SMTP('smtp.gmail.com', 587) as server:
    #     server.starttls()
    #     server.login('your-email', 'your-password')
    #     server.send_message(msg)
    
    print(f"ALERT: {subject}\n{message}")

def run_security_checks():
    """Run all security checks"""
    alerts = []
    
    # Check firewall
    if not check_firewall():
        alerts.append("Firewall is DISABLED!")
    
    # Check failed logins
    failed_logins = check_failed_logins()
    if failed_logins > 10:
        alerts.append(f"High number of failed logins: {failed_logins}")
    
    # Check disk space
    disk_usage = check_disk_space()
    if disk_usage > 90:
        alerts.append(f"Disk space critical: {disk_usage}% used")
    
    # Check API limits
    api_usage = check_api_rate_limits()
    for api, usage in api_usage.items():
        if usage > 80:
            alerts.append(f"{api} API at {usage}% of limit")
    
    # Send alerts
    if alerts:
        send_alert(
            "Security Issues Detected",
            "\n".join(alerts)
        )
    
    return len(alerts) == 0

if __name__ == '__main__':
    while True:
        all_good = run_security_checks()
        if all_good:
            print("✅ All security checks passed")
        time.sleep(300)  # Check every 5 minutes
```

```bash
# Make executable
chmod +x security_monitor.py

# Run in background
nohup python3 security_monitor.py &

# Or add to crontab (every 5 min)
(crontab -l 2>/dev/null; echo "*/5 * * * * python3 ~/security_monitor.py") | crontab -
```

### Log Monitoring

```bash
# Monitor OpenClaw logs
tail -f ~/.openclaw/logs/gateway.log | grep -i "error\|warning\|fail"

# Monitor system logs
log stream --predicate 'eventMessage contains "error"' --level error

# Monitor authentication attempts
log show --predicate 'process == "authd"' --last 1h
```

---

## 🌐 LAYER 5: VPN / REMOTE ACCESS

### Tailscale Setup (Recommended)

```bash
# Install Tailscale
brew install tailscale

# Start Tailscale
sudo tailscale up

# Get your Tailscale IP
tailscale ip -4

# Connect from another device:
# 1. Install Tailscale on device
# 2. Login with same account
# 3. Access Mac Mini via Tailscale IP
# Example: http://100.x.x.x:18789
```

**Benefits:**
- Encrypted tunnel
- No port forwarding needed
- Access from anywhere
- Free for personal use

---

## 📋 SECURITY CHECKLIST

### Daily
- [ ] Check security_monitor.py output
- [ ] Verify backups completed
- [ ] Review unusual login attempts

### Weekly
- [ ] Test backup restoration
- [ ] Update all software
- [ ] Review API usage
- [ ] Check disk space

### Monthly
- [ ] Full security audit
- [ ] Rotate API keys (if needed)
- [ ] Review firewall rules
- [ ] Test incident response

---

## 🚨 INCIDENT RESPONSE PLAN

### If Mac Mini is Compromised

**IMMEDIATE (0-5 minutes):**
1. Disconnect from internet
2. Stop all services
3. Take snapshot of system state

**SHORT-TERM (5-30 minutes):**
1. Analyze logs
2. Identify entry point
3. Contain damage

**RECOVERY (30+ minutes):**
1. Restore from clean backup
2. Update all passwords/keys
3. Patch vulnerabilities
4. Resume operations

### If API Keys Leaked

**IMMEDIATE:**
1. Revoke compromised keys
2. Generate new keys
3. Update all systems

**INVESTIGATION:**
1. How did leak occur?
2. What data was accessed?
3. Who was affected?

**PREVENTION:**
1. Implement better key management
2. Add rotation policy
3. Update documentation

---

## ✅ SECURITY VALIDATION

### Test Checklist

```bash
# 1. Firewall enabled?
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 2. API keys not in code?
grep -r "sk-" ~/work/AIEmpire-Core/ --exclude-dir=.git

# 3. Backups working?
tmutil status
# Check Backblaze/iCloud status

# 4. SSH hardened?
cat /etc/ssh/sshd_config | grep "PasswordAuthentication\|PermitRootLogin"

# 5. System updated?
softwareupdate --list
```

---

## 📊 SECURITY DASHBOARD

```
┌─────────────────────────────────────────────────────────────┐
│ Security Dashboard - Maurice's AI Empire                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🔒 FIREWALL: ✅ Enabled                                    │
│ 🔐 API KEYS: ✅ Secured (Keychain)                         │
│ 💾 BACKUPS:  ✅ 3-2-1 Configured                           │
│ 🌐 VPN:      ✅ Tailscale Active                           │
│ 📊 MONITORING: ✅ Running                                   │
│                                                             │
│ LAST BACKUP:                                                │
│ • Time Machine: 2 hours ago ✅                              │
│ • Backblaze: 1 hour ago ✅                                  │
│ • PostgreSQL: 12 hours ago ✅                               │
│ • Redis: 3 hours ago ✅                                     │
│                                                             │
│ THREATS (Last 24h):                                         │
│ • Failed logins: 0                                          │
│ • Port scans: 0                                             │
│ • Malware: 0                                                │
│                                                             │
│ API USAGE:                                                  │
│ • Kimi: 45% of limit                                        │
│ • Claude: 32% of limit                                      │
│                                                             │
│ DISK SPACE: 65% used (350GB free)                          │
│ SYSTEM LOAD: Normal                                         │
│                                                             │
│ STATUS: 🟢 ALL SYSTEMS SECURE                              │
└─────────────────────────────────────────────────────────────┘
```

---

**Status:** 🛡️ **SECURITY READY** 🛡️

**Version:** 1.0  
**Created:** 2026-02-08  
**By:** Claude Opus 4.5  
**For:** Maurice's AI Empire
