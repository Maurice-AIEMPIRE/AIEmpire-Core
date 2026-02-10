# AIEmpire-Core - Project Context

## Owner
Maurice Pfeifer, 37, Elektrotechnikmeister, 16 Jahre BMA-Expertise (Brandmeldeanlagen).
Ziel: 100 Mio EUR in 1-3 Jahren, alles automatisiert mit AI.

## Architecture
```
CONTROL: Claude Code + GitHub
AGENTS:  OpenClaw (Port 18789, 9 Cron Jobs)
MODELS:  Ollama (95% free) → Kimi K2.5 (4%) → Gemini (Mirror) → Claude (1%)
DATA:    Redis + PostgreSQL + ChromaDB
TASKS:   Atomic Reactor (FastAPI, Port 8888)
SWARM:   Kimi 50K-500K Agents
MIRROR:  Gemini Flash/Pro (Dual-Brain Amplification)
SALES:   X/Twitter Lead Machine + CRM (Port 3500)
REVENUE: Gumroad + Fiverr + Consulting
```

## Key Directories
- `workflow-system/` - Opus 4.6 5-Step Compound Loop (AUDIT → ARCHITECT → ANALYST → REFINERY → COMPOUNDER)
- `workflow-system/cowork.py` - Autonomous Cowork Engine (Observe-Plan-Act-Reflect daemon)
- `workflow-system/resource_guard.py` - CPU/RAM/Disk Monitoring + Auto-Throttling
- `gemini-mirror/` - **Gemini Dual-Brain Mirror System** (see below)
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

## Gemini Mirror System (Dual-Brain)
```
Main Brain (Mac/Kimi)  ←→  Mirror Brain (Gemini)
   Orchestrator              Mirror Orchestrator
   Cowork Agent              Mirror Cowork
         ↓   ↑               ↓   ↑
         Sync Engine (bidirektional, alle 15 Min)
              ↓
         Dual Brain (Review → Amplify → Compete, jede Stunde)
              ↓
         Vision Interrogator (taegliche Fragen, digitales Gedaechtnis)
```

### Gemini Mirror Dateien
- `gemini-mirror/gemini_client.py` - Hybrid API Client (Ollama → Gemini Flash → Pro)
- `gemini-mirror/mirror_orchestrator.py` - 5-Step Compound Loop auf Gemini
- `gemini-mirror/mirror_cowork.py` - Autonomer Agent (Observe-Plan-Act-Reflect)
- `gemini-mirror/sync_engine.py` - Bidirektionale Synchronisation
- `gemini-mirror/vision_interrogator.py` - Taegliche Fragen + digitales Gedaechtnis
- `gemini-mirror/dual_brain.py` - Gegenseitige Verstaerkungs-Schleife
- `gemini-mirror/gemini_empire.py` - Unified CLI
- `gemini-mirror/setup.py` - Initialisierung
- `gemini-mirror/config.py` - Zentrale Konfiguration

### Gemini Mirror Usage
```bash
# Setup (einmalig)
python gemini-mirror/setup.py

# Gesamtstatus
python gemini-mirror/gemini_empire.py status

# Voller Zyklus (Workflow + Cowork + Brain + Sync)
python gemini-mirror/gemini_empire.py full

# Einzelne Komponenten
python gemini-mirror/gemini_empire.py workflow              # 5-Step Loop
python gemini-mirror/gemini_empire.py workflow --step audit  # Einzelner Schritt
python gemini-mirror/gemini_empire.py cowork --focus revenue # Cowork
python gemini-mirror/gemini_empire.py sync                   # Sync
python gemini-mirror/gemini_empire.py brain                  # Dual-Brain
python gemini-mirror/gemini_empire.py vision generate        # Fragen generieren
python gemini-mirror/gemini_empire.py questions              # Offene Fragen
python gemini-mirror/gemini_empire.py answer Q-001 "Text"   # Frage beantworten

# Daemon-Modi
python gemini-mirror/gemini_empire.py daemon                 # Alle Daemons
python gemini-mirror/gemini_empire.py cowork --daemon        # Cowork Daemon
python gemini-mirror/gemini_empire.py sync --daemon          # Sync Daemon

# Neuer Zyklus
python gemini-mirror/gemini_empire.py cycle
```

### n8n Workflows (Gemini)
- `07_gemini_mirror_sync.json` - Sync alle 15 Minuten
- `08_vision_interrogator.json` - Vision-Fragen 3x taeglich
- `09_dual_brain_pulse.json` - Amplification stuendlich

## Current Blockers
- Revenue = 0 EUR (channels need activation)
- No Fiverr gigs live
- Telegram bot token invalid
