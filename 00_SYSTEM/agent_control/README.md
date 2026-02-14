# Agent Control (Parallel Terminal Team Mode)

Leichtgewichtiges Queue-System fuer paralleles Arbeiten mit mehreren Terminal-Modellen.

State:
- `00_SYSTEM/agent_control/queue.json`

CLI:
- `python3 automation/scripts/agent_control.py add --title "..." --details "..." --cmd "..." --priority 5`
- `python3 automation/scripts/agent_control.py claim --agent claude_a`
- `python3 automation/scripts/agent_control.py done --agent claude_a --id <task_id> --note "..."`
- `python3 automation/scripts/agent_control.py fail --agent claude_a --id <task_id> --note "..."`
- `python3 automation/scripts/agent_control.py heartbeat --agent claude_a --status "working"`
- `python3 automation/scripts/agent_control.py list`

Non-interactive wrapper:
- `automation/scripts/run_no_confirm.sh <command> ...`
- mit Auto-Yes: `AUTO_CONFIRM=1 automation/scripts/run_no_confirm.sh <command> ...`

Live execution policy:
- `00_SYSTEM/agent_control/LIVE_EXECUTION_POLICY.md`
