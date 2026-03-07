# GALAXIA Phase 1B: Infrastructure Deployment

**Goal:** Distributed infrastructure with Hetzner runners, database replication, and 24/7 availability

## Quick Start

```bash
# Setup Tailscale environment variable
export TAILSCALE_AUTH_KEY="tskey-..."  # Get from https://login.tailscale.com/admin/settings/keys

# Run the complete Phase 1B deployment
bash ops/phase_1b_deploy.sh
```

**Estimated Duration:** 1-2 hours (includes Ollama model downloads)

---

## Architecture

```
Internet
│
├─ Mac mini (Controller)
│  ├─ Ollama (qwen2.5-coder:14b)
│  ├─ Telegram Bot
│  └─ Task Router
│
└─ Hetzner Cloud (Mesh VPN via Tailscale)
   │
   ├─ Hetzner-1 (Primary, IP: 65.21.203.174)
   │  ├─ PostgreSQL (primary)
   │  ├─ Redis (primary)
   │  ├─ Ollama (backup model)
   │  └─ ChromaDB
   │
   └─ Hetzner-2 (Standby, IP: 65.21.203.175)
      ├─ PostgreSQL (replica)
      ├─ Redis (replica)
      ├─ Ollama (backup model)
      └─ ChromaDB
```

**Network:** WireGuard encrypted mesh VPN via Tailscale

---

## Scripts Included

### 1️⃣ Network Foundation
**File:** `ops/network/tailscale_setup.sh`

Sets up secure peer-to-peer network:
- Tailscale installation & authentication
- SSH key generation & distribution
- SSH config for all runners
- VPN mesh creation

**Run:** Automatically via `phase_1b_deploy.sh`

```bash
# Manual run:
export TAILSCALE_AUTH_KEY="tskey-..."
bash ops/network/tailscale_setup.sh
```

### 2️⃣ Hetzner Provisioning
**File:** `ops/hetzner/provision_runner.sh`

Provisions complete runner environments:
- Docker & Docker Compose
- Ollama with qwen2.5-coder models
- Redis
- PostgreSQL (primary only)
- ChromaDB
- Health monitoring
- Automated cron jobs

**Run:** Automatically via `phase_1b_deploy.sh` (twice for primary + standby)

```bash
# Manual run:
bash ops/hetzner/provision_runner.sh primary 65.21.203.174
bash ops/hetzner/provision_runner.sh standby 65.21.203.175
```

### 3️⃣ Database Replication
**File:** `ops/database/replication_setup.sh`

Sets up high-availability databases:
- PostgreSQL streaming replication
- WAL archiving for PITR
- Redis replication
- Automated daily backups
- Backup verification

**Run:** Automatically via `phase_1b_deploy.sh`

```bash
# Manual run:
bash ops/database/replication_setup.sh
```

### 4️⃣ Master Orchestration
**File:** `ops/phase_1b_deploy.sh`

Coordinates all Phase 1B steps:
1. Network Foundation (Tailscale)
2. Hetzner Primary provisioning
3. Hetzner Standby provisioning
4. Database replication
5. Verification & testing

```bash
bash ops/phase_1b_deploy.sh
```

---

## Configuration

### Environment Variables

```bash
# Required for Tailscale
export TAILSCALE_AUTH_KEY="tskey-..."

# Optional (auto-detected from .env)
export REPO_ROOT="/path/to/AIEmpire-Core"
export HETZNER_PRIMARY="65.21.203.174"
export HETZNER_STANDBY="65.21.203.175"
```

### SSH Configuration

After running scripts, SSH config is automatically created at `~/.ssh/config`:

```bash
# Direct SSH (via public IP)
ssh hetzner-1          # → root@65.21.203.174
ssh hetzner-2          # → root@65.21.203.175

# Via Tailscale VPN (more secure)
ssh hetzner-1-ts       # → root@100.64.0.1
ssh hetzner-2-ts       # → root@100.64.0.2
```

---

## Verification

### Check Network
```bash
# Local Tailscale status
tailscale status

# Remote runners
ssh hetzner-1 'tailscale status'
ssh hetzner-2 'tailscale status'
```

### Check Services
```bash
# List running services
ssh hetzner-1 'docker-compose -f /opt/aiempire/compose/docker-compose.yml ps'

# View logs
ssh hetzner-1 'docker-compose -f /opt/aiempire/compose/docker-compose.yml logs -f'
```

### Check PostgreSQL Replication
```bash
# On primary
ssh hetzner-1 'docker exec galaxia-postgres psql -U aiempire -d aiempire_core -c "SELECT client_addr, state FROM pg_stat_replication;"'

# Expected output: Shows standby connection in "streaming" state
```

### Check Redis Replication
```bash
# On primary
ssh hetzner-1 'docker exec galaxia-redis redis-cli info replication'

# Expected output: Shows role=master with connected_slaves=1
```

### Check Ollama Models
```bash
# List available models
ssh hetzner-1 'docker exec galaxia-ollama ollama list'

# Test model inference
ssh hetzner-1 'docker exec galaxia-ollama ollama run qwen2.5-coder:7b "test"'
```

---

## Monitoring & Maintenance

### Daily Backup
Automated daily backup runs at 02:00 UTC:

```bash
# View backup log
ssh hetzner-1 'tail -f /var/log/galaxia/backup.log'

# Manual backup
ssh hetzner-1 '/usr/local/bin/galaxia-backup'

# List backups
ssh hetzner-1 'ls -lh /var/backups/galaxia/'
```

### Health Checks
Health checks run every 5 minutes:

```bash
# View latest health report
ssh hetzner-1 'cat /var/lib/galaxia/health.json | jq .'

# Manual health check
ssh hetzner-1 '/usr/local/bin/galaxia-health-check'
```

