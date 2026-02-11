# Repo Automation Map

## Core Automation Surfaces

| Path | Purpose | Primary edit targets |
| --- | --- | --- |
| `.github/workflows/` | GitHub-native automation | `*.yml` workflows, schedules, issue-bot logic |
| `openclaw-config/jobs.json` | Local cron job orchestration | `jobs[].schedule.expr`, payload prompts, enabled flags |
| `n8n-workflows/` | n8n workflow definitions | `*.json` flow files, `n8n_connector.py` |
| `workflow-system/` | 5-step compounding loop | `orchestrator.py`, `cowork.py`, `resource_guard.py` |
| `atomic_reactor/tasks/` | Batch task definitions | `T-*.yaml` task prompts and metadata |
| `atomic_reactor/run_tasks.py` | Atomic Reactor execution engine | execution model, report outputs |
| `scripts/` | Local service lifecycle | `start_all_services.sh`, `check_status.sh`, `stop_all_services.sh` |

## Key Output Artifacts

| Path | Produced by |
| --- | --- |
| `MISSION_CONTROL.md` | `mission_control.py` and mission-control workflows |
| `mission_control_data.json` | `mission_control.py` |
| `atomic_reactor/reports/*.md` | `atomic_reactor/run_tasks.py` |
| `atomic_reactor/reports/summary_*.json` | `atomic_reactor/run_tasks.py` |
| `workflow-system/output/*.json` | `workflow-system/orchestrator.py` |
| `workflow-system/cowork_output/*.json` | `workflow-system/cowork.py` |

## Naming and Path Notes

1. Use `atomic_reactor/` as the canonical path in this repository.
2. Treat `atomic-reactor` references in old docs/scripts as legacy text; verify and normalize before adding new changes.
3. Keep workflow file names stable if other automations dispatch by `workflow_id`.
