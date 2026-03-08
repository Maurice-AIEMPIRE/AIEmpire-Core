# SALES — Team Coordinator (S01-S20)

## Purpose
Manages the full sales pipeline: lead generation, outreach (DM + email), discovery calls, objection handling, CRM pipeline, proposals, follow-ups, pricing, accounts, referrals, demos, contracts, retention, upselling, enablement, territory mapping, inbound qualification, and sales ops.

## Triggers
- `[SALES_RUN]` command (if defined)
- New leads identified
- Request for sales assets, scripts, or pipeline analysis

## Team Structure (20 Agents)

### Lead Generation (S01, S18, S19)
- **S01 Lead_Gen**: Lead sources, prospecting lists
- **S18 Territory_Mapper**: Regional/industry territory mapping
- **S19 Inbound_Qualifier**: BANT qualification for inbound leads

### Outreach (S02, S03, S08, S12)
- **S02 Outreach_DM**: DM sequences (X/Twitter, LinkedIn)
- **S03 Outreach_Email**: Cold email campaigns
- **S08 Followup_Engine**: Automated follow-up sequences
- **S12 Referral_System**: Referral program management

### Conversion (S04, S05, S07, S09, S13)
- **S04 Call_Discovery**: Discovery call scripts and frameworks
- **S05 Objection_Handler**: Objection response library
- **S07 Proposal_Writer**: Proposals and custom offers
- **S09 Pricing_Negotiator**: Pricing strategy and negotiation tactics
- **S13 Demo_Story**: Demo structure and storytelling

### Account Management (S06, S11, S14, S15, S16)
- **S06 CRM_Pipeline**: Pipeline stages, deal tracking
- **S11 Account_Plans**: Key account management
- **S14 Contract_Sanity**: Basic contract review (non-legal)
- **S15 Retention_Playbook**: Customer retention strategies
- **S16 Upsell_Crosssell**: Upselling and cross-selling logic

### Enablement & Ops (S17, S20)
- **S17 Sales_Enablement**: Battle cards, one-pagers, competitive briefs
- **S20 Sales_Ops**: Reporting, forecasting, process optimization

### QA (S10)
- **S10 Sales_QA**: Script quality, consistency, compliance

## Output Locations
- `sales/leads/` — LEAD_SOURCES.md, TERRITORY.md
- `sales/outreach/` — DM_SCRIPTS.md, COLD_EMAILS.md, FOLLOWUPS.md, REFERRALS.md
- `sales/scripts/` — DISCOVERY_CALL.md, OBJECTIONS.md, PROPOSALS.md, NEGOTIATION.md, DEMO_STORY.md
- `sales/crm/` — PIPELINE.md, ACCOUNT_PLANS.md, RETENTION.md, QUALIFICATION.md, FORECAST.md

## Revenue Channels (from EMPIRE_BLUEPRINT)
1. Gumroad digital products (€27-€149)
2. Fiverr/Upwork AI services (€30-€5.000)
3. BMA + AI consulting (€2.000-€10.000)
4. OpenClaw Skills marketplace
5. X/Twitter content + lead generation

## Quality Gate
- All scripts must sound natural, not robotic
- Pricing must be consistent with product catalog
- Follow-up sequences must have clear timing logic
- BANT qualification must be applied to all leads
