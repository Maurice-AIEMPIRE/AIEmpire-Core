---
title: RULES OF ENGAGEMENT
agent: Orchestrator
team: Command
created_at: 2026-02-10T10:00:00Z
inputs: [warroom_rules.md, routing_matrix.md]
confidence: high
---

# RULES OF ENGAGEMENT

> Quick reference for all agents. Full details in `warroom/00_nucleus/warroom_rules.md`.

---

## DO

1. Cite sources on every factual claim (Legal: MANDATORY)
2. Use YAML header on every output file
3. Mark gaps: `[MISSING]`, `[NEEDS SOURCE]`, `[NEEDS VERIFICATION]`, `[ESTIMATED]`
4. Work in your assigned folder only
5. End every deliverable with "Next Actions" (3-7 bullets)
6. Default to LOCAL models (Ollama) for everything
7. Keep deliverables export-ready (no placeholder text)
8. Use naming convention: `UPPERCASE_WITH_UNDERSCORES.md`
9. Route cross-squad requests through orchestrator
10. Track costs on every cloud API call

## DO NOT

1. Fabricate legal claims or case law
2. Send P3 data (legal docs, personal data, API keys) to cloud
3. Overwrite another agent's deliverable
4. Create top-level directories without updating ORCHESTRATOR.md
5. Use cloud models without justification
6. Leave unmarked gaps in outputs
7. Mix languages inconsistently (EN for system, DE for legal/DACH marketing)
8. Exceed 100 EUR/month cloud budget
9. Reference Roewer GmbH in any output
10. Skip the QA gate

## ESCALATION

When blocked or out of scope:
1. Mark with `[ESCALATE: reason]`
2. Continue with what you can deliver
3. Orchestrator routes to correct squad or Maurice

Legal escalations involving real legal risk → ALWAYS to Maurice first.

## QUALITY GATE

Task is DONE only when:
- [ ] Output in correct folder
- [ ] YAML header complete
- [ ] Sources cited (Legal: mandatory)
- [ ] No unresolved `[TODO]` — only `[MISSING]` with next action
- [ ] "Next Actions" section present
- [ ] QA agent sign-off (M20/S10/O30/L09/D08)

---

*Reviewed: 2026-02-10 | Source: warroom_rules.md, routing_matrix.md*
