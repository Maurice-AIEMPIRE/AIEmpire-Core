# Save Prompt - AIEmpire-Core

## Prompt Preservation

When a valuable prompt, system instruction, or agent configuration is created during a session, save it to the appropriate location:

### Routing Rules

| Content Type | Save Location | Format |
|-------------|---------------|--------|
| System prompt for an agent | `openclaw-config/` or `system-prompts/` | Markdown |
| Agent configuration | `openclaw-config/AGENTS.md` | Append to existing |
| Gold nugget (valuable insight) | `gold-nuggets/` | `GOLD_[TOPIC]_[DATE].md` |
| Workflow definition | `atomic-reactor/tasks/` | YAML |
| Brain module | `brain-system/brains/` | Numbered markdown |
| X/Twitter content | `x-lead-machine/` | Markdown |
| Business intelligence | `docs/` | Markdown |
| KPI snapshot | `docs/kpi/` | `YYYY-MM-DD.md` |

### Save Format

When saving a prompt or configuration:

```markdown
# [Title]

> Source: [conversation/file/URL]
> Created: [YYYY-MM-DD]
> Model: [which AI created this]
> Purpose: [one line description]

---

[Content here]
```

### Quality Check Before Saving

1. Is this genuinely valuable or just conversation noise?
2. Does a similar file already exist? → Update instead of duplicate
3. Is it in the right directory?
4. Are there any API keys or secrets? → Remove them
5. Will future agents/sessions benefit from this?

### After Saving

- Update `DOCUMENTATION_INDEX.md` if it's a new doc category
- Update `gold-nuggets/INDEX.md` if it's a gold nugget
- Commit with message: `docs: save [type] - [brief description]`
