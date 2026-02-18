# REVENUE_EXECUTION_BOARD_30D_V2

## Strategy Split
- 70% Service Cashflow: AI-Automation Setup
- 30% Shorts Autopilot

## Offer Stack (Service Track)
1. Lite (EUR 750): setup + 1 workflow + handoff doc (3 days)
2. Core (EUR 1500): setup + 3 workflows + KPI dashboard (5 days)
3. Pro (EUR 3000): setup + orchestration + monitoring + 14-day support (7 days)

## Outreach Channel
- Primary: LinkedIn + E-Mail

## Required Lead Fields
- `lead_source`
- `industry`
- `status`
- `next_action_at`
- `offer_value`

## Daily KPIs
- `new_leads`
- `first_replies`
- `calls_booked`
- `offers_sent`
- `closes`
- `cash_collected`

## Shorts Track Gate
- Publish only when OAuth/API ready and preflight decision is `run`.
- If not: write blocker reason-code and switch to degrade mode.

## Stripe Source of Truth
- `content_factory/deliverables/revenue/stripe/latest.json`

## Daily Operating Rhythm
- 07:55 precheck
- 08:00 outbound start
- 12:30 KPI checkpoint
- 18:00 closing block
- 22:30 degrade + snapshot

## KPI File Schema
- Output: `00_SYSTEM/revenue_system/kpi/daily_kpi_YYYY-MM-DD.json`
- Fields: `leads`, `replies`, `calls`, `offers`, `closes`, `cash_eur`, `published_shorts`, `runtime_incidents`
