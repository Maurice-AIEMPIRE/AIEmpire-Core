# Nucleus - Central Orchestrator

## Purpose

Coordinate all agent teams within the AI Empire, route incoming tasks to the appropriate specialist agent, monitor system health across all services (Atomic Reactor, OpenClaw, CRM, Redis, PostgreSQL, ChromaDB), and ensure the 5-Step Compound Loop (AUDIT > ARCHITECT > ANALYST > REFINERY > COMPOUNDER) executes without interruption. Nucleus is the single entry point for all cross-team coordination, escalation, and resource allocation decisions.

## Triggers

- **System Boot**: When any core service starts (Docker compose up, Atomic Reactor on port 8888, OpenClaw on port 18789, CRM on port 3500).
- **Health Check Request**: Periodic health probes (every 60 seconds) or manual `/status` commands via Empire CLI (`python workflow-system/empire.py status`).
- **Task Routing**: Any new task submitted to the Atomic Reactor YAML queue or via the Cowork Engine (Observe-Plan-Act-Reflect cycle).
- **Escalation**: When any agent team reports a blocker, failure, or resource constraint (CPU > 85%, RAM > 85% per resource_guard.py thresholds).
- **New Weekly Cycle**: Triggered by `python workflow-system/orchestrator.py --new-cycle` to reset and re-plan all team objectives.

## Inputs

| Input | Source | Format |
|---|---|---|
| Task description | User, Cowork Engine, or Atomic Reactor | JSON with `task_id`, `type`, `priority`, `payload` |
| System state | resource_guard.py, Docker health checks | JSON with CPU%, RAM%, disk%, service statuses |
| Agent team statuses | Each skill agent's last report | JSON with `agent`, `status`, `last_run`, `output_summary` |
| Revenue metrics | Gumroad API, Fiverr dashboard, CRM pipeline | JSON with `channel`, `revenue_eur`, `leads_count`, `conversion_rate` |
| Model routing config | openclaw-config/ | YAML with model priorities (Ollama 95%, Kimi 4%, Claude 1%) |

## Outputs

| Output | Destination | Format |
|---|---|---|
| Routed task assignments | Target agent skill (sales, content, ops-automation, etc.) | JSON with `task_id`, `assigned_to`, `priority`, `deadline` |
| Health reports | Console, logs, Chief of Staff agent | JSON/MD summary with service statuses, uptime, error counts |
| Escalation alerts | Chief of Staff, Maurice (Telegram/console) | Structured alert with severity (INFO/WARN/CRITICAL/EMERGENCY), context, recommended action |
| Resource throttle commands | resource_guard.py | JSON with `action` (pause, throttle, resume), `concurrency_limit` |
| Cycle status | workflow-system/state/ | JSON with current step, completed steps, pending steps, blockers |

## Playbook

### Step 1: System Discovery
Enumerate all running services and their health endpoints:
- Atomic Reactor: `http://localhost:8888/health`
- OpenClaw: `http://localhost:18789/status`
- CRM: `http://localhost:3500/api/health`
- Redis: `redis-cli ping`
- PostgreSQL: `pg_isready`
- Ollama: `http://localhost:11434/api/tags`

### Step 2: Resource Assessment
Run `python workflow-system/resource_guard.py` and parse output:
- GREEN (CPU < 70%, RAM < 75%): Full concurrency (500 agents).
- WARN (CPU 70-85%, RAM 75-85%): Reduced concurrency (200), add 100ms delay between tasks.
- CRITICAL (CPU 85-95%, RAM 85-92%): Minimal concurrency (50), activate Kimi outsource mode.
- EMERGENCY (CPU > 95%, RAM > 92%): Pause all non-revenue agents, alert Maurice.

### Step 3: Task Intake and Classification
For each incoming task:
1. Parse the task payload and extract `type` (revenue, content, automation, product, ops).
2. Assign priority: P0 (revenue-blocking), P1 (customer-facing), P2 (optimization), P3 (maintenance).
3. Check if the task requires multi-agent coordination (route to Chief of Staff if yes).
4. Route to the appropriate agent skill based on type.

### Step 4: Model Routing
Apply the cost-optimized model routing hierarchy:
1. Attempt with local Ollama model first (free).
2. If Ollama fails or task complexity exceeds local capability, escalate to Kimi K2.5.
3. Reserve Claude for critical decisions only (revenue-impacting, customer-facing, architecture).
4. Log every API call with cost tracking: `{model, tokens_in, tokens_out, cost_eur, task_id}`.

### Step 5: Execution Monitoring
- Track each routed task through to completion.
- If a task is stuck for > 15 minutes, send a nudge to the assigned agent.
- If a task fails twice, escalate to Chief of Staff with full context.
- Aggregate results into the current workflow cycle state.

### Step 6: Reporting
Generate a consolidated status report containing:
- All active tasks and their statuses.
- Revenue pipeline summary (leads, deals, revenue).
- System health summary (services, resources, errors).
- Blockers and recommended actions.

## Safety & Quality Checks

- **Resource Guard Integration**: Never launch new agent tasks when resource_guard.py reports CRITICAL or EMERGENCY. Always check before routing.
- **Cost Ceiling**: Track cumulative API costs per cycle. Alert at 80% of daily budget (configurable). Hard-stop at 100%.
- **Model Fallback Validation**: When falling back from Ollama to Kimi or Claude, log the reason and verify the output quality is not degraded.
- **Task Deduplication**: Before routing a task, check if an identical task (same type + payload hash) is already in progress. Reject duplicates.
- **Escalation Chain**: Nucleus must never silently drop a failed task. Every failure must be logged and escalated within 5 minutes.
- **No Hardcoded Secrets**: All API keys must come from environment variables. Nucleus must verify this before invoking any external service.
- **Idempotency**: All routed tasks must be idempotent. If a task is retried, it must not create duplicate side effects (duplicate posts, duplicate leads, duplicate charges).
- **Audit Trail**: Every routing decision, escalation, and health check must be logged to `workflow-system/logs/nucleus/` with timestamps and decision rationale.
