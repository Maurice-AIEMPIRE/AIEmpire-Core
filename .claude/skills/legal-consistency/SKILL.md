# L09: LEGAL CONSISTENCY CHECKER

## Purpose
Cross-checks all legal outputs for internal consistency. Ensures timeline, evidence map, and claims matrix don't contradict each other. Identifies gaps and logical errors.

## Triggers
- All legal outputs completed (timeline, evidence, claims, strategy)
- `[LEGAL_RUN]` command (Phase 7)
- Before any legal export

## Inputs
- `legal/timeline/TIMELINE.md`
- `legal/evidence/EVIDENCE_MAP.md`
- `legal/claims/CLAIM_MATRIX.md`
- `legal/strategy/` (all strategy documents)
- `legal/drafts/` (all draft documents)

## Output
`legal/memos/CONSISTENCY_REPORT.md`

## Playbook
1. **Timeline ↔ Evidence Cross-Check**:
   - Does every timeline event have supporting evidence?
   - Does every evidence exhibit appear in the timeline?
   - Are dates consistent across both documents?
2. **Claims ↔ Evidence Cross-Check**:
   - Does every claim have at least one supporting exhibit?
   - Are there exhibits not linked to any claim? (potential missed arguments)
3. **Internal Logic Check**:
   - Any contradictions between documents?
   - Any dates that don't add up?
   - Any actors named differently in different documents?
4. **Completeness Check**:
   - Missing evidence flagged?
   - All claims have risk assessments?
   - Strategy covers all high-risk claims?
5. **Gap List**: Prioritized list of what's missing

```markdown
## CONSISTENCY FINDINGS

### Contradictions Found
| Issue | Document A | Document B | Severity |
|-------|-----------|-----------|----------|
| Date mismatch | TIMELINE: 2024-01-15 | EX-001: 2024-01-16 | Medium |

### Gaps Found
| Gap | Impact | Recommended Action |
|-----|--------|--------------------|
| No evidence for C-03 | Claim unsupported | Request payment records |

### Cross-Reference Verification
- Timeline events with evidence: 15/18 (83%) — 3 events lack documentation
- Claims with evidence: 4/5 (80%) — C-03 unsupported
- Exhibits linked to claims: 12/14 (86%) — EX-006, EX-011 unlinked
```

## Quality Checks
- Must check ALL documents, not just a sample
- Contradictions must be classified by severity (Critical / Medium / Low)
- Every gap must have a recommended action
- Report must include pass/fail summary
