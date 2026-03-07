# L01: LEGAL TIMELINE BUILDER

## Purpose
Extracts all dates, events, and actors from legal documents and constructs a chronological master timeline with source citations.

## Triggers
- New legal documents ingested
- `[LEGAL_RUN]` command (Phase 2)
- Request for chronological analysis

## Inputs
- Processed documents from `data/processed/`
- Existing timeline from `legal/timeline/TIMELINE.md` (if updating)

## Output
`legal/timeline/TIMELINE.md`

## Playbook
1. **Scan** every processed document for dates (explicit and implicit)
2. **Extract** for each date: Event description, Actors involved, Source (file + page/section)
3. **Sort** chronologically
4. **Identify gaps**: Mark periods >30 days with no documentation as `[GAP]`
5. **Cross-reference**: Link events to evidence exhibits where available
6. **Format** as markdown table:

```markdown
| Date | Event | Actors | Source | Exhibit |
|------|-------|--------|--------|---------|
| 2024-01-15 | Contract signed | Maurice, Firma X | contract.pdf p.1 | EX-001 |
| 2024-03-01 | First complaint | Maurice → Firma X | email_20240301.pdf | EX-003 |
| [GAP] | No documentation from 2024-03-02 to 2024-05-14 | — | — | — |
```

## Quality Checks
- Every event MUST have a source reference
- Dates must be in ISO format (YYYY-MM-DD)
- Gaps must be explicitly marked
- Actors must use consistent naming throughout
