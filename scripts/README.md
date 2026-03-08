# AIEmpire-Core Service Management Scripts

Comprehensive service startup and shutdown scripts for the AIEmpire-Core project on macOS with Homebrew.

## Quick Start

```bash
# Start all services
./scripts/start_all_services.sh

# Check status anytime
./scripts/check_status.sh

# Stop all services gracefully
./scripts/stop_all_services.sh
```

## Scripts Overview

### `start_all_services.sh`
**Comprehensive service startup in correct dependency order**

**Features:**
- Checks all services before starting
- Starts services in 4 layers of dependencies:
  1. **Infrastructure Layer**: Redis, PostgreSQL
  2. **Container Layer**: Docker
  3. **AI & Automation Layer**: Ollama, n8n
  4. **Application Layer**: CRM, Atomic Reactor
- Color-coded output for easy monitoring
- Detects running services (prevents duplicate starts)
- Final status report shows what's UP/DOWN
- Works seamlessly on macOS with Homebrew

**Services Managed:**
- Ollama (port 11434) - LLM inference
- Redis (port 6379) - Caching & sessions
- PostgreSQL (port 5432) - Primary database
- Docker (port 2375) - Container runtime
- n8n (port 5678) - Automation workflows
- OpenClaw (port 18789) - Status monitoring only
- CRM (port 3500) - Node.js/Express application
- Atomic Reactor (port 8888) - FastAPI service

### `check_status.sh`
**Quick service status monitor**

**Features:**
- Shows all 8 services with UP/DOWN indicators
- Displays port numbers and access URLs
- Shows summary of running services
- Color-coded output (green=UP, red=DOWN)
- Can be used with `watch` for live monitoring

**Usage:**
```bash
# Single check
./scripts/check_status.sh

# Live monitoring (refreshes every 2 seconds)
watch -n 2 ./scripts/check_status.sh
```

### `stop_all_services.sh`
**Graceful service shutdown in reverse dependency order**

**Features:**
- Shuts down services in reverse order of startup
- Application Layer → AI Layer → Container Layer → Infrastructure Layer
- Graceful termination with fallback to force kill if needed
- Supports both brew services and manual process cleanup
- Detailed status output during shutdown

## Service Dependencies

```
Infrastructure (must start first)
├── Redis
└── PostgreSQL

Container & Orchestration
└── Docker

AI & Automation
├── Ollama
└── n8n

Application (startup last)
├── CRM (Node.js/Express)
└── Atomic Reactor (FastAPI)
```

## Installation Requirements

### Homebrew Services
```bash
# Required packages
brew install redis postgresql@16 ollama

# Optional
brew install n8n
brew install docker  # or Docker Desktop
```

### Project Structure
```
AIEmpire-Core/
├── scripts/
│   ├── start_all_services.sh
│   ├── check_status.sh
│   ├── stop_all_services.sh
│   └── README.md
├── crm/
│   └── package.json (Node.js/Express app)
├── atomic-reactor/
│   ├── main.py
│   └── requirements.txt
└── ...
```

## Port Reference

| Service | Port | Type | Status |
|---------|------|------|--------|
| Ollama | 11434 | API | Auto-start |
| Redis | 6379 | Cache | Auto-start |
| PostgreSQL | 5432 | Database | Auto-start |
| Docker | 2375 | Container | Auto-start |
| n8n | 5678 | Automation | Optional |
| OpenClaw | 18789 | Monitoring | Manual |
| CRM | 3500 | Application | Auto-start |
| Atomic Reactor | 8888 | FastAPI | Auto-start |

## Troubleshooting

### Service won't start
1. Check if already running: `./scripts/check_status.sh`
2. Check logs: `brew services info [service-name]`
3. Verify Homebrew installation: `brew info [package-name]`

### Port already in use
```bash
# Find what's using a port
lsof -i :[port-number]

# Kill process using that port
kill -9 [pid]
```

### Services not starting on reboot
Add to your shell startup file (~/.zshrc or ~/.bash_profile):
```bash
# Start AIEmpire services on login
~/projects/AIEmpire-Core/scripts/start_all_services.sh &
```

## Manual Service Commands

```bash
# Redis
brew services start/stop/restart redis
redis-cli ping

# PostgreSQL
brew services start/stop/restart postgresql@16
psql -U postgres

# Ollama
ollama serve
ollama list

# Docker
open -a Docker
docker ps

# n8n (if installed)
n8n start

# CRM (from crm directory)
npm start

# Atomic Reactor (from atomic-reactor directory)
python3 -m uvicorn main:app --port 8888
```

## Log Files

Services typically log to:
- Redis: `~/Library/Logs/redis.log`
- PostgreSQL: `~/Library/Logs/postgresql.log`
- Docker: Check Docker Desktop preferences
- Ollama: Check terminal output or `/var/log/ollama`

## Tips & Best Practices

1. **Always start services with the startup script** - maintains correct order and dependencies
2. **Check status regularly** - use the status checker to verify everything is running
3. **Graceful shutdown** - always use the stop script rather than force-killing processes
4. **Morning startup** - run `./scripts/start_all_services.sh` each day
5. **Live monitoring** - use `watch -n 2 ./scripts/check_status.sh` while developing

---

**Last Updated**: 2026-02-09
**macOS Compatibility**: M-series Macs (M1, M2, M3, M4)
**Architecture**: arm64 (native) or x86_64 (via Rosetta)
