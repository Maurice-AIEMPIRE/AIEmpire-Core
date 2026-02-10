# Incident Response Runbook — AI Empire

**Version:** 1.0
**Last Updated:** 2026-02-10
**Owner:** Maurice Pfeifer

---

## Purpose

This runbook provides **step-by-step procedures** for responding to operational incidents in the AI Empire 24/7 autonomous system. Follow these instructions when alerts fire or services fail.

**Key Principles:**
1. **Assess** — Understand scope and impact
2. **Contain** — Stop the bleeding, prevent further damage
3. **Resolve** — Fix the root cause
4. **Document** — Log what happened and why
5. **Improve** — Update systems to prevent recurrence

**Response Time Targets:**
- **Critical** (data breach, system down): <15 minutes
- **High** (service degraded, security alert): <1 hour
- **Medium** (performance issue, warning): <4 hours

---

## Incident Severity Levels

| Level | Description | Examples | Response Time |
|-------|-------------|----------|---------------|
| **SEV-1 (Critical)** | System down, data loss, security breach | PostgreSQL crash, data breach, all services offline | <15 min |
| **SEV-2 (High)** | Service degraded, high-risk security alert | OpenClaw down, CPU >95%, failed auth >10x | <1 hour |
| **SEV-3 (Medium)** | Performance issue, non-critical warning | Task queue >1000, LLM cost spike | <4 hours |
| **SEV-4 (Low)** | Informational, minor issue | Low disk space warning, single task failure | <24 hours |

---

## Incident #1: Service Down (Redis, PostgreSQL, Ollama, OpenClaw)

### Symptoms
- Health check fails (port not responding)
- Logs show connection errors
- Dashboard shows service as DOWN

### Immediate Actions (ASSESS)
1. **Check if service is running:**
   ```bash
   # Redis
   brew services list | grep redis
   redis-cli ping

   # PostgreSQL
   brew services list | grep postgresql
   psql -h localhost -U empire -d aiempire -c "SELECT 1;"

   # Ollama
   curl http://localhost:11434/api/version

   # OpenClaw
   curl http://localhost:18789/health
   ```

2. **Check logs for errors:**
   ```bash
   # Redis
   tail -100 /usr/local/var/log/redis.log

   # PostgreSQL
   tail -100 /usr/local/var/log/postgresql.log

   # Ollama
   tail -100 ~/.ollama/logs/server.log

   # OpenClaw
   tail -100 ~/.openclaw/logs/openclaw.log
   ```

### Resolution Steps (CONTAIN + RESOLVE)
1. **Restart service:**
   ```bash
   # Redis
   brew services restart redis

   # PostgreSQL
   brew services restart postgresql

   # Ollama
   pkill -f ollama
   ollama serve &

   # OpenClaw
   pkill -f openclaw
   python openclaw-config/start.py &
   ```

2. **Verify service is back:**
   ```bash
   ./ops/monitoring/health-check.sh
   ```

