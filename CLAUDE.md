# AIEmpire-Core - Project Context

## Owner
Maurice Pfeifer, 37, Elektrotechnikmeister, 16 Jahre BMA-Expertise (Brandmeldeanlagen).
Ziel: 100 Mio EUR in 1-3 Jahren, alles automatisiert mit AI.

## Architecture
```
CONTROL: Claude Code + GitHub
AGENTS:  OpenClaw (Port 18789, 9 Cron Jobs)
MODELS:  Ollama (95% free) → Kimi K2.5 (4%) → Claude (1%)
DATA:    Redis + PostgreSQL + ChromaDB
TASKS:   Atomic Reactor (FastAPI, Port 8888)
SWARM:   Kimi 50K-500K Agents
SALES:   X/Twitter Lead Machine + CRM (Port 3500)
REVENUE: Gumroad + Fiverr + Consulting
```

## Key Directories
- `workflow-system/` - Opus 4.6 5-Step Compound Loop (AUDIT → ARCHITECT → ANALYST → REFINERY → COMPOUNDER)
- `workflow-system/cowork.py` - Autonomous Cowork Engine (Observe-Plan-Act-Reflect daemon)
- `workflow-system/resource_guard.py` - CPU/RAM/Disk Monitoring + Auto-Throttling
- `kimi-swarm/` - 100K/500K Kimi agent swarm with Claude orchestration
- `atomic-reactor/` - YAML-based task definitions + async runner
- `x-lead-machine/` - Content generation + viral replies + lead gen
- `crm/` - Express.js CRM with BANT scoring
- `openclaw-config/` - OpenClaw agent configs, cron jobs, model routing
- `systems/` - Docker compose, lead agent prompts
- `gold-nuggets/` - Business intelligence documents

## Workflow System Usage
```bash
# Full 5-step loop
python workflow-system/orchestrator.py

# Single step
python workflow-system/orchestrator.py --step audit

# New weekly cycle
python workflow-system/orchestrator.py --new-cycle

# Check status
python workflow-system/orchestrator.py --status
```

## Cowork Engine (Autonomer Background Agent)
```bash
# Ein Zyklus (Observe → Plan → Act → Reflect)
python workflow-system/cowork.py

# Daemon-Modus (alle 30 Min)
python workflow-system/cowork.py --daemon

# Fokus + Intervall anpassen
python workflow-system/cowork.py --daemon --interval 900 --focus revenue

# Fokus-Bereiche: revenue | content | automation | product
python workflow-system/cowork.py --status
```

## Resource Guard (Ueberlastungsschutz)
```bash
# Status anzeigen
python workflow-system/resource_guard.py

# Integriert in Orchestrator + Cowork - stoppt automatisch bei:
# CPU > 95% oder RAM > 92% → EMERGENCY (alle Agents pausiert)
# CPU > 85% oder RAM > 85% → CRITICAL (Concurrency: 50, Outsource-Modus)
# CPU > 70% oder RAM > 75% → WARN (Concurrency: 200, leichte Verzoegerung)
```

## Empire Control Center (Unified CLI)
```bash
# Gesamtstatus aller Systeme
python workflow-system/empire.py status

# Workflow ausfuehren
python workflow-system/empire.py workflow
python workflow-system/empire.py workflow --step audit

# Cowork starten
python workflow-system/empire.py cowork --daemon --focus revenue

# Neuer Wochen-Zyklus
python workflow-system/empire.py cycle

# Alles nacheinander (Workflow + Cowork)
python workflow-system/empire.py full
```

## Session-Start Hook
Zeigt bei jedem Claude Code Start automatisch den System-Status.
Konfiguriert in `~/.claude/settings.json` → hooks.SessionStart.

## Agent Teams (Experimental)
Enabled via CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1.
Use for parallel tasks: research + implementation + testing.

## Coding Standards
- Python 3 with asyncio/aiohttp for all async I/O
- JSON output from all AI agents (structured, parseable)
- Cost tracking on every API call
- Model routing: Ollama first, Kimi for complex, Claude for critical
- Environment variables for all API keys (never hardcode)

## Revenue Channels
1. Gumroad digital products (27-149 EUR)
2. Fiverr/Upwork AI services (30-5000 EUR)
3. BMA + AI consulting (2000-10000 EUR) - UNIQUE NICHE
4. OpenClaw Skills marketplace
5. X/Twitter content + lead generation

## Current Blockers
- Revenue = 0 EUR (channels need activation)
- No Fiverr gigs live
- Telegram bot token invalid
- MOONSHOT_API_KEY must be set via .env (see .env.example)

## Fixed Issues (2026-02-10)
- SECURITY: Removed 7 hardcoded API keys from source code (use .env)
- CONFIG: Created .env.example with all required environment variables
- CONFIG: Completed requirements.txt (added rich, httpx, fastapi, uvicorn, ruff, pytest)
- CONFIG: Updated Claude model IDs to current versions (Haiku/Sonnet/Opus 4.5)
- IMPORT: Added missing __init__.py in systems/ and systems/kimi_bridge/
- CODE: Fixed X/Twitter auto-poster (uncommented API integration)
- CODE: Implemented task execution in claude_failover_system.py
- CODE: Added API key validation + tasks dir check in atomic-reactor
- CODE: Added missing `import os` in kimi-swarm/swarm_100k.py

## WARROOM Operating System (2026-02-10)

### Overview
100-agent specialist system organized in 6 squads. Agents are ROLES (prompt-based),
not separate processes. The orchestrator invokes the right role for each task.

### Command Center
- `warroom/00_command/` — Mission brief, objectives, status board, rules
- `warroom/00_nucleus/` — Squad definitions, routing matrix, operating rules
- `warroom/01_intake/` — Raw uploads + file manifests

### Squad Registry (see `agents.json` for full details)
| Squad | Count | Agent IDs | Work Folder |
|-------|-------|-----------|-------------|
| Legal Warroom | 10 | L01-L10 | `legal/` |
| Data Ops | 10 | D01-D10 | `data/` |
| Marketing | 20 | M01-M20 | `marketing/` |
| Sales | 20 | S01-S20 | `sales/` |
| Research | 10 | R01-R10 | `ops/skills/`, `blueprints/` |
| Ops/Engineering | 30 | O01-O30 | `ops/` |

### Warroom Commands
```
RUN WARROOM — Full Phase 0-4 execution
[STATUS] — Show pipeline status + blockers
[SPAWN] <team> <count> <objective> — Activate squad for task
[INGEST] <path> — Normalize + tag + index files
[LEGAL_RUN] — Build timeline + evidence + claims
[MARKETING_RUN] — Build offer + copy + funnel + email
[EXPORT] — Generate exports bundle
```

### Key Docs
- `ORCHESTRATOR.md` — Master workflow
- `agents.json` — 100 agent definitions
- `warroom/00_nucleus/warroom_rules.md` — 14 operating constraints
- `warroom/00_nucleus/routing_matrix.md` — Model selection + privacy
- `warroom/00_command/status.md` — Live status board
