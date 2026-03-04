# AIEmpire-Core - Project Context

## Owner
Maurice Pfeifer, 37, Elektrotechnikmeister, 16 Jahre BMA-Expertise (Brandmeldeanlagen).
Ziel: 100 Mio EUR in 1-3 Jahren, alles automatisiert mit AI.

## Architecture Overview
```
CONTROL:     Claude Code + GitHub (Squash Merge Only)
ENGINE:      empire_engine.py v2.0 (Unified Revenue Machine)
ANTIGRAVITY: 33 Python Module (Router, Cross-Verify, Knowledge, Planning, Sync, Swarm, Cloud)
BRIDGE:      antigravity/empire_bridge.py (verbindet ALLES)
AGENTS:      OpenClaw (Port 18789, 9 Cron Jobs) + Godmode (4 Ollama Roles)
MODELS:      Ollama (95% free) -> Kimi K2.5 (4%) -> Claude (1%)
DATA:        Redis + PostgreSQL + ChromaDB + SQLite (CRM)
TASKS:       Atomic Reactor (FastAPI, Port 8888)
API:         Empire API (FastAPI, Port 3333)
SWARM:       Kimi 100K-500K Agents
SALES:       X/Twitter Lead Machine + CRM (Port 3500)
REVENUE:     Gumroad + Fiverr + Consulting + Community
MONITOR:     Prometheus + Grafana + Loki (docker-compose.prod.yml)
PROTECTION:  Resource Guard v2 + Auto-Repair + Bombproof Startup
MOBILE:      PWA Command Center (GitHub Pages)
MIRROR:      Dual-Brain (Mac + Gemini Cloud)
N8N:         9 Automated Workflows (Port 5678)
BRAINS:      7+1 Neuroscience-based AI Agents
```

## Quick Start
```bash
# Dashboard anzeigen (Status + Revenue + Quick Wins)
python3 empire_engine.py

# System reparieren (offline, mit Ollama)
python3 scripts/auto_repair.py

# Bombproof Startup (nach Crash/Reboot)
./scripts/bombproof_startup.sh

# Setup (installiert alle Open-Source Tools)
./scripts/setup_optimal_dev.sh

# Alle Services starten (Redis -> PostgreSQL -> Ollama -> Docker -> n8n -> CRM -> Reactor)
./scripts/start_all_services.sh

# Service Status pruefen
./scripts/check_status.sh
```

## Tech Stack
- **Language:** Python 3.10+ (asyncio/aiohttp)
- **Web Frameworks:** FastAPI + Uvicorn (Python), Express.js (CRM)
- **Linting:** ruff (line-length=120, rules: E/F/W/I, ignore: E501/E402)
- **Testing:** pytest + pytest-asyncio (test paths: antigravity/, systems/, kimi-swarm/)
- **Formatting:** ruff format (double quotes)
- **Dependencies:** requirements.txt (production), requirements-dev.txt (dev tools)

## Key Directories

### Core Systems
- `empire_engine.py` - **UNIFIED ENTRY POINT** v2.0 (Dashboard + Revenue Machine + Auto-Cycle)
- `antigravity/` - 33 Python Module: Router, Agents, Cross-Verify, Knowledge, Planning, Sync, Bridge, Swarm, Cloud
- `antigravity/empire_bridge.py` - **GLUE** (verbindet alle Systeme durch Antigravity)
- `antigravity/config.py` - Central config mit auto .env loading (NIEMALS os.getenv direkt!)
- `antigravity/unified_router.py` - Multi-Provider Routing (Gemini -> Ollama -> Moonshot)
- `antigravity/cross_verify.py` - Agents verify each other (frischer Kontext, nie Selbstbewertung)
- `antigravity/knowledge_store.py` - Persistentes Wissen (JSONL, crash-safe, cross-session)
- `antigravity/planning_mode.py` - RESEARCH -> PLAN -> APPROVE -> EXECUTE -> VERIFY
- `antigravity/sync_engine.py` - Atomic Writes + Crash Recovery + Journaling
- `antigravity/agent_swarm.py` - 100+ parallel agents (8 roles: Architect, Coder, Analyst, Reviewer, etc.)
- `antigravity/cloud_backend.py` - Zero local memory (Google Drive + iCloud + LocalStorage)
- `antigravity/autonomous_daemon.py` - 24/7 continuous operation without human input
- `antigravity/resource_aware.py` - Adaptive model selection based on RAM/CPU
- `antigravity/system_guardian.py` - Prevents Mac from becoming unstable (LaunchAgent)
- `antigravity/context_continuity.py` - Claude context limit -> Ollama fallback
- `antigravity/state_recovery.py` - Crash-resistant checkpointing with atomic writes

