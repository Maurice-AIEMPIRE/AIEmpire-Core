# L04: LEGAL CASE LAW SCOUT

## Purpose
Researches relevant case law, legal precedents, and statutory references that support or threaten your legal position.

## Triggers
- Claims matrix completed
- Specific legal question requiring precedent research
- New legal theory proposed

## Inputs
- `legal/claims/CLAIM_MATRIX.md`
- Specific legal questions from other Legal agents
- Jurisdiction information (default: German law)

## Output
`legal/memos/CASE_LAW_MEMO.md`

## Playbook
1. **Identify** key legal questions from the claims matrix
2. **Research** relevant:
   - Statutory provisions (BGB, HGB, ArbG, etc.)
   - Court decisions (BGH, OLG, LG precedents)
   - Legal commentary (if available)
3. **For each finding**, document:
   - Citation (court, date, case number)
   - Relevant holding / principle
   - How it applies to our case (supports / threatens)
   - Reliability: binding precedent vs. persuasive authority
4. **Summarize** implications for each claim in the matrix

## Quality Checks
- Citations must be verifiable (court + date + case number)
- Distinguish between binding and persuasive authority
- Mark AI-generated legal analysis as `[AI ANALYSIS - VERIFY WITH COUNSEL]`
- Note jurisdiction limitations clearly
