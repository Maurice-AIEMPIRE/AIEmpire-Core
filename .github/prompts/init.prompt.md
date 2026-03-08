# Init Prompt - AIEmpire-Core

## System Initialization

When starting a new session on this project, perform the following:

### 1. Load Context

Read these files to understand current state:

- `CLAUDE.md` - Project architecture and commands
- `EMPIRE_BLUEPRINT.md` - Strategic blueprint and revenue plan
- `docs/kpi/` - Latest KPI snapshot (most recent date file)
- `workflow-system/state/` - Current workflow state

### 2. Check System Status

```bash
# Workflow status
python workflow-system/orchestrator.py --status

# Resource guard
python workflow-system/resource_guard.py
```

### 3. Identify Priority

Determine the highest-priority action based on:

1. Are there revenue-blocking issues? → Fix immediately
2. Is any automation broken? → Restore it
3. Are there pending workflow steps? → Continue the loop
4. Is content generation running? → Verify quality

### 4. Report

Provide a brief status in this format:

```
EMPIRE STATUS:
- Revenue: [current EUR]
- Workflow: [step X of 5 / idle]
- Cowork: [running / stopped]
- Blockers: [list or "none"]
- Next action: [recommended task]
```

### 5. Await Instructions

After reporting status, wait for Maurice's direction. He prefers:

- Direct answers, no filler
- Tables over paragraphs
- German for business topics, English for technical
- Action over discussion