### Workflow + Automation
- `workflow_system/` - Opus 4.6 5-Step Compound Loop
- `workflow_system/cowork.py` - Autonomous Cowork Engine (Observe-Plan-Act-Reflect daemon)
- `workflow_system/resource_guard.py` - Resource Guard v2 (Crash-Proof, Predictive, Preemptive)
- `workflow_system/empire.py` - Legacy CLI (use empire_engine.py instead)

### Revenue Generation
- `revenue_machine/` - Unified Revenue Pipeline (RevenuePipeline, NewsScanner, ContentFactory, MultiPlatformPublisher, AdManager, SelfOptimizer)
- `x_lead_machine/` - X/Twitter automation (post generation, viral replies, lead detection, buyer signals)
- `kimi_swarm/` - 100K/500K Kimi agent swarm mit Claude orchestration
- `atomic_reactor/` - YAML-basierte Task Definitions + FastAPI async runner (Port 8888)
- `crm/` - Express.js CRM mit BANT scoring + Socket.io (Port 3500)
- `BMA_ACADEMY/` - BMA Knowledge Fortress (DIN 14675 compliance, expert checklisten)
- `products/` - 4 Digitale Produkte (AI Setup Blueprint, Automated Cashflow, Viral Velocity, BMA Checklisten Pack)

### Intelligence
- `brain_system/` - 7+1 Neuroscience-based AI Brains (Brainstem, Neocortex, Prefrontal, Temporal, Parietal, Limbic, Cerebellum, Hippocampus)
- `gemini-mirror/` - Dual-Brain Amplification Loop (Kimi + Gemini parallel, cross-validation)
- `gold-nuggets/` - 15 Business Intelligence Dokumente (126KB)
- `warroom/` - Multi-Squad Operations Center (Legal, Data, Marketing, Sales, Research, Ops/Engineering)

### Infrastructure
- `empire_api/` - Central REST API + WebSocket (FastAPI, Port 3333, iPhone/iPad access)
- `godmode/` - 4-Role Local AI Programmer (Architect, Coder, Fixer, QA via Ollama)
- `mirror-system/` - Mac <-> Gemini Cloud sync (export/import/merge gate/product factory)
- `openclaw-config/` - OpenClaw Agents, 9 Cron Jobs, Model Routing, Persistent Memory
- `mobile-command-center/` - React PWA Dashboard (Recharts, Service Worker, deployed to GitHub Pages)
- `n8n-workflows/` - 9 n8n Workflows (content engine, health, sync, leads, Ollama brain, GitHub monitor)
- `scripts/` - 15+ Scripts (start/stop services, auto-repair, bombproof startup, setup, status check)
- `systems/` - Docker Compose, Scripts, Lead Agent Prompts
- `config/` - Centralized env_config.py (get_api_key, get_config, validate_env)
- `system-prompts/` - Cognitive role definitions for agents
- `docs/` - 35+ Strategic Documents (335KB: Vision, Architecture, Security, Revenue Guides, KPI tracking)

## Empire Engine CLI (Hauptprogramm)
```bash
python3 empire_engine.py              # Status Dashboard
python3 empire_engine.py scan         # News + Trends scannen
python3 empire_engine.py produce      # Content generieren
python3 empire_engine.py distribute   # Multi-Platform posten
python3 empire_engine.py leads        # Leads verarbeiten
python3 empire_engine.py revenue      # Revenue Report
python3 empire_engine.py auto         # Voller autonomer Zyklus
python3 empire_engine.py godmode [task]  # 4-Role AI Router
python3 empire_engine.py mirror       # Mirror System aktivieren
python3 empire_engine.py repair       # Auto-Repair ausfuehren
python3 empire_engine.py setup        # Dev-Umgebung einrichten
```

## Empire Bridge (Integration Layer)
```python
from antigravity.empire_bridge import get_bridge

bridge = get_bridge()

# Jeder AI-Call geht durch den Router (nie direkte API Calls!)
result = await bridge.execute("Generiere viralen Post ueber AI Agents")

# Kritische Tasks mit Cross-Verification
result = await bridge.execute_verified("Schreibe CRM Sync Funktion")

# Wissen speichern (persistiert zwischen Sessions)
bridge.learn("fix", "Port Conflict", "CRM braucht Port 3500 frei")

# Systemstatus
status = bridge.system_status()
```

