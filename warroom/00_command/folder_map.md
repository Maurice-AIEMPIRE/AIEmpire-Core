---
title: WARROOM FOLDER MAP
agent: Orchestrator
team: Command
created_at: 2026-02-10T10:00:00Z
inputs: [ORCHESTRATOR.md, agents.json]
confidence: high
---

# FOLDER MAP — How Warroom Connects to Work Folders

## Architecture

```
AIEmpire-Core/
├── warroom/                    # COMMAND & CONTROL (strategy, status, rules)
│   ├── 00_command/             # Mission brief, status board, objectives
│   ├── 00_nucleus/             # Squad definitions, routing, rules (EXISTING)
│   ├── 01_intake/              # Raw uploads + manifests
│   │   ├── uploads/            # Drop files here for processing
│   │   └── manifests/          # Auto-generated inventories
│   ├── 02_legal/               # Legal warroom overflow/scratch
│   ├── 03_data_ops/            # Data ops scratch
│   ├── 04_marketing_growth/    # Marketing scratch
│   ├── 05_sales/               # Sales scratch
│   ├── 06_engineering/         # Engineering scratch
│   └── 07_outputs/             # Final bundled exports
│       ├── pdf/
│       ├── docx/
│       ├── slides/
│       └── md/
│
├── data/                       # DATA OPS WORK (D01-D10)
│   ├── inbox/                  # Raw files land here
│   ├── processed/              # Normalized, tagged, deduped
│   ├── index/                  # Search index, embeddings
│   └── exports/                # Bundled exports
│
├── legal/                      # LEGAL WARROOM WORK (L01-L10)
│   ├── timeline/               # L01: TIMELINE.md
│   ├── evidence/               # L02: EVIDENCE_MAP.md
│   ├── claims/                 # L03: CLAIM_MATRIX.md
│   ├── drafts/                 # L08: Schriftsatz/Mail/Memo drafts
│   ├── strategy/               # L05-L07: Opponent, Risk, Settlement
│   └── memos/                  # L04,L09,L10: Case law, consistency, exec brief
│
├── marketing/                  # MARKETING WORK (M01-M20)
│   ├── offers/                 # M01,M08,M13,M17: Offers, positioning, magnets
│   ├── copy/                   # M02,M03,M10,M14,M16: Landing, email, UX
│   ├── seo/                    # M04: SEO cluster plan
│   ├── content/                # M05,M07,M09,M11,M12,M15,M18,M19,M20: Batch content
│   └── funnels/                # M06: Funnel blueprints
│
├── sales/                      # SALES WORK (S01-S20)
│   ├── leads/                  # S01,S18: Lead sources, territory
│   ├── outreach/               # S02,S03,S08,S12: DM, email, followup, referral
│   ├── scripts/                # S04-S07,S09,S10,S13-S14,S16-S17: Calls, proposals
│   └── crm/                    # S06,S11,S15,S19,S20: Pipeline, accounts, forecast
│
├── ops/                        # OPS/ENGINEERING WORK (O01-O30)
│   ├── configs/                # O01,O05-O06,O08-O09,O11-O19,O21-O24,O29: All configs
│   ├── health/                 # O02,O25: Health, telemetry
│   ├── logs/                   # O07: Logging
│   └── skills/                 # O04,R01: Skill templates, tools tracker
│
└── blueprints/                 # RESEARCH + TEMPLATES (R01-R10, O22,O26)
    └── playbooks/              # Automation workflows, prompt library
```

## Flow: Intake to Output

```
warroom/01_intake/uploads/  →  data/inbox/  →  data/processed/  →  legal/ | marketing/ | sales/
                                                                            ↓
                                                                  warroom/07_outputs/
```

1. Files arrive in `warroom/01_intake/uploads/` or `data/inbox/`
2. D01-D10 process them into `data/processed/`
3. Squads consume processed data and produce deliverables in their work folders
4. Final exports go to `warroom/07_outputs/` or `data/exports/`

## Next Actions
1. Ensure `data/inbox/` has legal documents for processing
2. Run file inventory to populate `warroom/01_intake/manifests/`
3. Begin squad deliverables in work folders
