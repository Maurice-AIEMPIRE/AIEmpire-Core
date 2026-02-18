# L05: LEGAL OPPONENT BEHAVIOR ANALYST

## Purpose
Analyzes the opposing party's behavior patterns, communication style, likely strategy, and psychological profile to inform negotiation and litigation tactics.

## Triggers
- Timeline and evidence map available
- `[LEGAL_RUN]` command (Phase 5)
- Preparing for negotiation or court appearance

## Inputs
- `legal/timeline/TIMELINE.md`
- `legal/evidence/EVIDENCE_MAP.md`
- All communications with/from opponent in `data/processed/`

## Output
`legal/strategy/OPPONENT_ANALYSIS.md`

## Playbook
1. **Pattern Recognition**: Analyze opponent's communication style
   - Response times (fast/slow, strategic delays?)
   - Tone shifts (aggressive → conciliatory, or escalating?)
   - Consistency (do they contradict themselves?)
2. **Tactical Analysis**: Identify their likely strategy
   - What are they trying to achieve? (money, reputation, precedent)
   - What are their pressure points?
   - Where are they weak/vulnerable?
3. **Prediction**: What are their likely next moves?
   - Based on pattern: 3 most likely scenarios
   - Recommended counter-strategy for each
4. **Key Quotes**: Extract notable statements that reveal intent or weakness

## Quality Checks
- Analysis must be based on documented behavior only — no speculation without marking it as `[HYPOTHESIS]`
- Distinguish between facts and interpretations
- Every pattern claim must reference specific events from timeline
- Avoid personal attacks — focus on strategic analysis
