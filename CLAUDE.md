# AIEmpire-Core - Project Context

## Owner
Maurice Pfeifer, 37, Elektrotechnikmeister, 16 Jahre BMA-Expertise (Brandmeldeanlagen).
Ziel: 100 Mio EUR in 1-3 Jahren, alles automatisiert mit AI.

## Architecture
```
CONTROL:     Claude Code + GitHub
ENGINE:      empire_engine.py (Unified Revenue Machine)
ANTIGRAVITY: 26 Module (Router, Cross-Verify, Knowledge, Planning, Sync)
BRIDGE:      antigravity/empire_bridge.py (verbindet ALLES)
AGENTS:      OpenClaw (Port 18789, 9 Cron Jobs)
MODELS:      Ollama (95% free) → Kimi K2.5 (4%) → Claude (1%)
DATA:        Redis + PostgreSQL + ChromaDB
TASKS:       Atomic Reactor (FastAPI, Port 8888)
SWARM:       Kimi 50K-500K Agents
SALES:       X/Twitter Lead Machine + CRM (Port 3500)
REVENUE:     Gumroad + Fiverr + Consulting + Community
PROTECTION:  Resource Guard v2 + Auto-Repair + Bombproof Startup
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
```

## Key Directories

### Core Systems
- `empire_engine.py` - **UNIFIED ENTRY POINT** (Dashboard + Revenue Machine + Auto-Cycle)
- `antigravity/` - 26 Module: Router, Agents, Cross-Verify, Knowledge, Planning, Sync, Bridge
- `antigravity/empire_bridge.py` - **GLUE** (verbindet alle Systeme durch Antigravity)
- `antigravity/config.py` - Central config mit auto .env loading (NIEMALS os.getenv direkt!)
- `antigravity/unified_router.py` - Multi-Provider Routing (Ollama → Kimi → Claude)
- `antigravity/cross_verify.py` - Agents verify each other (frischer Kontext, nie Selbstbewertung)
- `antigravity/knowledge_store.py` - Persistentes Wissen (JSONL, crash-safe, cross-session)
- `antigravity/planning_mode.py` - RESEARCH → PLAN → APPROVE → EXECUTE → VERIFY
- `antigravity/sync_engine.py` - Atomic Writes + Crash Recovery + Journaling

### Workflow + Automation
- `workflow_system/` - Opus 4.6 5-Step Compound Loop
- `workflow_system/cowork.py` - Autonomous Cowork Engine (Observe-Plan-Act-Reflect daemon)
- `workflow_system/resource_guard.py` - Resource Guard v2 (Crash-Proof, Predictive, Preemptive)
- `workflow_system/empire.py` - Legacy CLI (use empire_engine.py instead)

### Revenue Generation
- `x_lead_machine/` - Content generation + viral replies + lead gen
- `kimi_swarm/` - 100K/500K Kimi agent swarm mit Claude orchestration
- `atomic_reactor/` - YAML-basierte Task Definitions + async runner
- `crm/` - Express.js CRM mit BANT scoring (Port 3500)
- `BMA_ACADEMY/` - 9 Expert BMA Checklisten (DIN 14675)
- `products/` - Digitale Produkte (Gumroad-ready)

### Intelligence
- `brain_system/` - 7 spezialisierte AI Brains (Neuroscience-basiert)
- `gemini-mirror/` - Dual-Brain System (Kimi + Gemini parallel)
- `gold-nuggets/` - 15 Business Intelligence Dokumente (125KB)

### Infrastructure
- `openclaw-config/` - OpenClaw Agents, Cron Jobs, Model Routing
- `systems/` - Docker Compose, Scripts, Lead Agent Prompts
- `scripts/` - Auto-Repair, Bombproof Startup, Setup, LaunchAgent

## Empire Engine (Hauptprogramm)
```bash
python3 empire_engine.py              # Status Dashboard
python3 empire_engine.py scan         # News + Trends scannen
python3 empire_engine.py produce      # Content generieren
python3 empire_engine.py distribute   # Multi-Platform posten
python3 empire_engine.py leads        # Leads verarbeiten
python3 empire_engine.py revenue      # Revenue Report
python3 empire_engine.py auto         # Voller autonomer Zyklus
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

## Bombproof System (Crash-Schutz)
```bash
# Auto-Start bei jedem Boot (macOS LaunchAgent)
cp scripts/com.aiempire.bombproof.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.aiempire.bombproof.plist

