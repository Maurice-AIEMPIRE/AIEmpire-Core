# AI EMPIRE ARCHITECTURE

**Last Updated**: 2026-02-10
**Owner**: Maurice Pfeifer (CEO) + CLAUDE (Chief Architect)
**Status**: V1 FINAL

## SYSTEM OVERVIEW

```
EXTERNAL: CLI, Mobile, Telegram, Webhooks
CONTROL: Orchestrator (brain_system/orchestrator.py) + Mission Control
LLM ROUTING: Ollama (free) -> Kimi K2.5 (budget) -> Claude (critical)
AGENTS: Brain System (7 agents) + Kimi Swarm (100K-500K) + X Lead Machine
DATA: PostgreSQL 15 + Redis 7 + ChromaDB + SQLite
ORCHESTRATION: Atomic Reactor (YAML) + n8n (8 workflows)
BUSINESS: Content Engine + Sales Engine + BMA System
API: Empire API (FastAPI:3333) + CRM API (Express:3500)
OPS: Docker Compose + GitHub Actions (11 workflows) + Monitoring
```

## MODULE BREAKDOWN

### 1. ORCHESTRATOR
- orchestrator.py: Routes tasks to agents
- 7 brain agents: Neocortex, CEO, Mouth, Numbers, Drive, Hands, Memory

### 2. LLM ROUTING
- Simple -> OLLAMA (free)
- Complex -> KIMI (cheap)
- Strategic -> CLAUDE (best)
- Over budget -> QUEUE

### 3. AGENT SWARM
- Brain System: 7 specialized agents
- Kimi Swarm: 100K-500K parallel agents
- X Lead Machine: Twitter automation + leads

### 4. DATA LAYER
| DB | Port | Purpose |
|----|------|---------|
| PostgreSQL 15 | 5432 | Users, state, n8n |
| Redis 7 | 6379 | Cache, rate limits |
| ChromaDB | 8000 | Vectors, search |
| SQLite | local | CRM leads |

### 5. API LAYER
- Empire API (FastAPI:3333): /health, /api/action, WebSocket
- CRM API (Express:3500): /leads CRUD + BANT scoring

### 6. DEPLOYMENT
- Docker Compose: All services with health checks
- GitHub Actions: 11 workflows
- Monitoring: Prometheus + Grafana + Loki

## PERFORMANCE TARGETS
| Metric | 90-Day | 12-Month |
|--------|--------|----------|
| API latency | <100ms | <50ms |
| Uptime | 99.90% | 99.95% |
| Cost/task | EUR 0.05-0.50 | EUR 0.02-0.20 |
