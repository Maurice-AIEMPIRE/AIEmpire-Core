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
SWARM:   Open Swarm (Ollama, $0) + Cloud Swarm (Free Tier) + Kimi Legacy (API)
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
- `workflow-system/open_swarm.py` - OPEN SWARM: Kostenloser Agent-Schwarm mit Ollama ($0, Sprint-System)
- `workflow-system/cloud_swarm.py` - CLOUD SWARM: Free Tier Cloud AI (Groq, Gemini, Cerebras, HuggingFace, $0)
- `kimi-swarm/` - Legacy: 100K/500K Kimi agent swarm (braucht Moonshot API Key)
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

## Open Swarm (Kostenloser Agent-Schwarm)
```bash
# Sprint starten (default: revenue, 50 Tasks)
python workflow-system/open_swarm.py --sprint revenue --tasks 50

# Content-Sprint (100 Posts/Scripts generieren)
python workflow-system/open_swarm.py --sprint content --tasks 100

# Lead-Sprint (B2B Leads recherchieren)
python workflow-system/open_swarm.py --sprint leads --tasks 30

# Intelligence-Sprint (Markt-/Wettbewerbsanalyse)
python workflow-system/open_swarm.py --sprint intel --tasks 20

# Product-Sprint (Produkt-Ideen + Optimierungen)
python workflow-system/open_swarm.py --sprint products --tasks 30

# Test-Modus (5 Tasks, schneller Check)
python workflow-system/open_swarm.py --test

# Daemon: Automatische Sprints alle 60 Min
python workflow-system/open_swarm.py --daemon --interval 3600

# Status anzeigen
python workflow-system/open_swarm.py --status

# Sprint-Typen: revenue | content | leads | intel | products
# Kosten: $0.00 - komplett kostenlos mit Ollama!
# Ersetzt: Kimi Moonshot API ($0.0005/task)
```

## Cloud Swarm (Free Tier Cloud AI Power)
```bash
# Cloud Sprint starten (nutzt Groq, Gemini, Cerebras, etc.)
python workflow-system/cloud_swarm.py --sprint revenue --tasks 100

# Maximale Power (alle Provider parallel)
python workflow-system/cloud_swarm.py --sprint content --tasks 200 --max-power

# Nur bestimmte Provider
python workflow-system/cloud_swarm.py --providers groq,cerebras --tasks 50

# Provider Health Check
python workflow-system/cloud_swarm.py --health

# Status
python workflow-system/cloud_swarm.py --status

# Test (10 Tasks)
python workflow-system/cloud_swarm.py --test

# Daemon (automatische Sprints)
python workflow-system/cloud_swarm.py --daemon --interval 1800

# Provider: Groq, Cerebras, SambaNova, HuggingFace, Google Gemini, OpenRouter
# Kosten: $0.00 - nur Free Tiers!
# API Keys: export GROQ_API_KEY='...' etc.
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

## Product Factory (Signature-Produkt-Engine)
```bash
# Status + Ideen anzeigen
python workflow-system/product_factory.py

# Starter-Ideen laden (6 Produkte)
python workflow-system/product_factory.py --seed

# Neue Idee hinzufuegen
python workflow-system/product_factory.py --idea "BMA Checkliste" --desc "..."

# Alle Ideen bewerten (Score 0-100)
python workflow-system/product_factory.py --score

# Offer designen (Pricing, Bullets, CTA)
python workflow-system/product_factory.py --design 1

# Marketing generieren (30 Posts + 3 Emails)
python workflow-system/product_factory.py --market 1

# Volle Pipeline (Idea → Score → Design → Marketing)
python workflow-system/product_factory.py --pipeline
```

## Agent Registry (100-Agent-Management)
```bash
# Status
python workflow-system/agent_registry.py

# 20 Standard-Agents registrieren
python workflow-system/agent_registry.py --seed

# Agent nach Capability suchen
python workflow-system/agent_registry.py --find content_generation

# Health Check
python workflow-system/agent_registry.py --health

# Performance Report
python workflow-system/agent_registry.py --report
```

## QA Gate (make check)
```bash
make check    # Import + Lint + Status Checks
make test     # Quick Tests ohne Ollama
make help     # Alle verfuegbaren Commands
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

## Revenue Channels (via Product Factory)
6. Product Factory (Blueprints 27-49 EUR, SOPs 49-99 EUR, Automation Packs 99-149 EUR)

## Current Blockers
- Revenue = 0 EUR (channels need activation)
- No Fiverr gigs live
- Telegram bot token invalid