## Coding Standards
- Python 3.10+ mit asyncio/aiohttp fuer alle async I/O
- Line length: 120 characters (ruff enforced)
- Quote style: double quotes
- JSON Output von allen AI Agents (strukturiert, parseable)
- Cost Tracking auf jedem API Call
- Model Routing: Ollama first (95%), Kimi fuer komplex (4%), Claude fuer kritisch (1%)
- Max 100 EUR/Monat API Budget
- ALLE API Keys in .env (NIEMALS hardcoden!)
- Config IMMER durch `antigravity/config.py` importieren (NIEMALS `os.getenv` direkt!)
- Atomic Writes fuer alle kritischen State-Dateien (write to .tmp, then rename)
- Cross-Verification fuer alle kritischen Outputs
- German comments/docs allowed (bilingual codebase)
- Pragmatic code over perfection

## Git & PR Workflow
- **Merge Strategy:** Squash merge ONLY (rebase and merge disabled)
- **PR Requirements:** Every change via PR, describe scope/risk, reference issues
- **Reviewers:** At least 1 approval for non-trivial changes
- **Branch Hygiene:** Delete after merge, keep PRs small, close stale drafts
- **CODEOWNERS:** @mauricepfeifer-ctrl owns entire repo
- **Secret Scanning:** gitleaks v8.24.2 on every PR/push + weekly full-history scan

## CI/CD Workflows (GitHub Actions)
| Workflow | Schedule | Purpose |
|----------|----------|---------|
| Auto Content Generation | Every 4h | X/Twitter content via KimiAPI |
| 24/7 Content Engine | 4x daily (06/10/16/22 UTC) | Full content + leads + KPI cycle |
| Revenue Tracking | Daily 09:00 UTC | Revenue report across all channels |
| Mission Control Scan | Daily 09:00 UTC | System diagnostics + dashboard |
| Claude Health Check | Every 30 min | API monitoring + failover |
| X Auto Poster | Daily 07:00 UTC | Content generation + posting guide |
| Secret Scan | Weekly + PR/push | gitleaks security scanning |
| Issue Command Bot | On issue events | @bot commands (status, generate, revenue) |
| Deploy Mobile | On push to mobile-command-center/ | PWA to GitHub Pages |

## Docker Deployment
```bash
# CRM Development (Port 3000 + 9229 debug)
docker compose -f compose.debug.yaml up

# CRM Production (Port 3000)
docker compose up

# Full Production Stack (Traefik + Prometheus + Grafana + Loki)
docker compose -f docker-compose.prod.yml up
```

## Service Ports
| Service | Port | Protocol |
|---------|------|----------|
| CRM | 3500 | HTTP + WebSocket |
| Empire API | 3333 | HTTP + WebSocket |
| Atomic Reactor | 8888 | HTTP (FastAPI) |
| OpenClaw | 18789 | HTTP |
| Ollama | 11434 | HTTP |
| n8n | 5678 | HTTP |
| Grafana | 3000 | HTTP |
| Prometheus | 9090 | HTTP |
| Traefik Dashboard | 8081 | HTTP |
| Loki | 3100 | HTTP |

## Resource Guard v2 Thresholds
```
CPU > 95% oder RAM > 92% -> EMERGENCY (Ollama Models gestoppt)
CPU > 85% oder RAM > 85% -> CRITICAL (Concurrency: 50)
CPU > 70% oder RAM > 75% -> WARN (Concurrency: 200)
Trend steigend + >60%    -> PREDICTIVE WARN
```

## Bombproof Startup (Crash-Schutz)
```bash
# Startup-Reihenfolge (automatisch):
# 1. auto_repair.py (fixt .env, gcloud, korrupte Dateien, startet Ollama)
# 2. resource_guard.py startup_check (Crash Detection -> Safe Mode)
# 3. Core Services (Ollama, Redis, PostgreSQL)
# 4. App Services (CRM, Atomic Reactor, OpenClaw)
# 5. Health Verification

# Manuell reparieren
python3 scripts/auto_repair.py
./scripts/bombproof_startup.sh --repair
```

