# AIEmpire-Core - Project Context

## Owner
Maurice Pfeifer, 33, Elektrotechnikmeister, 16 Jahre BMA-Expertise (Brandmeldeanlagen).
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
- `workflow-system/empire_brain.py` - EMPIRE BRAIN: Zentrales Gehirn, verbindet ALLES
- `workflow-system/ollama_engine.py` - Lokale LLM Engine (Ollama, $0 Kosten)
- `workflow-system/agent_manager.py` - Revenue-basiertes Agent Ranking (Dirk Kreuter Style)
- `workflow-system/knowledge_harvester.py` - Knowledge Base + Codebase Scanner
- `workflow-system/cowork.py` - Autonomous Cowork Engine (Observe-Plan-Act-Reflect daemon)
- `workflow-system/resource_guard.py` - CPU/RAM/Disk Monitoring + Auto-Throttling
- `workflow-system/content_machine.py` - GELDMASCHINE: 1000x Content fuer X + TikTok ($0 mit Ollama)
- `workflow-system/tiktok_factory.py` - TikTok Script Factory (45s Format, Batch-Generierung)
- `workflow-system/x_posting_engine.py` - X/Twitter Posting Pipeline (Posts, Threads, Replies, DMs)
- `kimi-swarm/` - 100K/500K Kimi agent swarm with Claude orchestration
- `atomic-reactor/` - YAML-based task definitions + async runner
- `x-lead-machine/` - Content generation + viral replies + lead gen
- `crm/` - Express.js CRM with BANT scoring
- `openclaw-config/` - OpenClaw agent configs, cron jobs, model routing
- `systems/` - Docker compose, lead agent prompts
- `gold-nuggets/` - Business intelligence documents
- `scripts/` - Automation dashboard, notifications, master orchestrator

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

## Empire Brain (Zentrales Gehirn)
```bash
# System-Check: Alle Systeme verbinden
python workflow-system/empire_brain.py --connect

# Denk-Zyklus (Analyse → Entscheidung → Aktion)
python workflow-system/empire_brain.py --think --focus revenue

# Revenue-Analyse (Dirk Kreuter Modus)
python workflow-system/empire_brain.py --revenue
```

## Ollama Engine (Lokale AI, $0)
```bash
# OFFLINE_MODE=true (Default) → Ollama statt Cloud
# OFFLINE_MODE=false → Kimi Cloud Fallback
# Verfuegbare Modelle: qwen2.5-coder:7b, glm-4.7-flash, deepseek-r1:8b
python workflow-system/ollama_engine.py  # Test
```

## Agent Manager (Revenue Ranking)
```bash
# Top 10 Leaderboard nach Revenue
# Auto-Boost: Platz 1-3 → 2-3x Tasks
# Auto-Demote: Platz 8-10 → 0.5x Tasks
python workflow-system/agent_manager.py  # Demo
```

## Content Machine (Geldmaschine)
```bash
# Status anzeigen
python workflow-system/content_machine.py

# 50 Content-Pieces generieren (X + TikTok)
python workflow-system/content_machine.py --generate 50

# Batch X-Content / TikTok Scripts
python workflow-system/content_machine.py --batch x --count 20
python workflow-system/content_machine.py --batch tiktok --count 10

# 1 Idee → 10 Content-Pieces (Multiplier)
python workflow-system/content_machine.py --multiply "AI Automation fuer KMU"

# Kompletter Wochen-Plan (7 Posts + Thread + 5 TikToks)
python workflow-system/content_machine.py --weekly
```

## TikTok Factory
```bash
# 20 TikTok Scripts generieren
python workflow-system/tiktok_factory.py --generate 20

# Nische waehlen: geld_verdienen, ai_automation, bma_ai, build_in_public
python workflow-system/tiktok_factory.py --generate 10 --niche bma_ai

# Serie generieren (zusammenhaengende Teile)
python workflow-system/tiktok_factory.py --series 0

# Alle Scripts exportieren
python workflow-system/tiktok_factory.py --export
```

## X Posting Engine
```bash
# 30 X-Posts generieren
python workflow-system/x_posting_engine.py --generate 30

# 10 strategische Replies
python workflow-system/x_posting_engine.py --replies 10

# Wochen-Content-Plan
python workflow-system/x_posting_engine.py --weekly

# DM-Sequence fuer Lead
python workflow-system/x_posting_engine.py --dm "AI Automation Interesse"

# Ready-to-Post exportieren
python workflow-system/x_posting_engine.py --export
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
