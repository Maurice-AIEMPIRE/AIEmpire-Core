# Copilot Instructions - AIEmpire-Core

## Project Context

This is **Maurice Pfeifer's AI Empire** - a fully automated business system targeting 100M EUR revenue through AI agents, digital products, and consulting.

**Owner:** Maurice Pfeifer, 37, Elektrotechnikmeister, 16 years BMA expertise (Brandmeldeanlagen / Fire Alarm Systems).

**Unique Niche:** BMA + AI = unoccupied global market. Maurice is the only person combining deep fire alarm systems expertise with AI automation knowledge.

## Architecture Overview

```
CONTROL:   Claude Code + GitHub (Issues as command interface)
AGENTS:    OpenClaw (Port 18789, 9 Cron Jobs)
MODELS:    Ollama (95% free) → Kimi K2.5 (4%) → Claude (1%)
DATA:      Redis + PostgreSQL + ChromaDB
TASKS:     Atomic Reactor (FastAPI, Port 8888)
SWARM:     Kimi 50K-500K Agents
SALES:     X/Twitter Lead Machine + CRM (Port 3500, BANT Scoring)
REVENUE:   Gumroad + Digistore24 + Fiverr + Consulting
WORKFLOW:  5-Step Loop (AUDIT → ARCHITECT → ANALYST → REFINERY → COMPOUNDER)
COWORK:    Autonomous daemon (OBSERVE → PLAN → ACT → REFLECT)
```

## Key Directories

| Directory | Purpose | Language |
|-----------|---------|----------|
| `workflow-system/` | Opus 4.6 5-Step Compound Loop + Cowork Engine | Python |
| `kimi-swarm/` | 100K/500K Kimi agent swarm with Claude orchestration | Python |
| `atomic-reactor/` | YAML-based task definitions + async runner | Python/YAML |
| `x-lead-machine/` | Content generation + viral replies + lead gen | Python |
| `crm/` | Express.js CRM with BANT scoring | JavaScript |
| `openclaw-config/` | OpenClaw agent configs, cron jobs, model routing | Markdown/JSON |
| `brain-system/` | Orchestrator + brain modules (brainstem → hippocampus) | Python/Markdown |
| `gold-nuggets/` | Curated business intelligence documents | Markdown |
| `n8n-workflows/` | n8n automation connector | Python |
| `mobile-command-center/` | PWA for mobile access | HTML/JS |
| `systems/` | Docker compose, lead agent prompts | YAML/Markdown |
| `BMA_ACADEMY/` | Training academy structure | Markdown |

## Coding Standards

1. **Python 3** with `asyncio`/`aiohttp` for all async I/O
2. **JSON output** from all AI agents (structured, parseable)
3. **Cost tracking** on every API call
4. **Model routing:** Ollama first → Kimi for volume → Claude for critical only
5. **Environment variables** for all API keys (never hardcode)
6. **German comments are OK** - Maurice works bilingual (German/English)
7. **Pragmatic code** - working > perfect. Ship fast, iterate later.

## Revenue Channels (Priority Order)

1. Gumroad digital products (27-149 EUR)
2. Fiverr/Upwork AI services (30-5000 EUR)
3. BMA + AI consulting (2000-10000 EUR) - UNIQUE NICHE
4. OpenClaw Skills marketplace
5. X/Twitter content + lead generation
6. TikTok 3-persona content pipeline
7. Premium community (Agent Builders Club, 29 EUR/month)

## Agent Squad Structure

- **Squad 1:** Content Factory (15 agents) - TikTok, SEO, cross-platform
- **Squad 2:** Growth & Marketing (12 agents) - viral replies, outreach
- **Squad 3:** Sales (10 agents) - BANT qualification, email sequences
- **Squad 4:** Product & Tech (15 agents) - Gumroad builds, landing pages
- **Squad 5:** Operations (8 agents) - scheduling, budget, reporting
- **Squad 6:** Security (5 agents) - API keys, cost monitoring, rate limits
- **Squad 7:** Brain Trust (5 agents) - strategy, risk, innovation

## Important Files

- `CLAUDE.md` - Claude Code project context (auto-loaded)
- `EMPIRE_BLUEPRINT.md` - Full strategic blueprint
- `COPILOT_BRIEFING.md` - Quick-start briefing with current tasks
- `workflow-system/orchestrator.py` - Main workflow engine
- `workflow-system/cowork.py` - Autonomous background agent
- `workflow-system/resource_guard.py` - CPU/RAM monitoring

## Workflow Commands

```bash
# Full 5-step compound loop
python workflow-system/orchestrator.py

# Single step
python workflow-system/orchestrator.py --step audit

# Cowork daemon (every 30 min)
python workflow-system/cowork.py --daemon

# Empire CLI
python workflow-system/empire.py status
python workflow-system/empire.py full
```

## Constraints

- Budget: max 100 EUR/month for APIs
- Hardware: Apple M4, 16GB RAM
- Must not interfere with day job at Roewer GmbH
- No API keys in code - ENV variables only
- Rate limits must be respected (no spam)
- Anonymous TikTok personas (no face, no real name)

## Style Preferences

- Maurice prefers: direct, pragmatic, no unnecessary talk
- Language: German for business docs, English for code/technical
- Formatting: Clear structure, tables over paragraphs
- Commit messages: English, concise, prefix with component name