# Startup-Reihenfolge (automatisch):
# 1. auto_repair.py (fixt .env, gcloud, korrupte Dateien, startet Ollama)
# 2. resource_guard.py startup_check (Crash Detection → Safe Mode)
# 3. Core Services (Ollama, Redis, PostgreSQL)
# 4. App Services (CRM, Atomic Reactor, OpenClaw)
# 5. Health Verification

# Manuell reparieren
python3 scripts/auto_repair.py
./scripts/bombproof_startup.sh --repair
```

## Resource Guard v2
```bash
python3 workflow_system/resource_guard.py              # Status
python3 workflow_system/resource_guard.py --can-launch 14b  # Preemptive Check

# Thresholds:
# CPU > 95% oder RAM > 92% → EMERGENCY (Ollama Models gestoppt)
# CPU > 85% oder RAM > 85% → CRITICAL (Concurrency: 50)
# CPU > 70% oder RAM > 75% → WARN (Concurrency: 200)
# Trend steigend + >60% → PREDICTIVE WARN
```

## Knowledge Store (Persistentes Wissen)
```python
from antigravity.knowledge_store import KnowledgeStore
ks = KnowledgeStore()

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

## Coding Standards
- Python 3 mit asyncio/aiohttp fuer alle async I/O
- JSON Output von allen AI Agents (strukturiert, parseable)
- Cost Tracking auf jedem API Call
- Model Routing: Ollama first, Kimi fuer komplex, Claude fuer kritisch
- ALLE API Keys in .env (NIEMALS hardcoden!)
- Config IMMER durch antigravity/config.py importieren
- Atomic Writes fuer alle kritischen State-Dateien
- Cross-Verification fuer alle kritischen Outputs

## Revenue Channels
1. Gumroad digital products (27-149 EUR) — BMA Checklisten, AI Kits
2. Fiverr/Upwork AI services (50-5000 EUR)
3. BMA + AI consulting (2000-10000 EUR) — UNIQUE NICHE (nur Maurice weltweit!)
4. Premium Community "Agent Builders Club" (29 EUR/Monat)
5. X/Twitter content + lead generation (3 Personas, 9 Posts/Tag)
6. OpenClaw Skills marketplace

## System Inventory (14 Systeme)
| System | Module | Status | Files |
|--------|--------|--------|-------|
| Antigravity | 26 Python Module | PRODUCTION | 268KB |
| Workflow System | orchestrator, cowork, empire | PRODUCTION | 72KB |
| Empire Engine | empire_engine.py | PRODUCTION | 12KB |
| Kimi Swarm | 100K + 500K agents | READY | 45KB |
| X Lead Machine | content + leads | READY | 24KB |
| Atomic Reactor | YAML tasks + runner | PRODUCTION | 10KB |
| CRM | Express.js + SQLite | PRODUCTION | 32KB |
| Brain System | 7 AI Brains | PRODUCTION | 20KB |
| Gemini Mirror | Dual-Brain (Kimi+Gemini) | PRODUCTION | 114KB |
| BMA Academy | 9 Expert Checklisten | PRODUCT READY | 25KB |
| OpenClaw Config | Agents + Cron + Models | PRODUCTION | 15KB |
| Gold Nuggets | 15 Business Intel Docs | COMPLETE | 125KB |
| Auto-Repair | Self-healing + Ollama AI | PRODUCTION | 16KB |
| Bombproof Startup | LaunchAgent + 5 Phases | PRODUCTION | 14KB |

## Current Status
- Revenue: 0 EUR (alle Kanaele bereit aber nicht aktiviert)
- Systems: 11/12 aktiv (Ollama offline wenn nicht gestartet)
- Security: API Keys gesichert (keine hardcoded Keys mehr)
- Knowledge: 7+ Items im Knowledge Store
