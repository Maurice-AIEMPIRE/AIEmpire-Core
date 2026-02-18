# LEGAL WARROOM — Team Coordinator

## Purpose
Coordinates the 10 legal specialist agents (L01-L10) to produce a complete, export-ready legal work product from raw documents. Manages the pipeline: intake → timeline → evidence → claims → strategy → drafts → QA → export.

## Triggers
- `[LEGAL_RUN]` command
- Any task involving: Rechtsstreit, Klage, Beweis, Anwalt, Gericht, Verteidigung, Vergleich
- New files in `data/inbox/` tagged as legal
- User requests for legal analysis, timeline, evidence mapping

## Inputs
- Raw documents in `data/inbox/` (PDFs, emails, screenshots, contracts)
- Prior legal outputs in `legal/` subdirectories
- `agents.json` entries for L01-L10

## Outputs (mandatory deliverables)
1. `legal/timeline/TIMELINE.md` — Master chronology
2. `legal/evidence/EVIDENCE_MAP.md` — Evidence index with chain of custody
3. `legal/claims/CLAIM_MATRIX.md` — Claims, defenses, evidence links, risk scores
4. `legal/strategy/OPPONENT_ANALYSIS.md` — Opposing party behavior patterns
5. `legal/strategy/RISK_REPORT.md` — Best/worst case scenarios with probabilities
6. `legal/strategy/SETTLEMENT_PLAN.md` — Negotiation strategy + BATNA
7. `legal/drafts/` — Letters, motions, memos as needed
8. `legal/memos/CONSISTENCY_REPORT.md` — Cross-check timeline vs evidence vs claims
9. `legal/memos/EXEC_BRIEF.md` — 1-2 page executive summary

## Playbook

### Phase 1: Data Ingest (D01 + D02 + D03)
1. Inventory all files in `data/inbox/`
2. OCR any image-based documents
3. Normalize naming: `YYYY-MM-DD_TYPE_DESCRIPTION.ext`
4. Move processed files to `data/processed/`

### Phase 2: Timeline (L01 - Legal_Timeline)
1. Extract all dates, events, actors from processed documents
2. Build chronological timeline with source references
3. Flag gaps: periods with no documentation
4. Output: `legal/timeline/TIMELINE.md`

### Phase 3: Evidence Mapping (L02 - Legal_EvidenceMapper)
1. For each document, identify: what it proves, who it involves, relevance level
2. Create evidence chain: Document → Fact → Legal Claim
3. Apply exhibit naming: `EX-001`, `EX-002`, ...
4. Output: `legal/evidence/EVIDENCE_MAP.md`

### Phase 4: Claims Matrix (L03 - Legal_ClaimsMatrix)
1. List all potential claims (yours AND opponent's)
2. For each claim: supporting evidence, risk level (1-5), strength assessment
3. Map defenses and counter-arguments
4. Output: `legal/claims/CLAIM_MATRIX.md`

### Phase 5: Strategy (L05 + L06 + L07)
1. Opponent analysis: patterns, likely moves, weaknesses
2. Risk assessment: best/worst/likely scenarios with probability %
3. Settlement strategy: your BATNA, their BATNA, zone of agreement
4. Outputs in `legal/strategy/`

### Phase 6: Drafts (L08 - Legal_Drafting)
1. Draft any requested documents (letters, motions, responses)
2. Reference timeline + evidence map in footnotes
3. Output in `legal/drafts/`

### Phase 7: QA (L09 + L10)
1. Cross-check: Do all timeline events have evidence? Do all claims have support?
2. Consistency check: No contradictions between documents
3. Executive brief: 1-2 page summary for decision-maker
4. Outputs: `legal/memos/CONSISTENCY_REPORT.md`, `legal/memos/EXEC_BRIEF.md`

## Safety & Quality Checks
- Every factual claim MUST reference source document + page/section
- Mark uncertain items as `[UNVERIFIED]` with confidence level
- This system does NOT replace legal counsel — note this in every output header
- Never fabricate evidence or dates
- Flag any document that might be privileged (attorney-client communication)

## Exhibit Naming Convention
```
EX-001  First exhibit (chronological order of relevance)
EX-001a Supplement to EX-001
EX-002  Second exhibit
```

## YAML Header Template (for all legal outputs)
```yaml
---
title: <Document Title>
agent: <L01-L10 Agent Name>
team: Legal
created_at: <ISO8601>
inputs: [<source files used>]
confidence: <low|medium|high>
case_ref: <Case identifier if applicable>
---
```
