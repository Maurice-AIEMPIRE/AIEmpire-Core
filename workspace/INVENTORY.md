# AIEmpire Asset Inventory

**Last Updated:** 2026-02-19
**Owner:** Maurice Pfeifer
**Repository:** AIEmpire-Core

---

## Agent Teams (100 agents across 6 teams)

Source: `agents.json`

### LEGAL_WARROOM (10 agents)
| ID  | Name                  | Scope                                          |
|-----|-----------------------|------------------------------------------------|
| L01 | Legal_Timeline        | Chronologie, datierte Ereigniskette            |
| L02 | Legal_EvidenceMapper  | Beweisstücke -> Behauptungen -> Fundstellen    |
| L03 | Legal_ClaimsMatrix    | Ansprüche/Einwände/Beweis/Risiko               |
| L04 | Legal_CaseLawScout    | Relevante Rechtsprechung/Normen recherchieren  |
| L05 | Legal_OpponentAnalysis| Gegenseite: Argumentmuster, Widersprüche       |
| L06 | Legal_RiskOfficer     | Worst-case/Best-case, Kosten, Prozessrisiken   |
| L07 | Legal_Settlement      | Vergleichsvorschläge, Verhandlungspunkte, BATNA|
| L08 | Legal_Drafting        | Entwürfe: Schriftsätze/Mails/Memos             |
| L09 | Legal_Consistency     | Konsistenzcheck: Timeline vs. Evidence vs. Claims |
| L10 | Legal_SummaryExec     | Executive Briefing (1-2 Seiten) für Anwalt     |

### DATA_OPS (10 agents)
| ID  | Name                  | Scope                                          |
|-----|-----------------------|------------------------------------------------|
| D01 | Data_Intake           | Dateien aufnehmen, Inventar führen             |
| D02 | Data_NormalizeNaming  | Benennungsstandard, Ordnerlogik                |
| D03 | Data_OCRExtract       | Text aus PDFs/Bildern extrahieren              |
| D04 | Data_Dedupe           | Duplikate erkennen/entfernen                   |
| D05 | Data_Tagging          | Tags/Entities/Dates extrahieren                |
| D06 | Data_Indexer          | Suchindex/Embeddings                           |
| D07 | Data_CrossLink        | Zusammenhänge verknüpfen                       |
| D08 | Data_QA               | Qualitätscheck Extraktion/Tags                 |
| D09 | Data_ExportManager    | Exports bündeln (MD/PDF/ZIP)                   |
| D10 | Data_Dashboards       | Übersichten/Tabellen/Status                    |

### MARKETING (20 agents)
| ID  | Name                  | Scope                                          |
|-----|-----------------------|------------------------------------------------|
| M01 | Offer_Architect       | Offer Ladder, Preislogik, Value Props          |
| M02 | Copy_Longform         | Landingpages/Salespages                        |
| M03 | Copy_Email            | Email-Sequenzen                                |
| M04 | SEO_Strategist        | Cluster, Keywords, Content Plan                |
| M05 | Content_Batch         | Posts/Threads/Reels Scripts                    |
| M06 | Funnel_Builder        | Lead Magnet -> Tripwire -> Upsell              |
| M07 | Analytics_Growth      | KPIs, Tracking, Experimente                    |
| M08 | Brand_Positioning     | Positionierung, Messaging, ICP                 |
| M09 | Ad_Creatives          | Anzeigen Hooks/Angles                          |
| M10 | Newsletter_Editor     | Weekly Newsletter Template                     |
| M11 | Hook_Lab              | 100 Hooks/Angles                               |
| M12 | CaseStudy_Writer      | Case Studies, Social Proof                     |
| M13 | LeadMagnet_Author     | Audit/Scorecards/Guides                        |
| M14 | Webinar_Script        | Webinar Outline + Pitch                        |
| M15 | PR_Comms              | Presse/Partnerschaften/Outreach                |
| M16 | UX_Copy               | Checkout/Onboarding Copy                       |
| M17 | Competitor_Analyst    | Wettbewerber, Preis, Position                  |
| M18 | Community_Manager     | Community Loops, Engagement                    |
| M19 | Repurposing_Engine    | Long->Short Content                            |
| M20 | Marketing_QA          | Qualitätscheck Tone/Clarity/Claims             |