## Knowledge Store (Persistentes Wissen)
```python
from antigravity.knowledge_store import KnowledgeStore
ks = KnowledgeStore()

# 7 KI types: fix, decision, pattern, learning, error, optimization, architecture
ks.add("fix", "gemini env var crash",
       content="NIEMALS os.getenv direkt, immer config.py importieren",
       tags=["bugfix", "critical"])

results = ks.search("gemini config")   # Text-Suche
results = ks.search_by_tag("bugfix")   # Tag-Suche
context = ks.export_for_agent("crash") # Fuer Agent-Prompts
```

## Planning Mode (Google Antigravity Pattern)
```python
from antigravity.planning_mode import PlanningController, PlannedChange, ChangeType

ctrl = PlanningController()
plan = ctrl.create_plan("task-001", "Feature X", "Implement feature X")
plan.add_change(PlannedChange("file.py", ChangeType.MODIFY, "Add handler"))
ctrl.advance_to_plan(plan)
plan.approve("claude")
ctrl.advance_to_execute(plan)
# ... execute ...
ctrl.advance_to_verify(plan)
ctrl.complete(plan)
```

## Revenue Channels (Priority Order)
1. Gumroad digital products (27-149 EUR) -- BMA Checklisten, AI Kits, Courses
2. Fiverr/Upwork AI services (30-5000 EUR)
3. BMA + AI consulting (2000-10000 EUR) -- UNIQUE NICHE (nur Maurice weltweit!)
4. Premium Community "Agent Builders Club" (29 EUR/Monat)
5. X/Twitter content + lead generation (3 Personas, 9 Posts/Tag)
6. OpenClaw Skills marketplace
7. TikTok 3-persona pipeline (faceless video content)

## System Inventory (20 Systeme)
| System | Module | Status | Size |
|--------|--------|--------|------|
| Antigravity | 33 Python Module | PRODUCTION | 54 files |
| Workflow System | orchestrator, cowork, empire | PRODUCTION | 7 files |
| Empire Engine | empire_engine.py v2.0 | PRODUCTION | 22KB |
| Revenue Machine | Pipeline + Scanner + Factory | PRODUCTION | 33KB |
| Empire API | FastAPI Server (Port 3333) | PRODUCTION | 25KB |
| Godmode | 4-Role Ollama Programmer | PRODUCTION | 41KB |
| Kimi Swarm | 100K + 500K agents | READY | 223KB |
| X Lead Machine | content + leads + viral replies | READY | 98KB |
| Atomic Reactor | YAML tasks + FastAPI runner | PRODUCTION | 31KB |
| CRM | Express.js + SQLite + Socket.io | PRODUCTION | 58KB |
| Brain System | 7+1 AI Brains | PRODUCTION | 38KB |
| Gemini Mirror | Dual-Brain (Kimi+Gemini) | PRODUCTION | 148KB |
| Mirror System | Mac <-> Gemini Cloud Sync | PRODUCTION | 20+ files |
| BMA Academy | Knowledge Fortress | PRODUCT READY | 14KB |
| Products | 4 Digital Products (23 modules) | PRODUCT READY | 275KB |
| OpenClaw Config | Agents + 9 Cron + Models + Memory | PRODUCTION | 50KB |
| Gold Nuggets | 15 Business Intel Docs | COMPLETE | 126KB |
| Warroom | 6 Squads, 14 Rules, Mission Control | PRODUCTION | 10+ files |
| Mobile Command Center | React PWA Dashboard | PRODUCTION | 6 files |
| n8n Workflows | 9 Automated Workflows | READY | 12+ files |
| Auto-Repair | Self-healing + Ollama AI | PRODUCTION | 16KB |
| Bombproof Startup | LaunchAgent + 5 Phases | PRODUCTION | 14KB |
| Docs | 35+ Strategic Documents | COMPLETE | 335KB |

## Hardware Constraints
- Apple M4, 16GB RAM
- Must not interfere with day job (Roewer GmbH)
- Ollama models limited by RAM (Resource Guard manages this)
- Anonymous personas (no face, no real name on content)

## Key Integration Patterns
1. **All AI calls** go through `antigravity/unified_router.py` (never direct API calls)
2. **All config** through `antigravity/config.py` (never `os.getenv`)
3. **Critical outputs** get cross-verified via `antigravity/cross_verify.py`
4. **All learning** stored in `antigravity/knowledge_store.py`
5. **All state changes** are crash-safe (atomic writes via `antigravity/sync_engine.py`)
6. **Empire Bridge** lazy-loads all subsystems (router, verifier, knowledge, sync, planner, guard)
7. **Cloud proposes, Mac decides** (mirror-system golden rule)
