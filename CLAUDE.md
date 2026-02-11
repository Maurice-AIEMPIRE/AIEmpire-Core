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
- `workflow_system/` - Opus 4.6 5-Step Compound Loop (AUDIT → ARCHITECT → ANALYST → REFINERY → COMPOUNDER)
- `workflow_system/cowork.py` - Autonomous Cowork Engine (Observe-Plan-Act-Reflect daemon)
- `workflow_system/resource_guard.py` - Resource Guard v2 (Crash-Proof, Predictive, Preemptive)
- `antigravity/` - 4 Godmode Programmer Agents + Unified Router + Cross-Verification
- `antigravity/cross_verify.py` - Agent-Verification-System (agents verify each other)
- `antigravity/sync_engine.py` - Crash-safe state sync with atomic writes
- `antigravity/config.py` - Central config with auto .env loading
- `kimi_swarm/` - 100K/500K Kimi agent swarm with Claude orchestration
- `atomic_reactor/` - YAML-based task definitions + async runner
- `x_lead_machine/` - Content generation + viral replies + lead gen
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

## Resource Guard v2 (Crash-Proof Protection)
```bash
# Status anzeigen (inkl. Crash Detection)
python workflow_system/resource_guard.py

# Crash Recovery Check
python workflow_system/resource_guard.py --recover

# Preemptive Launch Check (vor Model-Start)
python workflow_system/resource_guard.py --can-launch 14b

# Thresholds:
# CPU > 95% oder RAM > 92% → EMERGENCY (Agents pausiert + Ollama Models gestoppt)
# CPU > 85% oder RAM > 85% → CRITICAL (Concurrency: 50, Outsource)
# CPU > 70% oder RAM > 75% → WARN (Concurrency: 200, Delay)
# Trend steigend + >60% → PREDICTIVE WARN (drosselt bevor Limit erreicht)

# v2 Features:
# - Crash Detection: erkennt unsauberes Shutdown → SAFE MODE
# - Preemptive Checks: guard.can_launch("14b") vor Model-Start
# - Predictive Throttling: erkennt steigende Trends
# - Signal Handling: SIGTERM/SIGINT → sauberes Shutdown
# - Emergency Actions: stoppt Ollama Models automatisch bei RAM-Krise
```

## Cross-Agent Verification (Qualitaetssicherung)
```bash
# Prinzip: "Agents verify each other" — nie ein Agent bewertet eigene Arbeit
# Fresh Context: Verifier sieht NUR Aufgabe + Output, nicht den Prozess
# Konsensus: Mehrere Agents muessen uebereinstimmen bei kritischen Tasks

# In Code:
# from antigravity.cross_verify import VerificationGate
# gate = VerificationGate(router)
# result = await gate.execute_verified(prompt, agent_key="coder")
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
