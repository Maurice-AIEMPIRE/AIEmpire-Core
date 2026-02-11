---
name: automate
description: >-
  Automation operator for AIEmpire-Core. Use when planning, creating, updating, or debugging repository automations:
  GitHub Actions workflows, @bot issue-command flows, mission-control scans, OpenClaw cron jobs in openclaw-config/jobs.json,
  n8n workflow JSON files, workflow-system orchestration loops, atomic_reactor task execution, and local service
  start/stop/status scripts. Trigger for schedule changes, pipeline failures, automation reliability work, cost-aware
  model routing, and recurring content or revenue operations.
---

# Automate

Operate AIEmpire-Core automations with reproducible changes and lightweight validation.
Load only the reference file that matches the current task to keep context small.

## Select the execution layer

1. Use `.github/workflows/` for repository events, cron schedules, issue bot behavior, and artifact or report publishing.
2. Use `openclaw-config/jobs.json` for local OpenClaw cron turns routed to specific agents.
3. Use `n8n-workflows/*.json` for external integrations and no-code orchestration.
4. Use `workflow-system/` (`orchestrator.py`, `cowork.py`) for iterative planning and refinement loops.
5. Use `atomic_reactor/tasks/*.yaml` plus `atomic_reactor/run_tasks.py` for batch LLM task execution.
6. Use `scripts/start_all_services.sh`, `scripts/check_status.sh`, and `scripts/stop_all_services.sh` for local runtime operations.

## Run the preflight first

Run:

```bash
.github/skills/automate/scripts/preflight_automation.sh
```

Use output to confirm missing commands, missing paths, unset environment variables, and service port state before editing automations.

## Follow this change workflow

1. Identify the source of truth with `references/repo-map.md`.
2. Confirm current behavior in `references/workflow-catalog.md` before modifying schedules or command logic.
3. Implement the smallest safe change.
4. Validate with the matching command from `references/ops-runbook.md`.
5. If workflow behavior changed, update comments, labels, and status messages in the same file so operator intent stays explicit.
6. Keep generated artifacts and reports out of commits unless the task explicitly requires them.

## Enforce operating rules

1. Prefer existing directories and conventions; do not create parallel automation stacks.
2. Keep path usage consistent with real repository names (`atomic_reactor`, not `atomic-reactor`).
3. Treat API keys and tokens as environment-only values; never write secrets into files.
4. Prefer cheap or local execution paths first, then escalate model cost only when quality or context limits require it.
5. Include failure handling for automation changes (timeouts, retries, or explicit fallback paths).

## Use references on demand

- Read `references/repo-map.md` for directory ownership and file-level authority.
- Read `references/workflow-catalog.md` for current GitHub workflow triggers and outputs.
- Read `references/ops-runbook.md` for command-level validation and troubleshooting.