### SALES (20 agents)
| ID  | Name                  | Scope                                          |
|-----|-----------------------|------------------------------------------------|
| S01 | Lead_Gen              | Leadquellen, Listen, Prospecting               |
| S02 | Outreach_DM           | DM-Sequenzen                                   |
| S03 | Outreach_Email        | Cold Email                                     |
| S04 | Call_Discovery        | Discovery Call Script                          |
| S05 | Objection_Handler     | Einwände, Antworten                            |
| S06 | CRM_Pipeline          | Pipeline Stages, Follow-ups                    |
| S07 | Proposal_Writer       | Angebote/Proposals                             |
| S08 | Followup_Engine       | Follow-up System                               |
| S09 | Pricing_Negotiator    | Preisargumentation/Verhandlung                 |
| S10 | Sales_QA              | Qualitätscheck Scripts                         |
| S11 | Account_Plans         | Key Accounts: Plan + Next Steps                |
| S12 | Referral_System       | Empfehlungen                                   |
| S13 | Demo_Story            | Demo-Struktur, Storyline                       |
| S14 | Contract_Sanity       | Vertragschecks                                 |
| S15 | Retention_Playbook    | Kundenbindung                                  |
| S16 | Upsell_Crosssell      | Upsell Logik                                   |
| S17 | Sales_Enablement      | Onepagers, Battlecards                         |
| S18 | Territory_Mapper      | Region/Branche Mapping                         |
| S19 | Inbound_Qualifier     | Qualifizierung                                 |
| S20 | Sales_Ops             | Reporting/Forecast                             |

### RESEARCH (10 agents)
| ID  | Name                  | Scope                                          |
|-----|-----------------------|------------------------------------------------|
| R01 | Tools_Tracker         | Tools/Agents/Models Updates                    |
| R02 | Trend_Scout           | Trends, Content Angles                         |
| R03 | Competitive_Intel     | Markt/Wettbewerb                               |
| R04 | Tech_Research         | MCP/Skills/Infra Patterns                      |
| R05 | Model_Bench           | Model Tests/Router Empfehlungen                |
| R06 | Prompt_Engineer       | Master Prompts, Prompt Libraries               |
| R07 | Workflow_Designer     | n8n/Zapier/Make Workflows                      |
| R08 | Knowledge_Architect   | KB Struktur, Naming, Retrieval                 |
| R09 | Security_Privacy      | Privacy, Keys, Threat model                    |
| R10 | Research_QA           | Quellen/Validität prüfen                       |

### OPS_ENGINEERING (30 agents)
| ID  | Name                  | Scope                                          |
|-----|-----------------------|------------------------------------------------|
| O01 | Router_Engineer       | Provider Routing (local/cloud/budget)          |
| O02 | Health_Monitor        | CPU/RAM/Throttle                               |
| O03 | Night_Run_Manager     | Overnight runs, scheduling                     |
| O04 | Skill_Builder         | Skills scaffolding + templates                 |
| O05 | MCP_Integrator        | MCP servers/tools wiring                       |
| O06 | CI_QA                 | Tests, lint, smoke checks                      |
| O07 | Logging_Observer      | Logs, metrics, alerts                          |
| O08 | Secrets_Manager       | Keys/Env/Rotation                              |
| O09 | Storage_Manager       | Folder rules, archiving                        |
| O10 | Export_Pipeline       | MD->PDF/DOCX bundling                          |
| O11 | Local_ModelOps        | Ollama models, profiles, performance           |
| O12 | Cloud_Providers       | OpenRouter/Groq/Moonshot config                |
| O13 | RateLimit_Manager     | Backoff, queues, retries                       |
| O14 | Agent_Scheduler       | Queues, priorities, orchestration              |
| O15 | Doc_Generator         | Auto docs from outputs                         |
| O16 | Repo_Structure        | Repo cleanup, conventions                      |
| O17 | Python_Runtime        | venv, deps, packaging                          |
| O18 | Node_Runtime          | node toolchain, n8n, etc.                      |
| O19 | Docker_Operator       | Docker compose/containers                      |
| O20 | Backups               | Backup/restore strategy                        |
| O21 | QA_Gatekeeper         | Output Gate checks                             |
| O22 | Template_Registry     | Templates registry                             |
| O23 | CLI_Toolsmith         | CLI commands wrappers                          |
| O24 | WebUI_Dashboard       | Mission control dashboard                      |
| O25 | Telemetry             | Metrics + cost tracking                        |
| O26 | Prompt_Store          | Prompt bank, versioning                        |
| O27 | Legal_Data_Bridge     | Legal outputs <-> data index sync              |
| O28 | Content_Pipeline      | Batch production machine                       |
| O29 | Safety_Compliance     | Policy guardrails                              |
| O30 | Ops_QA                | Ops review, integration tests                  |