### Log Aggregation
All logs available in:
- `/var/log/galaxia/` (all services)
- `/var/log/galaxia/health-check.log` (health checks)
- `/var/log/galaxia/backup.log` (backups)

---

## Failover Testing

### Test 1: Primary Failure
```bash
# Simulate primary failure
ssh hetzner-1 'docker-compose -f /opt/aiempire/compose/docker-compose.yml stop'

# Promote standby
ssh hetzner-2 'docker exec galaxia-postgres pg_ctl promote'

# Verify standby is now primary
ssh hetzner-2 'docker exec galaxia-postgres psql -U aiempire -d aiempire_core -c "SELECT pg_is_in_recovery();"'
# Expected: false (recovery complete, now primary)
```

### Test 2: Network Isolation
```bash
# Simulate network failure (on Tailscale)
ssh hetzner-1 'sudo tailscale down'

# Verify standby takes over
ssh hetzner-2 'docker exec galaxia-postgres psql -U aiempire -d aiempire_core -c "SELECT database FROM pg_stat_replication;"'
# Expected: (no rows) - replication stopped
```

### Test 3: Point-in-Time Recovery
```bash
# Show recovery time objective (RTO) and recovery point objective (RPO)
ssh hetzner-1 'ls -lh /var/lib/galaxia/wal-archive/ | tail -5'

# Restore from specific backup
ssh hetzner-1 'pg_restore --list /var/backups/galaxia/backup-2026-03-07-020000.sql.gz | head'
```

---

## Troubleshooting

### Tailscale Not Connecting
```bash
# Check Tailscale status
tailscale status

# Reconnect manually
sudo tailscale down && sudo tailscale up

# If issues persist, check auth key
echo $TAILSCALE_AUTH_KEY
```

### PostgreSQL Replication Stuck
```bash
# Check replication lag
ssh hetzner-1 'docker exec galaxia-postgres psql -U aiempire -d aiempire_core -c "SELECT slot_name, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;"'

# Restart standby if necessary
ssh hetzner-2 'docker restart galaxia-postgres'
```

### Ollama Models Not Downloading
```bash
# Check download progress
ssh hetzner-1 'docker logs galaxia-ollama -f'

# Models are typically 7-14 GB each
# Can take 30-60 minutes depending on network

# Kill stalled download and restart
ssh hetzner-1 'docker exec galaxia-ollama ollama stop'
ssh hetzner-1 'docker restart galaxia-ollama'
```

### Out of Disk Space
```bash
# Check disk usage
ssh hetzner-1 'df -h /var/lib/galaxia/'

# Clean old backups
ssh hetzner-1 'find /var/backups/galaxia -mtime +30 -delete'

# Prune Docker layers
ssh hetzner-1 'docker system prune -f'
```

---

## Operational Procedures

### Graceful Shutdown
```bash
# Drain all jobs and shutdown cleanly
ssh hetzner-1 << 'EOF'
  # Stop accepting new jobs
  touch /opt/aiempire/shutdown

  # Wait for running jobs to complete (max 5 min)
  sleep 300

  # Flush databases
  docker exec galaxia-postgres psql -U aiempire -d aiempire_core -c "CHECKPOINT;"
  docker exec galaxia-redis redis-cli BGSAVE

  # Stop services
  docker-compose -f /opt/aiempire/compose/docker-compose.yml stop
EOF
```

### Restart All Services
```bash
ssh hetzner-1 'docker-compose -f /opt/aiempire/compose/docker-compose.yml restart'
```

### Update Configuration
```bash
# Edit config on primary
ssh hetzner-1 'nano /etc/aiempire/config.yaml'

# Reload services
ssh hetzner-1 'docker-compose -f /opt/aiempire/compose/docker-compose.yml reload'
```

---

## Cost Optimization

### Ollama Models Size
```
qwen2.5-coder:7b   ~ 4.7 GB
qwen2.5-coder:14b  ~ 8.6 GB
deepseek-r1:7b     ~ 4.9 GB
```

**To save disk space:** Delete unused models:
```bash
ssh hetzner-1 'docker exec galaxia-ollama ollama rm deepseek-r1:7b'
```

### Disk Space Usage
Expected per runner:
- Ollama models: 15-20 GB
- PostgreSQL data: 500 MB - 2 GB (initial)
- Redis: 100 MB (in-memory cache)
- Backups: 500 MB - 1 GB daily

**Total:** 16-23 GB initial, grows with database size

---

## Next Steps

After Phase 1B is complete:

1. **Monitor Ollama downloads** (~30-60 min)
   ```bash
   ssh hetzner-1 'docker logs galaxia-ollama -f | grep "pulling'"
   ```

2. **Verify all systems healthy**
   ```bash
   bash ops/phase_1b_deploy.sh  # Re-run verification part
   ```

3. **Test distributed task execution**
   ```bash
   python3 empire_engine.py test-distributed
   ```

4. **Proceed to Phase 2: Revenue Automation**
   - See `docs/GALAXIA_TASK_003_SETUP.md` for next steps
   - Content generation pipeline
   - Lead distribution system
   - Monetization channels

---

## Support

For issues or questions:

1. Check logs: `ssh hetzner-1 'docker-compose -f /opt/aiempire/compose/docker-compose.yml logs'`
2. Check health: `ssh hetzner-1 'cat /var/lib/galaxia/health.json | jq'`
3. Run health check: `ssh hetzner-1 '/usr/local/bin/galaxia-health-check'`
4. Review this guide: Phase 1B README (this file)

---

**Version:** 1.0
**Created:** 2026-03-07
**Phase:** 1B - Infrastructure Foundation
**Status:** Ready for deployment

