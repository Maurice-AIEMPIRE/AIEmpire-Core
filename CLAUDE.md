# AIEmpire-Core - Project Context

## Owner
Maurice Pfeifer, 37, Elektrotechnikmeister, 16 Jahre BMA-Expertise (Brandmeldeanlagen).
Ziel: 100 Mio EUR in 1-3 Jahren, alles automatisiert mit AI.

## Architecture
```
CONTROL: Claude Code + GitHub
AGENTS:  OpenClaw (Port 18789, 9 Cron Jobs)
MODELS:  Ollama (95% free) → Kimi K2.5 (4%) → Claude (1%) → Gemini (Mirror Brain)
DATA:    Redis + PostgreSQL + ChromaDB
TASKS:   Atomic Reactor (FastAPI, Port 8888)
SWARM:   Kimi 50K-500K Agents
DUAL-BRAIN: Claude (Primary/Mac) <-> Gemini (Mirror/Cloud) + Cross-Pollination
VISION:  Daily Question Engine → Vision Profile → Decision Support
FACTORY: Product Factory (7-Step Pipeline: Idea → Revenue)
SALES:   X/Twitter Lead Machine + CRM (Port 3500)
REVENUE: Gumroad + Fiverr + Consulting + Product Factory
```

## Key Directories
- `workflow-system/` - Opus 4.6 5-Step Compound Loop (AUDIT → ARCHITECT → ANALYST → REFINERY → COMPOUNDER)
- `workflow-system/cowork.py` - Autonomous Cowork Engine (Observe-Plan-Act-Reflect daemon)
- `workflow-system/resource_guard.py` - CPU/RAM/Disk Monitoring + Auto-Throttling
- `gemini-mirror/` - Dual-Brain System (Claude <-> Gemini bidirectional sync + evolution)
- `gemini-mirror/mirror_core.py` - Gemini API, state sync, improvement queue
- `gemini-mirror/vision_engine.py` - Daily question engine, vision profile builder
- `gemini-mirror/cross_pollinator.py` - Dual-brain challenge, merge best of both
- `gemini-mirror/memory_bridge.py` - Shared knowledge graph across both brains
- `product-factory/` - Automated 7-step product pipeline (Idea → Revenue)
- `product-factory/factory.py` - Full pipeline: score, design, produce, market, sell
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

# Alles nacheinander (Workflow + Cowork + Mirror Sync)
python workflow-system/empire.py full
```

## Gemini Mirror (Dual-Brain System)
```bash
# Mirror initialisieren (einmalig)
python workflow-system/empire.py mirror --init

# Sync-Zyklus ausfuehren
python workflow-system/empire.py mirror --sync

# Continuous Sync Daemon
python workflow-system/empire.py mirror --daemon --interval 300

# Status anzeigen
python workflow-system/empire.py mirror --status

# Direkt ausfuehren:
python gemini-mirror/mirror_core.py --init
python gemini-mirror/mirror_core.py --sync
python gemini-mirror/mirror_core.py --daemon
```

## Vision Discovery Engine (Tagesfragen)
```bash
# Tagesfragen anzeigen
python workflow-system/empire.py vision

# Fragen generieren
python workflow-system/empire.py vision --generate

# Fragen interaktiv beantworten
python workflow-system/empire.py vision --answer

# Vision-Profil anzeigen
python workflow-system/empire.py vision --profile

# Q&A History
python workflow-system/empire.py vision --history
```

## Cross-Pollinator (Dual-Brain Evolution)
```bash
# Evolution Cycle (beide Brains loesen gleiche Challenge, bestes wird gemerged)
python workflow-system/empire.py evolve

# Status
python workflow-system/empire.py evolve --status

# Direkt:
python gemini-mirror/cross_pollinator.py --evolve
python gemini-mirror/cross_pollinator.py --challenge "Beschreibung der Challenge"
```

## Product Factory (Automatische Produkt-Pipeline)
```bash
# Status
python workflow-system/empire.py factory

# Idee hinzufuegen
python workflow-system/empire.py factory --add-idea "BMA Checkliste fuer Projektabnahme"

# Ideen bewerten
python workflow-system/empire.py factory --score

# Volle Pipeline (Idee → Score → Design → Produce → Market → Sell)
python workflow-system/empire.py factory --pipeline --idea "Beschreibung"

# Alle Produkte listen
python workflow-system/empire.py factory --list

# Direkt:
python product-factory/factory.py pipeline --idea "Beschreibung"
python product-factory/factory.py idea "BMA Checkliste"
python product-factory/factory.py score
python product-factory/factory.py design idea_xxx
python product-factory/factory.py produce prod_xxx
python product-factory/factory.py market prod_xxx
```

## Shared Memory (Wissens-Graph)
```bash
# Status
python workflow-system/empire.py memory

# Aus bestehenden Systemen importieren
python workflow-system/empire.py memory --import-all

# Wissen suchen
python workflow-system/empire.py memory --search "revenue"

# Konsolidieren
python workflow-system/empire.py memory --consolidate

# Direkt:
python gemini-mirror/memory_bridge.py --add business "key" "value"
python gemini-mirror/memory_bridge.py --search "query"
python gemini-mirror/memory_bridge.py --decide "Entscheidung" "Begruendung"
```

## Session-Start Hook
Zeigt bei jedem Claude Code Start automatisch den System-Status.
Konfiguriert in `~/.claude/settings.json` → hooks.SessionStart.

## Agent Teams (Experimental)
Enabled via CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1.
Use for parallel tasks: research + implementation + testing.

## Environment Variables
```bash
MOONSHOT_API_KEY        # Kimi/Moonshot API (existing)
ANTHROPIC_API_KEY       # Claude API (existing)
GEMINI_API_KEY          # Google Gemini API (NEW - required for Mirror)
EMPIRE_SYNC_SECRET      # Shared secret for brain sync (optional)
```

## Coding Standards
- Python 3 with asyncio/aiohttp for all async I/O
- JSON output from all AI agents (structured, parseable)
- Cost tracking on every API call
- Model routing: Ollama first, Kimi for complex, Claude for critical, Gemini for mirror
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
