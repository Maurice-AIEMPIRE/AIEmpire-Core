# AI EMPIRE DEPLOYMENT GUIDE

**Version**: v1.0 (2026-02-10)
**Owner**: CLAUDE (Chief Architect)
**Status**: Ready for Phase 1 Deployment

---

## 📋 TABLE OF CONTENTS

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Step 1: Secrets Management Setup](#step-1-secrets-management-setup)
3. [Step 2: Network & Firewall](#step-2-network--firewall)
4. [Step 3: Deploy to Production](#step-3-deploy-to-production)
5. [Step 4: Verify & Test](#step-4-verify--test)
6. [Step 5: Monitoring & Alerts](#step-5-monitoring--alerts)
7. [Rollback Procedure](#rollback-procedure)
8. [Support & Escalation](#support--escalation)

---

## ✅ PRE-DEPLOYMENT CHECKLIST

**SECURITY (Non-Negotiable)**:
- [ ] All secrets encrypted with sops/age (no .env in plaintext)
- [ ] TLS certificates ready (Let's Encrypt or self-signed)
- [ ] Firewall rules tested (UFW deny-all inbound)
- [ ] VPN setup (Tailscale) OR reverse proxy auth ready
- [ ] Database backups tested (restore from backup works)
- [ ] Monitoring stack deployed (Prometheus + Grafana + Loki)
- [ ] Security gates passing (no vulnerabilities in scanning)

**OPERATIONAL**:
- [ ] All services have healthchecks configured
- [ ] Resource limits appropriate for your system
- [ ] Logging centralized (JSON format)
- [ ] Incident response runbooks reviewed
- [ ] On-call contact list defined
- [ ] Backup retention policy set

**BUSINESS**:
- [ ] Revenue channels identified (Gumroad, Fiverr, etc.)
- [ ] Cost tracking enabled (API spending limits)
- [ ] Alerting configured (P1/P2/P3)
- [ ] Approval from Maurice obtained

---

## STEP 1: SECRETS MANAGEMENT SETUP

### 1.1 Install Tools

```bash
# macOS
brew install sops age

# Linux (Ubuntu/Debian)
sudo apt-get install sops
curl --location --output age.tar.gz https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz
tar xzf age.tar.gz && sudo mv age/age /usr/local/bin/

# Verify
sops --version
age --version
```

### 1.2 Generate Age Encryption Key

```bash
# Create keyring directory
mkdir -p ~/.age

# Generate key (stores both public + private)
age-keygen -o ~/.age/keys.txt

# Make it readable (permissions matter!)
chmod 600 ~/.age/keys.txt

# Extract public key for sharing/documentation
grep "public key:" ~/.age/keys.txt > ~/.age/public.txt

echo "✅ Age key created at ~/.age/keys.txt"
cat ~/.age/public.txt
```

### 1.3 Encrypt Existing .env File

```bash
# Backup original
cp .env .env.bak

# Encrypt
export SOPS_AGE_KEY_FILE=~/.age/keys.txt
sops --encrypt .env > .env.enc

# Verify encrypted
file .env.enc  # Should be JSON
head -2 .env.enc

# NEVER COMMIT .env (add to .gitignore if not already)
grep ".env$" .gitignore || echo ".env" >> .gitignore

# SAFE TO COMMIT .env.enc
git add .env.enc
git commit -m "chore: encrypt secrets with sops/age"
```

### 1.4 Configure CI/CD Secret Rotation

```bash
# Store age private key in GitHub Secrets
# Go to: https://github.com/mauricepfeifer-ctrl/AIEmpire-Core/settings/secrets/actions
# Add new  secret: "AGE_PRIVATE_KEY" = contents of ~/.age/keys.txt

# Test locally
export SOPS_AGE_KEY_FILE=~/.age/keys.txt
sops --decrypt .env.enc > /tmp/.env.test
echo "Decrypted secrets:"
head -5 /tmp/.env.test && rm /tmp/.env.test

echo "✅ Secrets encrypted and CI/CD configured"
```

---

## STEP 2: NETWORK & FIREWALL

### 2.1 VPN Setup (Tailscale - Recommended)

```bash
# Install Tailscale (free tier = unlimited devices + users)
# macOS
brew install tailscale && brew services start tailscale

# Linux
curl https://pkgr.tailscale.com/stable/ubuntu/focal.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-stable-noarmor.gpg > /dev/null
curl https://pkgr.tailscale.com/stable/ubuntu/focal.list | sudo tee /etc/apt/sources.list.d/tailscale.list
sudo apt-get update && sudo apt-get install tailscale
sudo systemctl enable tailscale
sudo systemctl start tailscale

# Authenticate (opens browser)
sudo tailscale up

# Get VPN IP
TAILSCALE_IP=$(tailscale ip -4)
echo "Your Tailscale IP: $TAILSCALE_IP"
```

### 2.2 Firewall Setup (UFW - Linux)

```bash
# macOS uses built-in firewall (System Preferences → Security & Privacy)
# Linux uses UFW

# Linux: Enable UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (Traefik)
sudo ufw allow 443/tcp   # HTTPS (Traefik)
# Optional: restrict SSH to Tailscale IP only
# sudo ufw allow from $TAILSCALE_IP to any port 22
sudo ufw enable

# Verify
sudo ufw status
```

### 2.3 Update Traefik Configuration

Edit `.env` (or `.env.enc`):
```env
# Traefik
LETSENCRYPT_EMAIL=admin@example.com
TRAEFIK_USERS=admin:$2y$05$...   # htpasswd hash

# VPN (Tailscale IP for whitelist)
TAILSCALE_IP=100.x.y.z            # From "tailscale ip -4"
```

---

## STEP 3: DEPLOY TO PRODUCTION

### 3.1 Deploy Base Infrastructure

```bash
cd /Users/maurice/AIEmpire-Core

# Decrypt secrets (create temporary .env)
export SOPS_AGE_KEY_FILE=~/.age/keys.txt
sops --decrypt .env.enc > .env.tmp
source .env.tmp

# Start base services (without production overrides yet)
docker-compose up -d

# Wait for healthchecks (2-3 min)
echo "Waiting for services to be healthy..."
sleep 30

# Check health
docker-compose ps
docker-compose logs --tail=20 empire-api
```

### 3.2 Deploy Production Overrides (TLS + Monitoring)

```bash
# Add production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# This ADDS: Traefik, Prometheus, Grafana, Loki, Promtail
# And applies security hardening to existing services

# Wait for new services
echo "Waiting for monitoring stack..."
sleep 30

# Verify all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Should show all HEALTHY (✓)
```

### 3.3 Setup Monitoring Dashboards

```bash
# Copy monitoring configs
mkdir -p ops/monitoring/grafana/{dashboards,datasources}

# Copy Prometheus config (see /ops/monitoring/prometheus.yml below)
# Copy Grafana datasources (see /ops/monitoring/grafana/datasources/ below)
# Copy Loki config (see /ops/monitoring/loki-config.yml below)

# Access Grafana
# URL: https://localhost:3000 (or https://grafana.yourdomain.com if DNS configured)
# Default user/pass: admin / $GRAFANA_PASSWORD

# Import dashboards:
# 1. Docker container metrics (Grafana ID: 893)
# 2. Node Exporter metrics (Grafana ID: 1860)
# 3. Custom AI Empire dashboard (provided in /ops/monitoring/dashboards/)
```

### 3.4 Configure Logging

```bash
# Verify Loki is collecting logs
curl -s http://localhost:3100/api/v1/status/buildinfo | jq .

# Tail real-time logs
curl -s  'http://localhost:3100/loki/api/v1/tail?query={job="docker"}' | jq .

# Logs should flow from all containers → Promtail → Loki → Grafana
```

### 3.5 Clean Up Temporary Files

```bash
# Remove decrypted .env (IMPORTANT!)
rm .env.tmp ~/.age/keys.txt.tmp 2>/dev/null

# Verify no secrets in shell history
history | grep -i "api_key\|password" && echo "⚠️ Secrets in history!" || echo "✅ History clean"

# Verify no secrets committed
git log --all -p | grep -i "api_key" && echo "⚠️ Secrets in git!" || echo "✅ Git clean"
```

---

## STEP 4: VERIFY & TEST

### 4.1 Health Checks

```bash
# Test all service endpoints
curl -s http://localhost:3333/health | jq .      # Empire API
curl -s http://localhost:5432 || echo "PostgreSQL OK"
curl -s http://localhost:6379 || echo "Redis OK"
curl -s http://localhost:11434/api/tags | jq .   # Ollama
curl -s http://localhost:8000/api/v1/heartbeat   # ChromaDB
curl -s http://localhost:5678/rest/health | jq . # n8n
curl -s http://localhost:9090/-/healthy          # Prometheus
```

### 4.2 Security Tests

```bash
# Test Traefik is enforcing TLS
curl -I http://localhost/  # Should redirect to HTTPS
# curl: (7) Failed to connect to localhost port 80

# Test API rate limiting
for i in {1..150}; do
  curl -s -H "Authorization: Bearer token" http://localhost:3333/api/action
done 2>&1 | grep -c "429"  # Should see rate limit responses

# Test secrets are not exposed
curl -s http://localhost:3333/health | grep -i "api_key\|password" || echo "✅ No secrets exposed"

# Test CSP (Content Security Policy)
curl -I https://localhost:3333 | grep -i "content-security"
```

### 4.3 Data Flow Tests

```bash
# Test 1: Create a task via API
curl -X POST http://localhost:3333/api/action \
  -H "Authorization: Bearer $(jwt_encode admin secret_key 24h)" \
  -H "Content-Type: application/json" \
  -d '{"action": "generate_content", "prompt": "Write a 3-sentence summary of AI"}'

# Test 2: Verify data in PostgreSQL
docker-compose exec postgresql psql -U empire -d empire_db -c "SELECT * FROM messages LIMIT 1;"

# Test 3: Verify caching in Redis
docker-compose exec redis redis-cli -a redis_pass GET "task:latest"

# Test 4: Verify vectors in ChromaDB
curl -s http://localhost:8000/api/v1/collections | jq .

# All should return data successfully
```

### 4.4 Monitoring Tests

```bash
# Test Prometheus is scraping metrics
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'

# Test alert rule evaluation
curl -s "http://localhost:9090/api/v1/query?query=up" | jq .

# Test Loki is collecting logs
curl -s 'http://localhost:3100/loki/api/v1/query_range?query={job="docker"}&start=1&end=9&limit=10' | jq '.data.result | length'

# Test Grafana can reach Prometheus + Loki
curl -s http://localhost:3000/api/datasources | jq '.[] | .name'

# Should list: "Prometheus", "Loki", etc.
```

---

## STEP 5: MONITORING & ALERTS

### 5.1 Create Critical Alerts

**File**: `/ops/monitoring/prometheus-rules.yml`

```yaml
groups:
- name: ai_empire
  interval: 30s
  rules:
  # CRITICAL: API down or unhealthy
  - alert: APIDown
    expr: up{job="empire-api"} == 0
     for: 2m
    annotations:
      severity: P1
      summary: "Empire API is DOWN"
      action: "Restart service or escalate"

  # CRITICAL: Daily API cost exceeded
  - alert: APIBudgetExceeded
    expr: increase(api_cost_usd_total[1d]) > 50
    for: 1m
    annotations:
      severity: P1
      summary: "API cost > EUR 50/day - pausing agents"

  # CRITICAL: Database connection leak
  - alert: PostgreSQLConnectionLeak
    expr: pg_connections > 100
    for: 5m
    annotations:
      severity: P1
      summary: "PostgreSQL > 100 connections"

  # HIGH: High CPU usage
  - alert: HighCPU
    expr: (100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)) > 85
    for: 5m
    annotations:
      severity: P2
      summary: "CPU > 85% on {{ $labels.instance }}"

  # HIGH: High memory usage
  - alert: HighMemory
    expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.85
    for: 5m
    annotations:
      severity: P2
      summary: "Memory > 85% on {{ $labels.instance }}"

  # MEDIUM: High disk usage
  - alert: HighDisk
    expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) > 0.80
    for: 10m
    annotations:
      severity: P3
      summary: "Disk > 80% on {{ $labels.device }}"
```

### 5.2 Setup Alert Routing

**Notification Destinations** (add to AlertManager config):
```yaml
global:
  resolve_timeout: 5m
  slack_api_url: ${SLACK_WEBHOOK_URL}   # Slack
  pagerduty_url: ${PAGERDUTY_API_URL}   # PagerDuty

route:
  group_by: ['alertname']
  receiver: 'default'
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
- name: 'default'
  slack_configs:
  - channel: '#alerts'
    title: '[{{ .GroupLabels.severity }}] {{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}'
```

*Configuration for Slack/PagerDuty/Email in `/ops/monitoring/alertmanager.yml`*

---

## 🔄 ROLLBACK PROCEDURE

**If something goes wrong during deployment:**

```bash
# Option 1: Rollback to Previous Compose (quick)
docker-compose down
docker-compose -f docker-compose.yml up -d  # Only base services, no prod overrides

# Option 2: Rollback Database (restore from backup)
docker-compose down
./ops/backup/restore-from-backup.sh --timestamp "1h ago"
docker-compose up -d

# Option 3: Full Rollback to Git Commit
git log --oneline | head -10
git reset --hard <commit_hash>
docker-compose down
docker system prune -a  # Remove all images
docker-compose up -d --build
```

**Recovery Time Targets (RTO)**:
- API service restart: 30s
- Database recovery: 5-10 min (depends on backup size)
- Full system recovery: 15-20 min

---

## 📞 SUPPORT & ESCALATION

### Runbook for Common Issues

| Issue | Symptoms | Resolution |
|-------|----------|-----------|
| Traefik SSL cert expired | HTTPS 404 / browser warning | Run `docker-compose restart traefik` or renew certificate |
| API rate limiting too aggressive | Legitimate requests blocked (429) | Increase limit in Traefik config + restart |
| Prometheus storage full | Disk 100% / alerts stopped | `prometheus_data` volume filling up, reduce retention policy |
| PostgreSQL replication lag | Data inconsistent across regions | Check network, or fall back to primary-only mode |
| Secret rotation expired | API calls failing (401) | Decrypt `.env.enc`, rotate key, re-encrypt, redeploy |
| Agent swarm runaway (cost spikes) | API bill spike > EUR 100/day | `redis-cli flushall` to clear task queue, pause agents |

### Escalation Path

```
Issue detected
  ↓
Is it P1 (system down / breach)?
  ├─ YES → Page CLAUDE immediately (24/7)
  └─ NO → Log in Slack #alerts, assign to on-call
        ↓
        Can on-call fix in < 30 min?
        ├─ YES → Execute fix, post resolution in #incidents
        └─ NO → Escalate to CLAUDE + Maurice
```

---

## ✅ DEPLOYMENT SUCCESS CRITERIA

**All of these must be true**:

1. ✅ All services healthy (docker-compose ps shows GREEN)
2. ✅ TLS certificates valid (https:// works without warnings)
3. ✅ Monitoring active (Prometheus scraping, Loki collecting)
4. ✅ Alerts configured (test alert fired + notified)
5. ✅ Backups working (restore test passed)
6. ✅ Secrets encrypted (no plaintext .env in repo)
7. ✅ Security scanning passed (no vulns in images)
8. ✅ Load test passed (100 concurrent users OK)
9. ✅ Rollback tested (can revert in < 5 min)
10. ✅ Team trained (all runbooks reviewed)

---

## 📈 NEXT STEPS (ORDERED)

1. **TODAY (Feb 10-11)**: Review this guide, set up VPN + firewall
2. **TOMORROW (Feb 12-13)**: Encrypt secrets, deploy base services
3. **DAY 3 (Feb 14)**: Deploy prod overrides, setup monitoring
4. **DAY 4 (Feb 15)**: Run security tests, configure alerts
5. **DAY 5 (Feb 16)**: Load testing, rollback drill, team training
6. **WEEK 2**: Revenue activation (Gumroad, Fiverr)
7. **WEEK 3+**: Scale & optimize based on monitoring data

---

**END OF DEPLOYMENT_GUIDE.md**

---

**Version**: v1.0
**Last Updated**: 2026-02-10
**Status**: READY FOR PRODUCTION
**Approval**: CLAUDE (Chief Architect) ✅
**Maurice Review**: _PENDING_
