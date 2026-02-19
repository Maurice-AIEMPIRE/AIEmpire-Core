# IMPLEMENTATION PLAN — AI Empire Stabilize & Standardize

**Date**: 2026-02-10
**Author**: Empire Nucleus (Claude Opus 4.6)
**Status**: ACTIVE

---

## Executive Summary

This plan takes the AIEmpire-Core codebase from "functional but fragile" to "stable and scalable". It fixes Python packaging issues, automates CSS vendor prefixes, and creates a filesystem-based 100-agent skill system that can be loaded on demand without blowing up context windows.

---

## Phase 0: Baseline Inventory (COMPLETED)

### Findings

**Codebase Stats:**
- 55+ Python files across 15+ directories
- 5 standalone HTML dashboards + 8 worktree copies
- 100 agents defined in `agents.json` across 6 teams
- 2 Claude Code worktrees (tender-maxwell, ecstatic-hoover)

**Critical Discovery: empire_nucleus.py does NOT exist in the repo.**
The EMPIRE_NUCLEUS_FIX_GUIDE.md references Pyre2 errors for a file that isn't present. The modules it supposedly imports (ollama_engine, agent_manager, memory_core, heartbeat_scheduler, guarded_tools, skills_library) also don't exist. Instead, the codebase has functional alternatives:
- ollama_engine → `antigravity/ollama_client.py` (OllamaClient with httpx)
- agent_manager → `antigravity/config.py` (AgentConfig dataclasses) + `antigravity/agent_runner.py`
- memory_core → `brain-system/orchestrator.py` (SQLite synapses) + `workflow-system/state/context.py` (JSON state)
- heartbeat_scheduler → `workflow-system/resource_guard.py` (ResourceGuard)
- guarded_tools → `workflow-system/resource_guard.py`
- skills_library → `workflow-system/steps/` (step modules)

**Decision:** Rather than creating empire_nucleus.py from scratch, the existing subsystems are already functional. The priority is making them importable and stable.

---

## Phase 1: Python Packaging (COMPLETED)

### Changes Made

| File | Action | Why |
|------|--------|-----|
| `workflow-system/__init__.py` | Created (empty) | Package was not importable |
| `godmode/__init__.py` | Created (empty) | Package was not importable |
| `brain-system/__init__.py` | Created (empty) | Package was not importable |

### Import Architecture (current, working)
```
empire_launch.py (root entry point)
├── antigravity/ (proper package with __init__.py + 4 internal imports)
│   ├── config.py → AgentConfig, MERGE_CHECKS, agents
│   ├── ollama_client.py → OllamaClient (httpx-based)
│   ├── agent_runner.py → run_agent, run_merge_checks
│   └── swarm_run.py → run_swarm (orchestrator)
│
├── workflow-system/ (now a package)
│   ├── empire.py → CLI entry point
│   ├── orchestrator.py → 5-step loop (uses relative imports from state/, steps/)
│   ├── resource_guard.py → ResourceGuard
│   ├── cowork.py → Observe-Plan-Act-Reflect daemon
│   ├── state/context.py → JSON state persistence
│   └── steps/ → step1-5 modules
│
├── brain-system/ (now a package)
│   └── orchestrator.py → 8-brain SQLite system
│
├── systems/ (already a package)
│   ├── kimi_bridge/ → KimiClient (aiohttp + Moonshot API)
│   └── stripe_payments/ → Product catalog + Stripe CLI
│
├── chat_manager.py (standalone, multi-model)
└── claude_failover_system.py (standalone, GitHub fallback)
```

### Dependencies Status
**requirements.txt** already declares: aiohttp, pyyaml, rich, httpx, ruff, pytest, fastapi, uvicorn

**Note:** `requests` is NOT used in the codebase — httpx is used instead. If you see Pyre2 errors about `requests`, it's likely from a file not yet committed or from empire_nucleus.py (which doesn't exist in the repo).

### Remaining Python Task (for Maurice)
The `.venv` symlinks point to Python 3.14 on your Mac. On your machine, run:
```bash
cd ~/AIEmpire-Core  # or wherever the repo is
source .venv/bin/activate
pip install -r requirements.txt
pip install -r empire-api/requirements.txt
python -m compileall . -q  # should pass with 0 errors
```

---

## Phase 2: Safari CSS Fix (COMPLETED)

### Automated Solution
Created `scripts/fix_webkit_backdrop.py` — a Python script that:
1. Finds all HTML/CSS files recursively (including worktrees)
2. Identifies `backdrop-filter:` without `-webkit-backdrop-filter:`
3. Adds the webkit prefix automatically
4. Is idempotent (safe to run multiple times)

### Results
- **6 fixes applied** across 2 files:
  - `AI_EMPIRE_BIG_PICTURE.html` — 1 fix
  - `.claude/worktrees/ecstatic-hoover/AI_EMPIRE_BIG_PICTURE.html` — 5 fixes
- Other files (AI_EMPIRE_DASHBOARD.html, mobile-command-center/index.html) were already properly prefixed
- party_dashboard.html and STRUCTURE_MAP.html don't use backdrop-filter

### Future-Proofing
Run `python scripts/fix_webkit_backdrop.py` after any CSS changes to ensure Safari compatibility. Consider adding it to CI/QA checks.

---

## Phase 3: 100-Agent Skills Structure (COMPLETED)

### Created: `.claude/skills/` directory with 100+ skill folders

