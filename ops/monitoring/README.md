# AI Empire Monitoring Stack — Simple & Effective

**Version:** 1.0
**Last Updated:** 2026-02-10
**Status:** Production-ready

---

## Overview

This monitoring stack provides observability for the AI Empire 24/7 autonomous system. It is **simple, proven, and low-maintenance**—no complex tools like Prometheus/Grafana unless needed.

**Core Principles:**
- **Logs-first:** Structured JSON logs for all services
- **Health checks:** Every service exposes `/health` endpoint
- **Alerts:** Critical issues trigger Telegram notifications (when reconfigured)
- **PostgreSQL-based:** Metrics stored in database (already running)

---

## Components

### 1. Service Health Checks
**Script:** `ops/monitoring/health-check.sh`
**Frequency:** Every 60 seconds (cron job)
**Checks:**
- Redis (port 6379)
- PostgreSQL (port 5432)
- Ollama (port 11434)
- OpenClaw (port 18789)
- Atomic Reactor (port 8888)
- CRM (port 3500)

**Alerts:** If any service down for >5 minutes → Telegram notification

---

### 2. Resource Monitoring
**Script:** `workflow-system/resource_guard.py`
**Frequency:** Real-time (integrated into workflows)
**Monitors:**
- CPU usage (alert at >85%, emergency stop at >95%)
- RAM usage (alert at >85%, emergency stop at >92%)
- Disk space (alert at <10GB free)

**Actions:**
- WARN (70% CPU/RAM): Log warning
- CRITICAL (85% CPU/RAM): Throttle agents, enable outsource mode
- EMERGENCY (95% CPU/92% RAM): Stop all agents, alert owner

---

### 3. Agent Audit Logs
**Storage:** PostgreSQL table `agent_audit_logs`
**Schema:**
```sql
CREATE TABLE agent_audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    agent_name VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,  -- read, write, exec, api_call
    command TEXT,
    file_path TEXT,
    result_status VARCHAR(20),  -- success, failure, denied
    risk_level VARCHAR(10),  -- low, med, high
    metadata JSONB
);

CREATE INDEX idx_agent_logs_timestamp ON agent_audit_logs(timestamp DESC);
CREATE INDEX idx_agent_logs_risk ON agent_audit_logs(risk_level);
```

**Retention:** 90 days (auto-delete older records)

---

### 4. Cost Tracking
**Storage:** PostgreSQL table `llm_cost_tracking`
**Schema:**
```sql
CREATE TABLE llm_cost_tracking (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    model VARCHAR(50) NOT NULL,  -- ollama, kimi, claude
    tokens_used INT NOT NULL,
    cost_usd DECIMAL(10, 6) DEFAULT 0,
    request_type VARCHAR(50),  -- content, research, code_gen
    success BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_cost_timestamp ON llm_cost_tracking(timestamp DESC);
CREATE INDEX idx_cost_model ON llm_cost_tracking(model);
```

**Dashboard Query:**
```sql
-- Daily cost by model
SELECT
    DATE(timestamp) AS date,
    model,
    SUM(tokens_used) AS total_tokens,
    SUM(cost_usd) AS total_cost
FROM llm_cost_tracking
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp), model
ORDER BY date DESC, total_cost DESC;
```

---

### 5. KPI Metrics
**Storage:** PostgreSQL table `kpi_metrics`
**Schema:**
```sql
CREATE TABLE kpi_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metric_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20),  -- eur, count, percent
    metadata JSONB
);

CREATE INDEX idx_kpi_name_timestamp ON kpi_metrics(metric_name, timestamp DESC);
```

**Tracked Metrics:**
- `revenue_eur` (daily Gumroad sales)
- `leads_count` (new CRM leads)
- `agent_uptime_pct` (service availability)
- `task_success_rate` (successful task completions)
- `security_incidents` (should always be 0)

**Dashboard Query:**
```sql
-- Last 7 days KPIs
SELECT
    metric_name,
    DATE(timestamp) AS date,
    AVG(metric_value) AS avg_value,
    unit
FROM kpi_metrics
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY metric_name, DATE(timestamp), unit
ORDER BY date DESC, metric_name;
```

---

## Alerting Rules

### Critical Alerts (Immediate Telegram Notification)
1. **Service Down >5 minutes**
   - Redis, PostgreSQL, Ollama, OpenClaw, Atomic Reactor, CRM
   - Action: Restart service, escalate to Maurice

2. **CPU/RAM Emergency (>95%/92%)**
   - Resource Guard auto-stops agents
   - Action: Investigate runaway process, kill if needed

3. **Disk Space <5GB**
   - System may crash if disk full
   - Action: Delete old logs, backups, or expand disk