---

## Content Assets

### Products (Publish-Ready Digital Products)

#### 1. BMA Checklisten-Pack (9 files)
Location: `products/bma-checklisten-pack/`
| File | Description |
|------|-------------|
| 01_Inbetriebnahme_Protokoll.md  | Commissioning protocol              |
| 02_Wartungs_Checkliste_DIN14675.md | Maintenance checklist (DIN 14675) |
| 03_Abnahme_Protokoll.md         | Acceptance protocol                 |
| 04_Uebergabe_Protokoll.md       | Handover protocol                   |
| 05_Stoerungsdokumentation.md    | Fault documentation                 |
| 06_Melder_Pruefung_Esser.md     | Detector testing (Esser)            |
| 07_Melder_Pruefung_Hekatron.md  | Detector testing (Hekatron)         |
| 08_Feuerwehr_Schnittstelle.md   | Fire department interface           |
| 09_Risikobewertung.md           | Risk assessment                     |

#### 2. AI Setup Blueprint (4 files)
Location: `products/AI_Setup_Blueprint/`
| File | Description |
|------|-------------|
| 01_introduction_to_local_ai.md    | Intro to running AI locally      |
| 02_installing_ollama_python.md    | Ollama + Python setup guide      |
| 03_your_first_agent_script.md     | First agent tutorial             |
| 04_bonus_automation_ideas.md      | Automation ideas & next steps    |

#### 3. Automated Cashflow (5 files)
Location: `products/Automated_Cashflow/`
| File | Description |
|------|-------------|
| 01_n8n_basics_masterclass.md      | n8n workflow basics              |
| 02_connecting_stripe_paypal.md    | Payment processor integration    |
| 03_the_perfect_sales_funnel.md    | Sales funnel design              |
| 04_automating_dm_sales.md         | DM sales automation              |
| 05_scaling_to_10k.md              | Scaling to 10K EUR/month         |

#### 4. Viral Velocity (5 files)
Location: `products/Viral_Velocity/`
| File | Description |
|------|-------------|
| 01_the_algorithm_secrets.md          | Platform algorithm breakdown   |
| 02_automating_tweets_with_python.md  | Twitter automation scripts     |
| 03_the_reply_guy_strategy.md         | Engagement growth strategy     |
| 04_visuals_that_convert.md           | Visual content that converts   |
| 05_launching_your_growth_engine.md   | Growth engine playbook         |

### X/Twitter Lead Machine Content
Location: `x_lead_machine/`
- `READY_TO_POST.md` - Queued posts ready to publish
- `EXTRA_POSTS.md` - Additional post bank
- `GOLD_30_AUTOMATIONS.md` - 30 automation thread ideas
- `week_content_20260208.md` - Weekly content calendar
- `trending_now.md` - Current trending topics
- `post_generator.py` - Automated post generation
- `viral_reply_generator.py` - Reply engagement bot
- `x_automation.py` - Full X automation pipeline
- `generate_week.py` - Weekly content batch generator

### Gold Nuggets (15 Business Intelligence Documents)
Location: `gold-nuggets/`
- MONETIZATION_REPORT_2026-02-08.md
- GOLD_OPENCLAW_MASTERPLAN_2026-02-08.md
- GOLD_REDPLANET_MEMORY_AGENT_2026-02-08.md
- GOLD_NOTEBOOKLM_OPENCLAW_2026-02-08.md
- GOLD_KIMI_AGENT_SWARM_2026-02-08.md
- GOLD_VISION_SCAN_2026-02-08.md
- GOLD_AI_EMPIRE_APP_2026-02-08.md
- GOLD_OPENCLAW_ECOSYSTEM_2026-02-08.md
- GOLD_AI_FRAMEWORKS_2026-02-08.md
- GOLD_KIMI_SWARM_20260208.md
- GOLD_DEXTER_FINANCE_AI_2026-02-08.md
- GOLD_VIDEO_CONTENT_PIPELINE_2026-02-08.md
- GOLD_ELITE_SYSTEM_PROMPT_2026-02-08.md
- GITHUB_GOLD_NUGGETS.md
- INDEX.md