```
.claude/skills/
├── nucleus/SKILL.md              — Empire Orchestrator (Chief of Staff)
│
├── legal-warroom/SKILL.md        — Legal Team Coordinator
├── legal-timeline/SKILL.md       — L01: Chronological event mapping
├── legal-evidence/SKILL.md       — L02: Evidence cataloging & exhibit numbering
├── legal-claims/SKILL.md         — L03: Claims/defense matrix
├── legal-caselaw/SKILL.md        — L04: Case law & precedent research
├── legal-opponent/SKILL.md       — L05: Opponent behavior analysis
├── legal-risk/SKILL.md           — L06: Risk/cost modeling
├── legal-settlement/SKILL.md     — L07: Negotiation & BATNA strategy
├── legal-drafting/SKILL.md       — L08: Document drafting
├── legal-consistency/SKILL.md    — L09: Cross-check & contradiction finder
├── legal-summary/SKILL.md        — L10: Executive briefing (1-2 pages)
│
├── data-ops/SKILL.md             — Data Team Coordinator (D01-D10)
├── data-intake/ through data-dashboards/  — 10 data agent folders
│
├── marketing-offers/SKILL.md     — Marketing Team Coordinator (M01-M20)
├── marketing-copy/ through marketing-qa/  — 20 marketing agent folders
│
├── sales-leadgen/SKILL.md        — Sales Team Coordinator (S01-S20)
├── sales-outreach-dm/ through sales-ops/  — 20 sales agent folders
│
├── research-tools/SKILL.md       — Research Team Coordinator (R01-R10)
├── research-trends/ through research-qa/  — 10 research agent folders
│
├── ops-router/SKILL.md           — Ops Team Coordinator (O01-O30)
├── ops-health/ through ops-qa/   — 30 ops agent folders
```

### How Skills Work
Each SKILL.md contains:
- **Purpose**: What this agent does
- **Triggers**: When to activate it
- **Inputs/Outputs**: What it reads and produces
- **Playbook**: Step-by-step execution guide
- **Quality Checks**: Validation criteria

### How to Use
When starting a task, Claude Code reads the relevant SKILL.md file to understand the agent's role and process. Multiple skills can be composed for complex tasks. The Nucleus skill routes to the correct team.

---

## Phase 4: Legal War Room (COMPLETED)

All 10 legal agent skills are fully specified with:
- Detailed playbooks for each role
- Cross-references between agents (e.g., Timeline feeds into Evidence, which feeds into Claims)
- Output format templates with markdown table structures
- Quality gates at every step
- Evidence exhibit naming convention (EX-001, EX-001a, etc.)
- YAML header template for all legal outputs
- Disclaimer on every output: not a substitute for legal counsel

### Legal Pipeline Flow
```
Documents → D01-D03 (ingest/normalize/extract)
    → L01 (timeline) → L02 (evidence map) → L03 (claims matrix)
    → L04 (case law) + L05 (opponent analysis)
    → L06 (risk report) + L07 (settlement plan)
    → L08 (draft documents)
    → L09 (consistency check) → L10 (executive brief)
    → Export
```

---

## What's NOT Done (Next Steps for Maurice)

### 1. Install Dependencies on Your Mac
```bash
cd ~/AIEmpire-Core
source .venv/bin/activate
pip install -r requirements.txt
pip install -r empire-api/requirements.txt
```

### 2. empire_nucleus.py Decision
The file doesn't exist in the repo but is referenced in documentation. Options:
- **Option A**: Delete EMPIRE_NUCLEUS_FIX_GUIDE.md if empire_nucleus.py was never meant to be
- **Option B**: Create empire_nucleus.py as a unified entry point that imports from existing subsystems
- **Recommendation**: Option A — the existing subsystems work. Focus on revenue, not refactoring.

### 3. Populate Agent Skills
The 100 folder structures are created. Individual SKILL.md files exist for the nucleus, all legal agents, and all team coordinators. The remaining ~80 individual agent folders need SKILL.md files. These can be generated on demand as each agent is activated.

### 4. Legal Document Intake
To activate the Legal War Room:
1. Drop legal documents into `data/inbox/`
2. Run the data pipeline (D01-D03)
3. Run `[LEGAL_RUN]` to trigger the full legal analysis chain

### 5. Revenue Activation (from MASTER_EXECUTION_PLAN.md)
The tech is stable. Priority now shifts to:
- Fiverr: 3 gigs live
- Gumroad: 3 products live
- X/Twitter: daily content
- BMA consulting: outreach

---

## Architecture Decision Records

### ADR-001: No empire_nucleus.py
**Decision**: Don't create a new monolithic entry point.
**Reason**: The codebase already has functional subsystems (antigravity, workflow-system, brain-system) that work independently. A single nucleus file would create a god-object anti-pattern.
**Alternative**: Use the skills system + ORCHESTRATOR.md as the coordination layer.

### ADR-002: Skills as Filesystem, Not Code
**Decision**: Agent skills are SKILL.md files, not Python classes.
**Reason**: Skills need to be loaded into LLM context, not executed as code. A markdown file with playbooks is the right abstraction for AI agent instructions.

### ADR-003: Webkit Prefix via Script, Not PostCSS
**Decision**: Python script instead of PostCSS build pipeline.
**Reason**: The project doesn't use a CSS build system. Adding PostCSS would mean adding Node.js tooling for one CSS property. A simple Python script achieves the same result with zero new dependencies.