3. **If restart fails, check for:**
   - Port already in use: `lsof -i :6379` (kill process)
   - Permission errors: Check file ownership
   - Corrupted data: Restore from backup (see [Incident #5](#incident-5-data-loss))

### Post-Incident (DOCUMENT + IMPROVE)
1. **Log incident in PostgreSQL:**
   ```sql
   INSERT INTO incident_log (timestamp, severity, service, description, resolution)
   VALUES (NOW(), 'SEV-2', 'Redis', 'Service crashed due to OOM', 'Restarted, increased memory limit');
   ```

2. **Update monitoring:**
   - If crash was due to OOM: Lower Redis memory limit
   - If crash was due to disk full: Increase disk cleanup frequency

3. **Root cause analysis:**
   - Why did it crash? (OOM, disk full, bug, external attack?)
   - How to prevent? (Better monitoring, resource limits, auto-restart?)

---

## Incident #2: CPU/RAM Emergency (>95%/92%)

### Symptoms
- Resource Guard triggers EMERGENCY alert
- System sluggish, agents frozen
- `top` shows runaway process

### Immediate Actions (ASSESS)
1. **Check Resource Guard status:**
   ```bash
   python workflow-system/resource_guard.py
   ```

2. **Identify top processes:**
   ```bash
   top -o cpu
   top -o mem
   ```

### Resolution Steps (CONTAIN)
1. **Resource Guard auto-stops agents** (no manual action needed if integrated)

2. **If manual intervention required, kill runaway process:**
   ```bash
   # Find process ID
   ps aux | grep openclaw  # or other service
   kill -9 <PID>
   ```

3. **If Ollama consuming too much RAM:**
   ```bash
   pkill -f ollama
   # Wait 10 seconds
   ollama serve &
   # Reduce concurrency: Edit OpenClaw config to use smaller models
   ```

### Resolution Steps (RESOLVE)
1. **Identify root cause:**
   - Agent infinite loop? Check agent audit logs
   - Memory leak? Review recent code changes
   - Too many concurrent tasks? Lower concurrency limit

2. **Fix and restart:**
   ```bash
   # If config change needed
   vim openclaw-config/config.json
   # Restart OpenClaw
   pkill -f openclaw && python openclaw-config/start.py &
   ```

### Post-Incident
1. **Tune Resource Guard thresholds** (if false alarm)
2. **Add agent rate limits** (if agent loop caused issue)
3. **Review agent code** (if memory leak detected)

---

## Incident #3: Security Alert (Failed Auth, Suspicious Commands)

### Symptoms
- Alert: "Failed auth attempts >10 in 5 minutes"
- Alert: "Suspicious agent command detected" (e.g., `rm -rf`, `sudo`)
- Audit logs show unexpected activity

### Immediate Actions (ASSESS + CONTAIN)
1. **Review audit logs:**
   ```bash
   psql -h localhost -U empire -d aiempire -c \
   "SELECT * FROM agent_audit_logs WHERE risk_level = 'high' ORDER BY timestamp DESC LIMIT 20;"
   ```

2. **Check for unauthorized access:**
   ```bash
   # Failed SSH attempts (if SSH enabled)
   tail -100 /var/log/auth.log | grep "Failed password"

   # Failed web login attempts (OpenClaw, CRM)
   tail -100 ~/.openclaw/logs/access.log | grep "401"
   ```

3. **If breach suspected, IMMEDIATELY:**
   - **Disconnect from network** (turn off WiFi if remote attacker)
   - **Stop all agents:** `pkill -f openclaw && pkill -f atomic-reactor`
   - **Rotate all API keys** (GitHub, Kimi, Claude, Gumroad, X/Twitter)

### Resolution Steps (RESOLVE)
1. **If false alarm (Maurice testing):**
   - Document in incident log
   - Adjust alert threshold if needed

2. **If real attack:**
   - **Investigate:** Who? When? How? (IP address, user agent, logs)
   - **Block attacker:** Add IP to firewall deny list
   - **Patch vulnerability:** Update code, fix misconfiguration
   - **Restore from backup** (if data modified)

3. **If prompt injection attack:**
   - **Review agent prompts:** Check for jailbreak patterns
   - **Strengthen sandboxing:** Add more command restrictions
   - **Update agent code:** Improve input sanitization

### Post-Incident
1. **Security incident report:**
   - What happened?
   - How did attacker gain access?
   - What data was accessed/modified?
   - What actions were taken?

2. **Notify affected parties** (if customer data leaked, GDPR compliance)

3. **Update security controls:**
   - Add new detection rules
   - Strengthen sandboxing
   - Rotate secrets quarterly (not just on breach)

---

## Incident #4: Disk Space Critical (<5GB)

### Symptoms
- Alert: "Disk space <5GB"
- Services failing with "No space left on device"
- Backups failing

### Immediate Actions (ASSESS)
1. **Check disk usage:**
   ```bash
   df -h /
   du -sh ~/* | sort -rh | head -20
   ```

2. **Identify largest consumers:**
   ```bash
   du -sh ~/.openclaw/logs/*
   du -sh ~/.aiempire-backups/*
   du -sh ~/.ollama/models/*
   ```

### Resolution Steps (CONTAIN + RESOLVE)
1. **Delete old logs (>90 days):**
   ```bash
   find ~/.openclaw/logs -type f -mtime +90 -delete
   find /usr/local/var/log/ -type f -mtime +90 -delete
   ```

2. **Delete old backups (if retention policy not working):**
   ```bash
   find ~/.aiempire-backups/hourly -type f -mtime +3 -delete
   find ~/.aiempire-backups/daily -type f -mtime +30 -delete
   ```

3. **Clean up temp files:**
   ```bash
   rm -rf /tmp/aiempire-*
   rm -rf /tmp/ollama-*
   ```

4. **If still low, remove unused Ollama models:**
   ```bash
   ollama list
   ollama rm <unused_model>
   ```

### Post-Incident
1. **Increase disk space** (buy external drive or upgrade Mac storage)
2. **Automate cleanup:**
   ```bash
   # Add to crontab (daily at 3 AM)
   crontab -e
   0 3 * * * find ~/.openclaw/logs -type f -mtime +90 -delete
   ```

---

## Incident #5: Data Loss (PostgreSQL/Redis Corrupted)

### Symptoms
- Service won't start
- Logs show "corrupted data" or "invalid format"
- Queries fail with errors

### Immediate Actions (ASSESS)
1. **Stop service to prevent further corruption:**
   ```bash
   brew services stop postgresql
   brew services stop redis
   ```

2. **Check backup availability:**
   ```bash
   ls -lh ~/.aiempire-backups/hourly/postgres_*.enc
   ls -lh ~/.aiempire-backups/hourly/redis_*.enc
   ```

### Resolution Steps (RESOLVE)
1. **Restore from most recent backup:**
   ```bash
   # PostgreSQL
   BACKUP_FILE=$(ls -t ~/.aiempire-backups/hourly/postgres_*.enc | head -1)
   openssl enc -d -aes-256-cbc -pbkdf2 -in "$BACKUP_FILE" -k "$ENCRYPTION_KEY" | gunzip | \
   psql -h localhost -U empire -d aiempire

   # Redis
   BACKUP_FILE=$(ls -t ~/.aiempire-backups/hourly/redis_*.enc | head -1)
   openssl enc -d -aes-256-cbc -pbkdf2 -in "$BACKUP_FILE" -k "$ENCRYPTION_KEY" | \
   gunzip > /usr/local/var/db/redis/dump.rdb
   ```

2. **Restart services:**
   ```bash
   brew services start postgresql
   brew services start redis
   ```

3. **Verify data integrity:**
   ```bash
   psql -h localhost -U empire -d aiempire -c "SELECT COUNT(*) FROM agent_audit_logs;"
   redis-cli DBSIZE
   ```

### Post-Incident
1. **Root cause analysis:**
   - Why did corruption occur? (Sudden power loss, disk failure, bug?)
   - How to prevent? (UPS, better error handling, more frequent backups?)

2. **Test backups immediately:**
   ```bash
   ./ops/backup/restore-test.sh
   ```

3. **Document data loss:**
   - How much data was lost? (hours, days?)
   - What impact on operations? (revenue, leads, tasks?)

---

## Incident #6: Backup Failure

### Symptoms
- Alert: "Backup failed"
- Backup script exited with error
- No recent backup files

### Immediate Actions (ASSESS)
1. **Check backup script logs:**
   ```bash
   tail -100 ~/.openclaw/logs/backup.log
   ```

2. **Run backup manually to reproduce error:**
   ```bash
   ./ops/backup/backup.sh
   ```

### Resolution Steps (RESOLVE)
1. **Common issues:**
   - **Encryption key not found:**
     ```bash
     security add-generic-password -a "$USER" -s "aiempire-backup-key" -w "your_key_here"
     ```
   - **PostgreSQL password not found:**
     ```bash
     security add-generic-password -a "$USER" -s "aiempire-postgres" -w "your_password_here"
     ```
   - **Disk full:** See [Incident #4](#incident-4-disk-space-critical-5gb)
   - **Service down:** See [Incident #1](#incident-1-service-down)

2. **Fix issue and re-run backup:**
   ```bash
   ./ops/backup/backup.sh
   ```

### Post-Incident
1. **Add monitoring for backup script:**
   ```bash
   # Cron job checks if backup ran today
   0 8 * * * [ -f ~/.aiempire-backups/hourly/postgres_$(date +%Y%m%d)*.enc ] || echo "Backup failed yesterday" | mail -s "Backup Alert" maurice@example.com
   ```

---

## Incident #7: Agent Goes Rogue (Infinite Loop, Destructive Action)

### Symptoms
- Agent runs 100+ commands in 1 minute
- Agent tries to run forbidden commands (`rm -rf`, `sudo`)
- Audit logs show unusual behavior

### Immediate Actions (CONTAIN)
1. **Stop agent immediately:**
   ```bash
   pkill -f openclaw
   ```

2. **Review audit logs:**
   ```bash
   psql -h localhost -U empire -d aiempire -c \
   "SELECT * FROM agent_audit_logs WHERE agent_name = 'rogue_agent' ORDER BY timestamp DESC LIMIT 50;"
   ```

3. **Check for damage:**
   - Files deleted? Check `~/.openclaw/workspace/`
   - Secrets leaked? Check outbound network logs
   - Data modified? Check PostgreSQL recent queries

### Resolution Steps (RESOLVE)
1. **If files deleted, restore from backup:**
   ```bash
   # Restore entire workspace
   rsync -av ~/.aiempire-backups/daily/workspace_latest/ ~/.openclaw/workspace/
   ```

2. **If prompt injection suspected:**
   - **Review agent prompt:** Look for "ignore previous instructions"
   - **Strengthen sandboxing:** Add more command restrictions
   - **Update agent code:** Improve input validation

3. **Fix bug and restart agent:**
   ```bash
   # Update config to disable problematic agent
   vim openclaw-config/config.json
   # Restart
   python openclaw-config/start.py &
   ```

### Post-Incident
1. **Red-team agent prompts quarterly** (simulate attacks)
2. **Add anomaly detection** (alert if agent runs >50 commands/minute)
3. **Review agent code** (fix infinite loop, add retry limits)

---

## Escalation Path

### Level 1: Automated Response
- Resource Guard stops agents at >95% CPU/RAM
- Health checks restart services automatically (future)

### Level 2: Dashboard Alert
- Warning displayed in dashboard
- Owner checks when convenient (<4 hours)

### Level 3: Telegram Notification
- Critical alert sent to Maurice
- Response required within 1 hour

### Level 4: SMS + Email
- Emergency alert (data breach, system down)
- Response required within 15 minutes

### Level 5: Manual Intervention
- Maurice logs in, follows runbook
- If unable to resolve, escalate to:
  - GitHub community (for bugs)
  - Cloud provider support (for infra issues)
  - Security consultant (for breaches)

---

## Post-Incident Review Template

After every SEV-1 or SEV-2 incident:

```markdown
## Incident Post-Mortem

**Date:** 2026-XX-XX
**Severity:** SEV-X
**Duration:** X hours
**Services Affected:** Redis, PostgreSQL, etc.

### Timeline
- 14:00 — Alert triggered: "Redis DOWN"
- 14:05 — Maurice investigated logs
- 14:10 — Root cause identified: OOM
- 14:15 — Service restarted, restored
- 14:20 — Verified all services healthy

### Root Cause
Redis consumed 95% RAM due to...

### Impact
- X tasks failed
- X customers affected (if any)
- EUR X revenue lost (if applicable)

### Resolution
- Restarted Redis
- Increased memory limit
- Added better monitoring

### Action Items
- [ ] Update Redis config (memory limit)
- [ ] Add OOM alerting
- [ ] Test backup restore (verify)

### Lessons Learned
- Memory limits should be 80% of available RAM (not 95%)
- Need better OOM alerting before crash
```

---

**Last Updated:** 2026-02-10
**Owner:** Maurice Pfeifer
**Status:** Living document — update after every major incident
