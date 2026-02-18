# WARROOM RULES

> Hard constraints that apply to every squad, every agent, every output.
> Violations = task rejected at Output Gate (QA_Gatekeeper, O21).
> Owner: Maurice Pfeifer | Updated: 2026-02-10

---

## 1. Zero Hallucination Policy

No agent may invent facts. If data is missing, the output must contain one of these markers at the exact point of uncertainty:

- `[MISSING]` — data not found, needs manual input
- `[NEEDS SOURCE]` — claim exists but source document not identified
- `[NEEDS VERIFICATION]` — source exists but accuracy unconfirmed (especially case law)
- `[ESTIMATED]` — value is a calculated approximation, method noted inline

An output with unmarked gaps is automatically rejected.

---

## 2. Source Attribution (Legal = Mandatory, All Others = Expected)

Legal Warroom outputs: every factual claim must cite `filename + section + date`. No exceptions.

All other squads: claims based on external data should cite the source. Internal assumptions should be stated as such.

Format: `[Source: filename.pdf, §3.2, 2025-11-14]` or `[Source: URL, accessed 2026-02-10]`

---

## 3. Output Standards

Every deliverable file must include a YAML header:

```yaml
---
title: <short title>
agent: <AgentName or AgentID>
team: <Legal|Data|Money_Machine|Engineering>
created_at: <ISO8601>
inputs: [<file1>, <file2>, ...]
confidence: <low|medium|high>
---
```

Below the header, the body. At the end, a "Next Actions" section (3–7 bullet points max) describing what should happen next with this output.

---

## 4. Role Separation

Each agent delivers only its own scope as defined in `agents.json`. An agent must not overwrite or modify another agent's deliverable. If agent L01 (Timeline) spots an evidence issue, it flags it for L02 (EvidenceMapper) — it does not edit the evidence map.

Cross-squad requests go through the orchestrator, not directly between agents.

---

## 5. Privacy and Data Handling

Full rules are in `routing_matrix.md`. The non-negotiable core:

- Legal documents stay local unless Maurice explicitly authorizes cloud processing for a specific file.
- No API keys, passwords, or personal data in any output file.
- No sensitive data in git commit messages.
- Anonymize client/opposing-party names in any output that leaves the local machine.

---

## 6. Export-Ready Standard

Every output must be usable without further editing by its intended consumer:

- Legal outputs → ready for counsel review
- Marketing/sales outputs → ready for customer/platform
- Data outputs → ready for squad consumption
- Engineering outputs → ready for deployment or PR

"Export-ready" means: no broken formatting, no placeholder text (unless marked `[MISSING]`), no internal jargon unexplained, no dangling references.

---

## 7. File Placement

Outputs go in the folder specified by `agents.json` deliverables. If no folder is specified, use:

```
warroom/<squad>/<output_type>/
```

Never dump files in the repo root. Never create new top-level directories without updating `ORCHESTRATOR.md`.

---

## 8. Naming Convention

Files: `UPPERCASE_WITH_UNDERSCORES.md` for deliverables (matching existing convention).
Dated files: `YYYY-MM-DD_TITLE.md` prefix when multiple versions will exist.
No spaces, no special characters beyond underscores and hyphens.

---

## 9. Quality Gate (Output Gate)

A task is DONE only when all of the following are true:

1. Output file exists in the correct folder
2. YAML header is present and complete
3. Source citations present (mandatory for Legal, expected for others)
4. No unresolved `[TODO]` markers — only `[MISSING]` with a stated next action
5. "Next Actions" section at the end
6. Reviewed by the squad's QA agent (M20, S10, O30, L09, D08)

If any item fails, the task stays open and the QA agent files a rejection note.

---

## 10. Cost Consciousness

- Default to free/local models (Ollama) for all routine work
- Cloud API calls require justification (see `routing_matrix.md`)
- Every API call must be cost-tracked
- Budget ceiling: 100 EUR/month total across all squads
- If monthly spend exceeds 80 EUR, Engineering must throttle non-critical cloud calls

---

## 11. Hauptjob Safety

Nothing produced by this system may jeopardize Maurice's employment at Roewer GmbH. Specifically:

- No work during Roewer business hours that could create conflicts of interest
- No use of Roewer resources, contacts, or proprietary information
- No public content that references Roewer or its clients
- TikTok personas remain anonymous (no real name, no face)

---

## 12. Escalation Protocol

When an agent encounters something outside its scope or competence:

1. Mark the gap with `[ESCALATE: reason]` in the output
2. Continue with what it can deliver
3. The orchestrator routes the escalation to the appropriate squad or to Maurice directly

Legal escalations that involve real legal risk always go to Maurice before any output is finalized.

---

## 13. Versioning

Major deliverables should be versioned when updated. Append `_v2`, `_v3` etc. or use git history. Never silently overwrite a deliverable that has been reviewed or exported.

---

## 14. Communication Language

- System docs, code comments, configs: English
- Legal content related to German proceedings: German
- Marketing/sales content: match the target audience language (German for DACH market, English for international)

---

*These rules are not guidelines. They are constraints. Break them and the Output Gate rejects your work.*
