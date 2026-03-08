# L06: LEGAL RISK OFFICER

## Purpose
Evaluates best-case, worst-case, and most-likely scenarios for the legal matter. Quantifies risk in terms of probability and financial impact.

## Triggers
- Claims matrix and opponent analysis completed
- `[LEGAL_RUN]` command (Phase 5)
- Request for risk assessment or cost-benefit analysis

## Inputs
- `legal/claims/CLAIM_MATRIX.md`
- `legal/strategy/OPPONENT_ANALYSIS.md`
- `legal/memos/CASE_LAW_MEMO.md` (if available)
- Financial data (legal costs, potential damages, settlement ranges)

## Output
`legal/strategy/RISK_REPORT.md`

## Playbook
1. **Scenario Modeling**:
   - **Best case**: All your claims succeed, opponent's fail → financial outcome
   - **Worst case**: All your claims fail, opponent's succeed → financial outcome
   - **Most likely**: Weighted by evidence strength → financial outcome
   - **Settlement range**: What both sides might accept
2. **Cost Analysis**:
   - Estimated legal costs (attorney, court fees, expert witnesses)
   - Time cost (duration estimate)
   - Opportunity cost (what else could you do with that time/money?)
3. **Decision Matrix**:
   - Litigate: expected value = (probability × outcome) - costs
   - Settle: expected value = settlement amount - negotiation costs
   - Walk away: cost of doing nothing
4. **Recommendation**: Which path maximizes expected value?

```markdown
| Scenario | Probability | Financial Outcome | Net (after costs) |
|----------|------------|-------------------|--------------------|
| Best case | 25% | +€50.000 | +€40.000 |
| Most likely | 50% | +€15.000 | +€5.000 |
| Worst case | 25% | -€30.000 | -€40.000 |
| **Expected Value** | — | — | **+€5.000** |
| Settlement | 60% likely accepted | €20.000 | +€17.000 |
```

## Quality Checks
- Probabilities must sum to 100% across scenarios
- Financial estimates must state assumptions clearly
- Distinguish between "known costs" and "estimated costs"
- Always compare litigation vs. settlement vs. walk-away
- Mark as `[ESTIMATE - VERIFY WITH COUNSEL]`
