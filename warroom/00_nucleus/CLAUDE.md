# WARROOM NUCLEUS — Squad Definitions

> Single source of truth for all squad missions, inputs, outputs, and completion criteria.
> Owner: Maurice Pfeifer | Updated: 2026-02-10

---

## How to Read This File

Every squad below follows the same schema:

```
MISSION   → What this squad exists to do (one sentence).
INPUTS    → What it consumes (files, data, commands).
OUTPUTS   → What it produces (deliverables, artifacts).
DONE-WHEN → Hard checklist — if any item is missing, the task is NOT done.
```

Cross-references to `agents.json` IDs are included where applicable.

---

## 1. MONEY MACHINE

**Agents:** M01–M20 (Marketing), S01–S20 (Sales) from `agents.json`

### Mission

Turn attention into revenue through products, funnels, email sequences, copy, content, SEO, analytics, and tooling — end to end, from first impression to paid invoice.

### Inputs

- Market/trend data from Research squad (R02, R03)
- Product specs and pricing from `marketing/offers/`
- Lead lists from `sales/leads/`
- Performance metrics from analytics dashboards
- Brand positioning from `marketing/offers/POSITIONING.md`
- Customer feedback, testimonials, case studies

### Outputs

| Category | Deliverable | Location |
|----------|-------------|----------|
| Products | Offer stack, pricing ladder, lead magnets | `marketing/offers/` |
| Funnels | Lead magnet → tripwire → core → upsell blueprints | `marketing/funnels/` |
| Email | Welcome, nurture, launch, and cart-abandon sequences | `marketing/copy/EMAIL_SEQUENCES.md` |
| Copy | Landing pages, sales pages, checkout copy, UX copy | `marketing/copy/` |
| Content | Social posts, threads, reels scripts, hooks library, case studies | `marketing/content/` |
| SEO | Keyword clusters, content plan, pillar/spoke maps | `marketing/seo/SEO_CLUSTER_PLAN.md` |
| Analytics | KPI dashboards, growth experiments, conversion tracking | `marketing/content/GROWTH_EXPERIMENTS.md` |
| Tooling | Repurposing pipeline, content batch system, ad creative bank | `marketing/content/PIPELINE.md` |
| Sales | Outreach scripts, discovery calls, proposals, battlecards, pipeline | `sales/` |

### Definition of Done

- [ ] Every deliverable has a YAML header (`title`, `agent`, `team`, `created_at`, `inputs`, `confidence`)
- [ ] Copy reviewed by Marketing_QA (M20) for tone, clarity, and claims
- [ ] Sales scripts reviewed by Sales_QA (S10)
- [ ] Funnel has a documented conversion goal and tracking plan
- [ ] Email sequences include subject lines, preview text, and CTA per step
- [ ] SEO plan maps keywords to content pieces with search volume estimates
- [ ] No placeholder text — every `[TODO]` replaced or marked `[MISSING]` with next action
- [ ] All assets are export-ready: can go to customer/partner/platform without editing

---

## 2. LEGAL WARROOM

**Agents:** L01–L10 from `agents.json`

### Mission

Build airtight, source-backed legal work products for ongoing disputes — timelines, evidence maps, claim matrices, risk assessments, settlement strategies, and draft correspondence — structured for direct handoff to counsel.

### Inputs

- Raw documents in `data/inbox/` (PDFs, emails, screenshots, contracts, correspondence)
- Processed/tagged documents from Data Room squad
- Cross-link maps from D07 (Data_CrossLink)
- Prior legal outputs for consistency checks

### Outputs