---

## Technical Stack Summary

| Component          | Technology                | Location                    |
|--------------------|---------------------------|-----------------------------|
| Core Engine        | Python 3 (asyncio)        | `empire_engine.py`          |
| Antigravity System | 26 Python modules         | `antigravity/`              |
| Model Router       | Ollama/Kimi/Claude        | `antigravity/unified_router.py` |
| Brain System       | 7 AI Brains               | `brain_system/`             |
| Workflow Engine    | Orchestrator + Cowork     | `workflow_system/`          |
| Gemini Mirror      | Dual-Brain (Kimi+Gemini)  | `gemini-mirror/`            |
| Kimi Swarm         | 100K/500K agents          | `kimi_swarm/`               |
| Atomic Reactor     | YAML tasks + FastAPI      | `atomic_reactor/`           |
| CRM                | Express.js + SQLite       | `crm/`                      |
| Revenue Machine    | Pipeline automation       | `revenue_machine/`          |
| X Lead Machine     | Content + viral replies   | `x_lead_machine/`           |
| OpenClaw Config    | Agents + Cron + Models    | `openclaw-config/`          |
| Auto-Repair        | Self-healing scripts      | `scripts/auto_repair.py`    |
| Bombproof Startup  | LaunchAgent + 5 Phases    | `scripts/bombproof_startup.sh` |
| War Room           | Command center            | `warroom/`                  |
| Mirror System      | Cloud sync + product factory | `mirror-system/`         |

---

## Revenue Potential Matrix

| Product                    | Price  | Target Sales/Mo | Monthly Rev | Annual Rev  | Effort to Launch |
|----------------------------|--------|-----------------|-------------|-------------|------------------|
| BMA Checklisten-Pack       | 27 EUR | 10              | 270 EUR     | 3,240 EUR   | LOW (ready)      |
| AI Agent Starter Kit       | 49 EUR | 15              | 735 EUR     | 8,820 EUR   | LOW (ready)      |
| AI Automation Blueprint    | 79 EUR | 5               | 395 EUR     | 4,740 EUR   | LOW (ready)      |
| BMA Video-Schulungspaket   | 47 EUR | 8               | 376 EUR     | 4,512 EUR   | MEDIUM           |
| BMA Troubleshooting-Kompass| 37 EUR | 8               | 296 EUR     | 3,552 EUR   | LOW (ready)      |
| AI Side Hustle Playbook    | 97 EUR | 5               | 485 EUR     | 5,820 EUR   | MEDIUM           |
| AI Automation Setup Basic  | 30 EUR | 10              | 300 EUR     | 3,600 EUR   | MEDIUM           |
| Agent Builders Club        | 29/mo  | 50              | 1,450 EUR   | 17,400 EUR  | MEDIUM           |
| Fiverr/Upwork AI Services  | 50-5K  | varies          | 5,000 EUR   | 60,000 EUR  | HIGH             |
| BMA + AI Consulting        | 2-10K  | 2               | 5,000 EUR   | 60,000 EUR  | HIGH             |
| **TOTAL POTENTIAL**        |        |                 | **14,307**  | **171,684** |                  |

---

## Stripe Products (Already Configured)

14 products live on Stripe (test mode):
- BMA Profi-Checklisten Pack (27 EUR)
- BMA Video-Schulungspaket (47 EUR)
- BMA Troubleshooting-Kompass (37 EUR)
- AI Agent Blueprint - Starter (47 EUR)
- AI Side Hustle Playbook (97 EUR)
- AI Automation Setup Basic/Standard/Premium (30/150/500 EUR)
- BMA Expert Consulting Basic/Standard/Premium (200/750/2000 EUR)
- Custom AI Agent Basic/Standard/Premium (500/2000/5000 EUR)

---

*Generated: 2026-02-19 | Source: AIEmpire-Core repository analysis*
