# AIEmpire-Core Startup Guide

## Overview

AIEmpire-Core requires multiple services to run in a specific order. This guide explains the three startup/shutdown scripts and how to use them.

## The Three Scripts

### 1. `scripts/start_all_services.sh` - Daily Startup
**Use this to start everything in the morning**

```bash
cd /sessions/pensive-intelligent-hypatia/mnt/AIEmpire-Core
./scripts/start_all_services.sh
```

**What it does:**
- ✅ Checks if services are already running (prevents duplicates)
- ✅ Starts services in correct dependency order
- ✅ Waits for each service before starting the next
- ✅ Provides color-coded status output
- ✅ Shows final report of all 8 services

**Startup Order (Layers):**
1. Redis + PostgreSQL (database layer)
2. Docker (container runtime)
3. Ollama + n8n (AI & automation)
4. CRM + Atomic Reactor (applications)

---

### 2. `scripts/check_status.sh` - Anytime Status Check
**Use this to verify everything is running**

```bash
./scripts/check_status.sh
```

**Output Example:**
```
📊 AIEmpire-Core Service Status Monitor
      2026-02-09 14:23:45

Ollama                    ✅ UP (Port 11434)  → http://localhost:11434
Redis                     ✅ UP (Port 6379)   → redis-cli
PostgreSQL                ✅ UP (Port 5432)   → psql
Docker                    ✅ UP (Port 2375)   → docker ps
n8n                       ❌ DOWN (Port 5678)
OpenClaw                  ❌ DOWN (Port 18789)
CRM                       ✅ UP (Port 3500)   → http://localhost:3500
Atomic Reactor            ✅ UP (Port 8888)   → http://localhost:8888

Summary: 6/8 services running
```

**Live Monitoring (auto-refresh every 2 seconds):**
```bash
watch -n 2 ./scripts/check_status.sh
```

---

### 3. `scripts/stop_all_services.sh` - Graceful Shutdown
**Use this when you're done for the day**

```bash
./scripts/stop_all_services.sh
```

**What it does:**
- ✅ Stops services in reverse order (applications first, infrastructure last)
- ✅ Gracefully terminates processes
- ✅ Force-kills if graceful termination fails
- ✅ Provides feedback on each service

---

## Daily Workflow

### Morning: Start Everything
```bash
cd ~/AIEmpire-Core
./scripts/start_all_services.sh
# Wait 30-60 seconds for all services to fully start
./scripts/check_status.sh
```

### During Work: Monitor Status
```bash
# Quick check
./scripts/check_status.sh

# Live dashboard (press Ctrl+C to exit)
watch -n 2 ./scripts/check_status.sh
```

### When Leaving: Clean Shutdown
```bash
./scripts/stop_all_services.sh
```

---

## Service Quick Reference

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Ollama** | 11434 | LLM inference engine | Auto-start ✅ |
| **Redis** | 6379 | Session cache & temporary data | Auto-start ✅ |
| **PostgreSQL** | 5432 | Main application database | Auto-start ✅ |
| **Docker** | 2375 | Container runtime | Auto-start ✅ |
| **n8n** | 5678 | Workflow automation | Optional ⚠️ |
| **OpenClaw** | 18789 | Status monitoring | Manual ⚠️ |
| **CRM** | 3500 | Main Express.js application | Auto-start ✅ |
| **Atomic Reactor** | 8888 | FastAPI backend service | Auto-start ✅ |

---

## Accessing Services

### Web Applications
- **CRM Dashboard**: http://localhost:3500
- **Atomic Reactor API**: http://localhost:8888
- **n8n Workflows** (if running): http://localhost:5678
- **OpenClaw** (if running): http://localhost:18789

### Command Line Tools
```bash
# Check Redis
redis-cli ping

# Connect to PostgreSQL
psql -U postgres

# List Ollama models
ollama list

# Docker info
docker ps

# Monitor Atomic Reactor logs
# (check terminal where script was started)
```

---

## Troubleshooting

### A service shows DOWN but should be UP

**Option 1: Check if something else is using the port**
```bash
lsof -i :3500  # Replace 3500 with the port number
```

**Option 2: Check service logs**
```bash
brew services info postgresql@16
brew services info redis
```

**Option 3: Try restarting the service**
```bash
# Stop all services
./scripts/stop_all_services.sh

# Start all services
./scripts/start_all_services.sh
```

### All services are DOWN

1. Check if Docker Desktop is running (needed for Docker service)
2. Verify Homebrew packages: `brew services list`
3. Check if Ollama app is running (may need to open it manually)
4. Try: `./scripts/stop_all_services.sh && sleep 5 && ./scripts/start_all_services.sh`

### Services won't stop

```bash
# Force kill by port number
lsof -ti :3500 | xargs kill -9  # Replace 3500 with port

# Then restart
./scripts/start_all_services.sh
```

---

## Auto-Start on Mac Boot

Edit your shell startup file (`~/.zshrc` or `~/.bash_profile`):

```bash
# AIEmpire-Core Auto-Start
if [ -x "$HOME/AIEmpire-Core/scripts/start_all_services.sh" ]; then
    echo "Starting AIEmpire-Core services..."
    $HOME/AIEmpire-Core/scripts/start_all_services.sh &
fi
```

---

## Manual Service Commands (if needed)

### Redis
```bash
brew services start redis
brew services stop redis
redis-cli shutdown
```

### PostgreSQL
```bash
brew services start postgresql@16
brew services stop postgresql@16
```

### Ollama
```bash
ollama serve              # Start server
pkill ollama             # Stop server
```

### Docker
```bash
open -a Docker           # Start Docker Desktop
pkill Docker            # Stop Docker Desktop
```

### n8n (if installed)
```bash
n8n start
pkill n8n
```

### CRM (Node.js)
```bash
cd crm
npm start
# Press Ctrl+C to stop
```

### Atomic Reactor (FastAPI)
```bash
cd atomic-reactor
python3 -m uvicorn main:app --port 8888
# Press Ctrl+C to stop
```

---

## Performance Tips

1. **Don't run unnecessary services** - Disable n8n if not needed
2. **Monitor memory** - Use Activity Monitor if services seem slow
3. **Check Docker** - Docker Desktop can be heavy on resources
4. **Redis optimization** - Redis is lightweight, not usually an issue
5. **PostgreSQL maintenance** - Periodically run VACUUM to optimize

---

## Getting Help

**Check the detailed README:**
```bash
cat ./scripts/README.md
```

**View this guide again:**
```bash
cat STARTUP_GUIDE.md
```

**For specific service issues:**
- Ollama: Check `ollama --help` or https://ollama.ai
- PostgreSQL: Check `psql --help` or PostgreSQL docs
- Node.js/CRM: Check `npm --help` or project README
- FastAPI: Check FastAPI documentation

---

**Created**: 2026-02-09
**Platform**: macOS (M1/M2/M3/M4 with Homebrew)
**Tested on**: Mac Mini M4
