# Operations Runbook

## Preflight and baseline

```bash
.github/skills/automate/scripts/preflight_automation.sh
```

## Local service lifecycle

```bash
./scripts/start_all_services.sh
./scripts/check_status.sh
./scripts/stop_all_services.sh
```

## Mission control

```bash
python3 mission_control.py
```

Expected outputs:
- `MISSION_CONTROL.md`
- `mission_control_data.json`

## Workflow system loop

```bash
python3 workflow-system/orchestrator.py --status
python3 workflow-system/orchestrator.py --step audit
python3 workflow-system/cowork.py --status
python3 workflow-system/cowork.py --focus automation
```

## Atomic reactor execution

```bash
python3 atomic_reactor/run_tasks.py
```

Expected outputs:
- `atomic_reactor/reports/*`

## n8n connector quick check

```bash
python3 n8n-workflows/n8n_connector.py --help
```

## Lightweight syntax checks

```bash
python3 -m py_compile mission_control.py workflow-system/orchestrator.py workflow-system/cowork.py atomic_reactor/run_tasks.py
```

## Troubleshooting shortcuts

1. If a scheduled workflow does not trigger, verify cron syntax and default branch.
2. If `@bot` commands do nothing, inspect `.github/workflows/issue-command-bot.yml` permissions and `GITHUB_TOKEN` availability.
3. If local scripts fail, confirm executable bits and command dependencies via the preflight script.
