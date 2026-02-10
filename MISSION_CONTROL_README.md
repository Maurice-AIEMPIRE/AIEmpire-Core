# Mission Control System

## Overview

Mission Control is the central scanning and prioritization system for the AI Empire. It scans all active and open tasks across every subsystem (GitHub Issues, GitHub Actions workflows, Atomic Reactor tasks, Docker services, Brain System, and logs), then produces a single-page dashboard ranked by **IMPACT > URGENCY > EFFORT**.

## Architecture

```
Mission Control
├── Source Scanners
│   ├── GitHub Issues        (open issues with labels)
│   ├── GitHub Actions       (failed workflow runs)
│   ├── Atomic Reactor       (YAML task definitions)
│   ├── Docker Services      (exited containers)
│   ├── Brain System         (pending synapses)
│   └── System Logs          (error entries)
├── Prioritization Engine
│   ├── Priority Score = (10-IMPACT)*100 + (10-URGENCY)*10 + EFFORT
│   ├── Blocker Detection
│   ├── Time-Critical Filter
│   └── Cost-Risk Analysis
├── Dashboard Generator
│   ├── Overview Statistics
│   ├── Top 10 Blockers
│   ├── Top 10 Levers (highest impact)
│   ├── Time-Critical Tasks
│   ├── Cost Risks
│   ├── Tasks by Category (BUILD/FIX/AUTOMATE/CONTENT/STRATEGY)
│   └── Next 90 Minutes Action List
└── Outputs
    ├── MISSION_CONTROL.md   (Markdown dashboard)
    ├── mission_control_data.json (JSON for knowledge graph)
    └── Console report
```

## Quick Start

### Run a Full Scan

```bash
python mission_control.py
```

This scans all sources, generates the dashboard, and saves both `MISSION_CONTROL.md` and `mission_control_data.json`.

### Via GitHub Issue Command

```
@bot mission-control
```

The bot will run a full scan and post the dashboard as a comment on the issue.

### Via Empire CLI

```bash
python workflow-system/empire.py status
```

Mission Control data is included in the unified empire status.

## Task Model

Every task has these attributes:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (e.g. GH-42, WF-content, TASK-deploy) |
| `title` | string | Short task description |
| `source` | string | Where the task was discovered |
| `category` | enum | BUILD, FIX, AUTOMATE, CONTENT, STRATEGY |
| `priority` | enum | CRITICAL, HIGH, MEDIUM, LOW |
| `impact` | int (1-10) | Business impact score |
| `urgency` | int (1-10) | Time sensitivity score |
| `effort` | int (1-10) | Estimated effort (lower = easier) |
| `deadline` | string? | Optional deadline date |
| `blocker` | bool | Whether this blocks other work |
| `blocker_reason` | string? | Why it blocks |
| `cost_risk` | string? | Financial risk description |
| `description` | string? | Detailed task description |

## Priority Score Formula

```
priority_score = (10 - impact) * 100 + (10 - urgency) * 10 + effort
```

Lower score = higher priority. Impact dominates because it is multiplied by 100, urgency by 10, and effort is added directly. This ensures that high-impact tasks always surface first, even if they have lower urgency.

## Source Scanners

### GitHub Issues
- Uses `gh issue list` CLI
- Reads issue labels for categorization
- Labels containing "bug", "blocker", "critical" are marked as blockers
- Each open issue becomes a task

### GitHub Actions
- Uses `gh run list` CLI
- Checks last 10 workflow runs
- Failed workflows become FIX tasks with blocker status

### Atomic Reactor Tasks
- Reads YAML files from `atomic-reactor/tasks/`
- Each task definition becomes a BUILD task
- Reads impact and effort from YAML if available

### Docker Services
- Uses `docker ps -a` command
- Exited containers become FIX tasks
- Monitors container health

### Brain System
- Checks SQLite database at `~/.openclaw/brain-system/synapses.db`
- Pending (unprocessed) synapses above threshold become AUTOMATE tasks

### System Logs
- Scans `logs/` directory and `/var/log/`
- Files containing ERROR or CRITICAL keywords generate review tasks

## Dashboard Sections

### Overview
Total counts: open tasks, blockers, high priority, time-critical, cost risks.

### Top 10 Blockers
Tasks with `blocker=True`, sorted by priority score.

### Top 10 Levers
Tasks with highest impact score, regardless of blocker status.

### Time-Critical Tasks
Tasks with deadlines, sorted by date.

### Cost Risks
Tasks with `cost_risk` set, showing financial exposure.

### Tasks by Category
Top 5 tasks per category (BUILD, FIX, AUTOMATE, CONTENT, STRATEGY).

### Next 90 Minutes Action List
Top 7 tasks by priority score with full context for immediate action.

## JSON Export

The `mission_control_data.json` file contains:

```json
{
  "generated_at": "2026-02-10T12:00:00",
  "summary": {
    "total_tasks": 15,
    "by_category": {"BUILD": 5, "FIX": 4, ...},
    "by_priority": {"CRITICAL": 1, "HIGH": 3, ...},
    "blockers": 2,
    "time_critical": 1,
    "cost_risks": 1
  },
  "tasks": [...]
}
```

This file is designed to be consumed by the Digital Memory knowledge graph and other analysis tools.

## Testing

Run the test suite:

```bash
python -m pytest test_mission_control.py -v
```

Or with unittest:

```bash
python -m unittest test_mission_control -v
```

The test suite covers:
- Task creation and priority scoring
- Category and priority enums
- All scanner methods (with mocked external calls)
- Dashboard and action list generation
- JSON export and serialization
- Empty state handling
- Error resilience for missing tools (gh, docker, yaml)

## Files

| File | Purpose |
|------|---------|
| `mission_control.py` | Core scanning and reporting system |
| `test_mission_control.py` | Complete test suite |
| `MISSION_CONTROL_README.md` | This documentation |
| `MISSION_CONTROL.md` | Generated dashboard (gitignored) |
| `mission_control_data.json` | Generated JSON data (gitignored) |

## Integration

Mission Control integrates with:
- **GitHub Control Interface** via `@bot mission-control` command
- **Empire CLI** via `python workflow-system/empire.py status`
- **Cowork Engine** reads mission control data for autonomous planning
- **Digital Memory** consumes the JSON export for knowledge graph updates

## Requirements

- Python 3.8+
- `gh` CLI (optional, for GitHub scanning)
- `docker` CLI (optional, for container scanning)
- `pyyaml` (optional, for Atomic Reactor task scanning)

All scanners handle missing dependencies gracefully and report what they can access.