| Role | Agent | Deliverable | Location |
|------|-------|-------------|----------|
| Timeline | L01 | Chronological event chain with dated source refs | `legal/timeline/TIMELINE.md` |
| Evidence Mapper | L02 | Evidence → claim → relevance → source location | `legal/evidence/EVIDENCE_MAP.md` |
| Claims Matrix | L03 | Claim / counterclaim / evidence / risk / next action | `legal/claims/CLAIM_MATRIX.md` |
| Case Law Scout | L04 | Relevant case law and statutes (sourced only) | `legal/memos/CASE_LAW_MEMO.md` |
| Opponent Analysis | L05 | Opposing argument patterns, contradictions, attack surfaces | `legal/strategy/OPPONENT_ANALYSIS.md` |
| Risk Officer | L06 | Worst/best case, cost exposure, process risks | `legal/strategy/RISK_REPORT.md` |
| Settlement | L07 | Settlement proposals, negotiation points, BATNA | `legal/strategy/SETTLEMENT_PLAN.md` |
| Drafting | L08 | Draft briefs, emails, memos | `legal/drafts/DRAFTS_INDEX.md` |
| Consistency Check | L09 | Cross-validation: timeline vs. evidence vs. claims | `legal/memos/CONSISTENCY_REPORT.md` |
| Executive Summary | L10 | 1–2 page briefing for counsel | `legal/memos/EXEC_BRIEF.md` |

### Definition of Done

- [ ] Every factual claim cites a source document (filename + section + date)
- [ ] No hallucinated case law — every statute/ruling is verifiable or marked `[NEEDS VERIFICATION]`
- [ ] Timeline entries are chronologically ordered with no date gaps left unexplained
- [ ] Evidence map covers every document in `data/processed/` relevant to the case
- [ ] Consistency report confirms alignment across timeline, evidence map, and claims matrix
- [ ] Risk report includes quantified exposure ranges (best/worst/likely)
- [ ] All drafts marked as `DRAFT — NOT LEGAL ADVICE` in header
- [ ] Executive brief is ≤ 2 pages and actionable
- [ ] YAML header present on every output file
- [ ] Output is export-ready for counsel without further formatting

---

## 3. DATA ROOM

**Agents:** D01–D10 from `agents.json`

### Mission

Ingest raw files, normalize naming, extract text/entities, deduplicate, tag, index, cross-link, and package data for consumption by Legal Warroom, Money Machine, and Engineering squads.

### Inputs

- Raw files dropped into `data/inbox/` (PDF, DOCX, emails, screenshots, CSVs, JSON)
- Manual upload triggers or automated intake scans
- Naming conventions from `data/processed/NAMING_RULES.md`

### Outputs

| Stage | Deliverable | Location |
|-------|-------------|----------|
| Ingest | File inventory with status (inbox/processed/indexed) | `data/processed/INVENTORY.md` |
| Normalize | Renamed files following naming standard | `data/processed/` |
| Extract | OCR/text extraction log | `data/processed/OCR_LOG.md` |
| Dedupe | Duplicate/near-duplicate detection report + decision | `data/processed/DEDUPE_REPORT.md` |
| Tag | Entity/date/keyword extraction per file | `data/index/TAGS.json` |
| Index | Search index / embeddings status | `data/index/INDEX_STATUS.md` |
| Cross-link | Person ↔ date ↔ document relationship map | `data/processed/CROSSLINK_MAP.md` |
| QA | Extraction and tagging quality check | `data/processed/DATA_QA.md` |
| Export | Bundled exports (MD/PDF/ZIP) | `data/exports/` |
| Dashboard | Status overview tables | `data/processed/DASHBOARD.md` |

### Definition of Done

- [ ] Every file in `data/inbox/` has been processed or explicitly skipped with reason
- [ ] Inventory is current — no file exists in `data/processed/` without an inventory entry
- [ ] Naming follows the convention in `NAMING_RULES.md` (no spaces, no special chars, date-prefixed)
- [ ] OCR log notes extraction confidence per file (high/medium/low/failed)
- [ ] Dedupe report lists every duplicate pair with a keep/discard/merge decision
- [ ] Tags JSON validates against schema (file → tags[] → entities[] → dates[])
- [ ] Cross-link map has no orphaned nodes (every entity appears in at least one document)
- [ ] QA report confirms spot-check accuracy ≥ 90%
- [ ] Exports are self-contained (no broken internal links)
- [ ] YAML header on every output file

---

## 4. ENGINEERING

**Agents:** O01–O30 (Ops/Engineering), R04–R07 (Tech Research) from `agents.json`

### Mission

