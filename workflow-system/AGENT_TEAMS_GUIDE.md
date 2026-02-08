# Agent Teams Setup - AIEmpire-Core

## Aktivierung

Agent Teams ist aktiviert in `~/.claude/settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Alternative via Shell:
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

## Team-Vorlagen fuer AIEmpire-Core

### 1. Revenue Sprint Team
```
Create a team for a revenue sprint. Spawn three teammates:

- revenue-researcher: Analyze Gumroad, Fiverr, Upwork for high-demand
  AI products. Find gaps where our BMA+AI expertise has zero competition.
  Share findings with product-builder.

- product-builder: Based on researcher findings, create 3 digital
  products (markdown/PDF content). Use workflow-system/steps for quality.
  Coordinate with test-reviewer on deliverable quality.

- test-reviewer: Review all products for quality, pricing strategy,
  and market fit. Score each product 1-10. Send feedback to product-builder
  for iteration.

Coordinate via shared task list. Goal: 3 launch-ready products.
```

### 2. Content Pipeline Team
```
Create a team for weekly content production. Spawn four teammates:

- trend-scanner: Research trending topics in AI automation, BMA/fire alarm,
  and solopreneur niches. Output: 20 topic ideas ranked by viral potential.

- content-writer: Take top 10 topics and create X/Twitter posts, threads,
  and LinkedIn content. Use x-lead-machine/ patterns for hooks and CTAs.

- lead-optimizer: Review all content for lead generation effectiveness.
  Every post must have a clear CTA. Score conversion potential 1-10.

- scheduler: Organize final content into a 7-day calendar with optimal
  posting times. Output to x-lead-machine/READY_TO_POST.md.

Have them coordinate - trend-scanner feeds content-writer,
lead-optimizer reviews and sends back to content-writer for revision.
```

### 3. Bug Hunt / Debug Team
```
Create a team to investigate and fix issues. Spawn teammates:

- code-auditor: Review atomic-reactor/, kimi-swarm/, and crm/ for bugs,
  security issues, and hardcoded credentials. Document findings.

- fixer: Take auditor findings and implement fixes. Focus on critical
  security issues first (hardcoded API keys, missing error handling).

- test-writer: Create test scripts to verify fixes work. Run validation.

Coordinate through task list with dependencies: audit → fix → test.
```

### 4. Workflow System Enhancement Team
```
Create a team to enhance the Opus 4.6 Workflow System. Spawn teammates:

- analyst: Run workflow-system/orchestrator.py --status and review
  current state. Identify improvement opportunities in the 5-step loop.

- enhancer: Implement improvements to workflow steps. Add new prompt
  templates, better scoring criteria, or new convergence strategies.

- integrator: Connect workflow system outputs to existing systems
  (atomic-reactor tasks, kimi-swarm priorities, openclaw cron jobs).

Goal: Make the workflow system output directly actionable.
```

## Navigation

- `Shift+Up/Down` - Wechsel zwischen Teammates
- Team-Lead koordiniert alle Tasks
- Immer ueber Team-Lead herunterfahren: "Shutdown all teammates"

## Wann Agent Teams nutzen

JA:
- Parallele Recherche + Implementation + Testing
- Multi-Modul Features (Frontend + Backend + Tests)
- Debugging mit konkurrierenden Hypothesen
- Content-Produktion (Research + Writing + Review)

NEIN:
- Einzelne einfache Tasks
- Sequenzielle Abhaengigkeiten
- Aenderungen an der gleichen Datei

## Kosten

Agent Teams verbraucht deutlich mehr Tokens (proportional zur Teammate-Anzahl).
Nur einsetzen wenn parallele Arbeit echten Mehrwert bringt.
Fuer sequenzielle Arbeit: Einzelsession nutzen.
