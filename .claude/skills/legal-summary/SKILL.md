# L10: LEGAL EXECUTIVE SUMMARY

## Purpose
Distills all legal analysis into a concise 1-2 page executive briefing for the decision-maker. Written for a non-lawyer audience.

## Triggers
- Consistency check completed
- `[LEGAL_RUN]` command (Phase 7)
- Request for case overview or status update

## Inputs
- `legal/memos/CONSISTENCY_REPORT.md`
- `legal/strategy/RISK_REPORT.md`
- `legal/strategy/SETTLEMENT_PLAN.md`
- `legal/claims/CLAIM_MATRIX.md`

## Output
`legal/memos/EXEC_BRIEF.md`

## Playbook
1. **Situation** (3-5 sentences): What is this case about?
2. **Key Facts** (5-7 bullets): The most important facts, with dates
3. **Your Position**: Strengths and weaknesses in plain language
4. **Risk Assessment**: Best/worst/likely outcomes with numbers
5. **Recommendation**: What to do next (settle, litigate, or other)
6. **Immediate Actions**: Top 5 things to do this week
7. **Open Questions**: What decisions are needed from you

## Format
- Maximum 2 pages (A4)
- Plain language (no legal jargon without explanation)
- Numbers and percentages for risk/financial data
- Bold key decisions and action items

## Quality Checks
- Must be understandable by someone with no legal background
- Financial figures must match risk report
- Action items must be specific and time-bound
- Must include the disclaimer: "This analysis supports decision-making but does not constitute legal advice."