Build, maintain, and operate the technical infrastructure — OpenClaw agents, MCP integrations, n8n workflows, Python tooling, model routing, CI/QA, monitoring, and deployment — so that every other squad can run autonomously.

### Inputs

- Task requests from other squads (via orchestrator commands)
- System metrics from Resource Guard (`workflow-system/resource_guard.py`)
- Model performance benchmarks from R05 (Model_Bench)
- Infrastructure patterns from R04 (Tech_Research)
- Workflow designs from R07 (Workflow_Designer)

### Outputs

| Category | Deliverable | Location |
|----------|-------------|----------|
| OpenClaw | Agent configs, cron jobs, model routing rules | `openclaw-config/` |
| MCP | Server/tool wiring, integration configs | `ops/configs/MCP.md` |
| n8n | Workflow automation blueprints | `blueprints/AUTOMATION_WORKFLOWS.md` |
| Python Tools | Scripts, CLI wrappers, runtime configs | `scripts/`, `ops/configs/PYTHON_ENV.md` |
| Model Ops | Ollama profiles, provider configs, router logic | `ops/configs/OLLAMA.md`, `ops/configs/PROVIDERS.md`, `ops/configs/ROUTER.md` |
| CI/QA | Tests, linting, smoke checks, output gate | `ops/configs/CI.md`, `ops/configs/QA_GATE.md` |
| Monitoring | Health checks, telemetry, cost tracking, logging | `ops/health/` |
| Security | Secrets rotation, rate limits, safety compliance | `ops/configs/SECRETS.md`, `ops/configs/RATELIMITS.md`, `ops/configs/SAFETY.md` |
| Infrastructure | Docker compose, backups, storage rules | `ops/configs/DOCKER.md`, `ops/configs/BACKUPS.md`, `ops/configs/STORAGE.md` |
| Templates | Skill scaffolds, prompt bank, doc generator | `blueprints/`, `ops/skills/` |

### Definition of Done

- [ ] Code passes lint (`ruff`) and smoke tests before merge
- [ ] Every config change is version-controlled in git
- [ ] Model router defaults to local (Ollama) with documented fallback chain
- [ ] MCP integrations have connection test scripts
- [ ] n8n workflows have trigger documentation and error handling
- [ ] Health monitor reports CPU/RAM/disk within thresholds (see Resource Guard)
- [ ] Secrets are in `.env` only — zero hardcoded keys in source
- [ ] Backups follow 3-2-1 rule (3 copies, 2 media, 1 offsite)
- [ ] Every new tool/script has a one-line usage comment at top
- [ ] Ops_QA (O30) sign-off on integration tests

---

## Squad Interaction Map

```
                    ┌─────────────┐
                    │  NUCLEUS    │
                    │ (this file) │
                    └──────┬──────┘
                           │ defines
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │ DATA ROOM   │ │   LEGAL     │ │   MONEY     │
    │ D01–D10     │ │  WARROOM    │ │  MACHINE    │
    │             │ │  L01–L10    │ │ M01–M20     │
    │ ingest/tag/ │ │             │ │ S01–S20     │
    │ index/pack  │ │ timeline/   │ │             │
    └──────┬──────┘ │ evidence/   │ │ products/   │
           │        │ claims/     │ │ funnels/    │
           │feeds──►│ strategy    │ │ content/seo │
           │        └──────┬──────┘ └──────┬──────┘
           │               │               │
           └───────┬───────┴───────┬───────┘
                   │               │
            ┌──────▼──────┐        │
            │ ENGINEERING │◄───────┘
            │ O01–O30     │  powers all squads
            │ R04–R07     │
            └─────────────┘
```

Data Room feeds Legal Warroom with processed documents.
Engineering powers all squads with infrastructure and tooling.
Money Machine consumes research, content, and analytics to produce revenue.

---

## References

- `agents.json` — Full agent registry with IDs, scopes, and deliverables
- `ORCHESTRATOR.md` — Master workflow and orchestrator commands
- `warroom/00_nucleus/routing_matrix.md` — Model selection and privacy rules
- `warroom/00_nucleus/warroom_rules.md` — Operating rules and constraints

---

*This file is the warroom's operating contract. If it's not in here, it's not agreed.*
