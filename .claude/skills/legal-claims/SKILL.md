# L03: LEGAL CLAIMS/DEFENSE MATRIX ANALYST

## Purpose
Builds the master claims matrix: every legal claim (yours and opponent's), supporting evidence, risk assessment, and recommended next actions.

## Triggers
- Timeline and evidence map completed
- `[LEGAL_RUN]` command (Phase 4)
- Request for claims analysis or risk assessment

## Inputs
- `legal/timeline/TIMELINE.md`
- `legal/evidence/EVIDENCE_MAP.md`
- Original documents from `data/processed/`

## Output
`legal/claims/CLAIM_MATRIX.md`

## Playbook
1. **Identify** all potential claims:
   - Your claims against opponent (offensive)
   - Opponent's likely claims against you (defensive)
   - Third-party claims (if applicable)
2. **For each claim**, document:
   - Legal basis (which law, regulation, or contract clause)
   - Supporting evidence (exhibit references)
   - Counter-evidence (what weakens this claim)
   - Risk level: 1 (very low) to 5 (critical)
   - Strength: Strong / Medium / Weak
   - Recommended action: Pursue / Defend / Settle / Drop
3. **Link** to timeline events and evidence exhibits
4. **Prioritize** by risk × impact

```markdown
## YOUR CLAIMS (Offensive)

| ID | Claim | Legal Basis | Evidence | Risk | Strength | Action |
|----|-------|-------------|----------|------|----------|--------|
| C-01 | Breach of contract | §433 BGB | EX-001, EX-005 | 2 | Strong | Pursue |
| C-02 | Damages (lost revenue) | §280 BGB | EX-003, EX-007 | 3 | Medium | Pursue with caution |

## OPPONENT'S LIKELY CLAIMS (Defensive)

| ID | Claim | Legal Basis | Their Evidence | Our Defense | Risk | Action |
|----|-------|-------------|---------------|-------------|------|--------|
| D-01 | No breach occurred | §433 BGB | [UNKNOWN] | EX-001 contradicts | 2 | Defend with EX-001 |
```

## Quality Checks
- Every claim must reference at least one evidence exhibit or be marked `[NEEDS EVIDENCE]`
- Risk levels must be justified with reasoning (not arbitrary)
- Both offensive AND defensive claims must be analyzed
- German law references (BGB, HGB, etc.) must cite specific paragraphs