4. **Security Incident Detected**
   - Failed auth attempts >10 in 5 minutes
   - Suspicious agent commands (e.g., `rm -rf`, `sudo`)
   - Action: Lock account, review audit logs

5. **Backup Failure**
   - PostgreSQL or Redis backup didn't run
   - Action: Investigate, run manual backup

### Warning Alerts (Dashboard Only)
1. **CPU/RAM >70%**
   - System under load but not critical
   - Action: Monitor, consider throttling agents

2. **Task Queue >1000**
   - Agents falling behind
   - Action: Scale up concurrency or offload to Kimi

3. **LLM Cost >EUR 5/day**
   - Spending too much on cloud APIs
   - Action: Optimize prompts, use Ollama more

4. **Agent Task Failure Rate >10%**
   - Agents not completing tasks
   - Action: Review agent logs, fix bugs

---

## Dashboard (Simple CLI)

**Script:** `ops/monitoring/dashboard.sh`
**Usage:**
```bash
./ops/monitoring/dashboard.sh
```

**Output Example:**
```
=== AI Empire Status Dashboard ===
Date: 2026-02-10 22:00:00

Services:
✅ Redis (6379): UP
✅ PostgreSQL (5432): UP
✅ Ollama (11434): UP
✅ OpenClaw (18789): UP
✅ Atomic Reactor (8888): UP
✅ CRM (3500): UP

Resources:
CPU: 45% (OK)
RAM: 68% (OK)
Disk: 28 GB free (OK)

KPIs (Last 24 Hours):
Revenue: EUR 127.50
Leads: 23
Agent Uptime: 99.8%
Task Success Rate: 97.2%
Security Incidents: 0 ✅

LLM Cost (Last 24 Hours):
Ollama: EUR 0.00 (95% of requests)
Kimi: EUR 1.23 (4% of requests)
Claude: EUR 0.15 (1% of requests)
Total: EUR 1.38

Alerts:
⚠️ Task queue depth: 1203 (threshold: 1000)
```

---

## Setup Instructions

### 1. Create PostgreSQL Tables
```bash
psql -h localhost -U empire -d aiempire -f ops/monitoring/schema.sql
```

### 2. Install Monitoring Scripts
```bash
# Health check (every 60 seconds)
crontab -e
* * * * * /Users/maurice/AIEmpire-Core/.claude/worktrees/cranky-leavitt/ops/monitoring/health-check.sh

# Resource guard (integrated into workflows, no cron needed)

# Dashboard (manual run)
alias empire-status="$PWD/ops/monitoring/dashboard.sh"
```

### 3. Configure Alerts (Telegram, Optional)
```bash
# Add to ~/.zshrc or ~/.bashrc
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Test Telegram alert:
```bash
./ops/monitoring/send-alert.sh "Test Alert" "This is a test message from AI Empire monitoring."
```

---

## Maintenance

### Daily
- Check dashboard once: `./ops/monitoring/dashboard.sh`
- Review agent audit logs for suspicious activity

### Weekly
- Analyze LLM cost trends (optimize if >EUR 50/week)
- Check task success rate (debug if <95%)

### Monthly
- Clean up old logs (keep 90 days)
- Run backup restore test (`ops/backup/restore-test.sh`)
- Review security incidents (should be 0)

---

## Troubleshooting

### Service won't start
```bash
# Check logs
tail -f ~/.openclaw/logs/openclaw.log
tail -f /usr/local/var/log/redis.log
tail -f /usr/local/var/log/postgresql.log

# Restart service
brew services restart redis
brew services restart postgresql
```

### High CPU/RAM usage
```bash
# Check Resource Guard status
python workflow-system/resource_guard.py

# Identify top processes
top -o cpu
top -o mem

# Kill runaway agent (if needed)
pkill -f "openclaw"
```

### Disk space low
```bash
# Find large files
du -sh ~/.openclaw/logs/*
du -sh ~/.aiempire-backups/*

# Delete old logs (>90 days)
find ~/.openclaw/logs -type f -mtime +90 -delete

# Delete old backups (if retention policy not working)
find ~/.aiempire-backups/hourly -type f -mtime +3 -delete
```

---

## Future Enhancements (Optional)

### Prometheus + Grafana (If Metrics Volume Grows)
- Prometheus scrapes `/metrics` endpoints
- Grafana dashboards for visualization
- AlertManager for advanced alerting

### Distributed Tracing (If Multi-Node)
- OpenTelemetry for request tracing
- Jaeger or Zipkin for visualization

### Log Aggregation (If Scale Increases)
- Loki for centralized log storage
- Grafana Loki queries for log analysis

**For now, PostgreSQL + simple scripts are sufficient for 1-Mac operation.**

---

**Last Updated:** 2026-02-10
**Owner:** Maurice Pfeifer
**Status:** Production-ready
