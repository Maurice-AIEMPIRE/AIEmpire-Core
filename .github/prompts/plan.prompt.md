# Plan Prompt - AIEmpire-Core

## Planning Mode

When asked to plan a feature, change, or new capability for the AI Empire:

### Framework

1. **Assess scope** against existing architecture (see `CLAUDE.md`)
2. **Check dependencies** - which systems are affected?
3. **Estimate cost** - can this run on Ollama or does it need paid APIs?
4. **Define steps** - numbered, with files and expected outcomes
5. **Identify risks** - what could break? How to mitigate?
6. **Set priority** - P0 (revenue now) through P3 (backlog)

### Output Template

```markdown
## Plan: [Feature Name]

**Priority:** P[0-3]
**Estimated effort:** [hours]
**Model tier:** [Ollama | Kimi | Claude]
**Cost:** [EUR estimate]

### Steps
1. [ ] ...
2. [ ] ...
3. [ ] ...

### Files Changed
- `path/to/file` - [what changes]

### Risks
- [Risk]: [Mitigation]

### Success Criteria
- [ ] [Measurable result]
```

### Key Constraints

- Budget: max 100 EUR/month total API spend
- Hardware: M4, 16GB RAM - respect Resource Guard limits
- Must not break existing workflows or revenue paths
- All API keys via environment variables
- Prefer Ollama → Kimi → Claude (cost escalation ladder)
