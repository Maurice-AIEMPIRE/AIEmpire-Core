# Mission Control System Documentation

Complete strategic task oversight and intelligent prioritization system for AI Empire.

## Overview

Mission Control is a multi-dimensional task management system that automatically scans various sources (GitHub, Docker, logs, task files, Brain System) and intelligently prioritizes work based on impact, urgency, and effort.

### Key Features

- **Multi-Source Scanning**: Automatically discovers tasks from 6+ sources
- **Intelligent Prioritization**: Priority Score formula balances impact, urgency, and effort
- **Strategic Categorization**: 5 task categories (BUILD, FIX, AUTOMATE, CONTENT, STRATEGY)
- **Blocker Detection**: Identifies and highlights blocking issues
- **Time-Critical Awareness**: Tracks deadlines and time-sensitive tasks
- **Cost Risk Management**: Identifies tasks with financial implications
- **Daily Automation**: GitHub Actions workflow for automated scanning
- **JSON Export**: Machine-readable output for integration with other systems

## Smart Categorization

Tasks are automatically organized into 5 strategic categories:

### 1. BUILD
Developing new features, expanding capabilities, infrastructure work.
- Typically medium-high effort
- High strategic value
- Non-urgent (usually)

### 2. FIX
Bug fixes, critical issues, system repairs.
- Often medium effort
- High urgency
- Blocking other work

### 3. AUTOMATE
Process optimization, workflow automation, efficiency improvements.
- Varies in effort
- High ROI
- Long-term impact

### 4. CONTENT
Content creation, documentation, marketing materials.
- Low to medium effort
- Medium urgency
- Builds brand/visibility

### 5. STRATEGY
Planning, roadmapping, research, decision-making.
- Low effort (usually)
- Low urgency (usually)
- High strategic importance

## Intelligent Prioritization

### Priority Levels
- **CRITICAL**: Blocking system, major issue
- **HIGH**: Important, impacts work
- **MEDIUM**: Standard priority
- **LOW**: Nice-to-have, can defer

### Priority Score Formula

```
Score = (10 - Impact) * 100 + (10 - Urgency) * 10 + Effort
```

**Key rule:** Lower score = higher priority.

**Components:**
- **Impact** (1-10): How much value does completing this task add?
- **Urgency** (1-10): How time-sensitive is this task?
- **Effort** (1-10): How much effort does this task require?

**Interpretation:**
- Higher impact reduces the score strongly (dominant factor).
- Higher urgency reduces the score (secondary factor).
- Higher effort increases the score (penalty).

**Examples:**
- Fix critical bug: Impact=9, Urgency=9, Effort=4 → Score = 100 + 10 + 4 = 114 (TOP)
- Write blog: Impact=3, Urgency=2, Effort=3 → Score = 700 + 80 + 3 = 783 (LOW)

## Multi-System Scanning

### 1. GitHub Issues
Automatically scans open and closed issues, categorizes by labels:
- Labels `fix`, `bug` → FIX category
- Labels `automate`, `automation` → AUTOMATE category
- Labels `content` → CONTENT category
- Labels `strategy` → STRATEGY category
- Labels `critical`, `high`, `low` → Priority level

**Requires:** `GITHUB_TOKEN` environment variable

### 2. GitHub Workflow Runs
Detects failed workflows and creates blocker tasks:
- Failed runs → High-priority FIX tasks
- Blocking work until resolved

**Requires:** `GITHUB_TOKEN` environment variable

### 3. Task Files
Reads YAML definitions from `atomic-reactor/tasks/*.yaml`:

```yaml
title: My Task
category: BUILD  # or FIX, AUTOMATE, CONTENT, STRATEGY
priority: HIGH   # or CRITICAL, MEDIUM, LOW
impact: 8        # 1-10
urgency: 5       # 1-10
effort: 4        # 1-10
deadline: 2026-02-15T23:59:59
cost_risk: EUR 5000 revenue impact
tags:
  - backend
  - critical
description: Task description here
```

### 4. Docker Services
Scans container status and flags exited/dead services:
- Stopped containers → High-priority FIX tasks
- Prevents system degradation

**Requires:** Docker installed and running

### 5. Brain System (Synapses DB)
Monitors the Brain System database for integration points:
- Located at `~/.openclaw/brain-system/synapses.db`
- Detects issues or anomalies

**Optional:** System may not be installed

### 6. Log Files
Scans logs for ERROR and CRITICAL entries:
- Locations: `logs/`, root directory
- Creates FIX tasks for errors found
- Limits to first 5 errors per scan

## Usage

### Command Line

```bash
# Run Mission Control scan
python3 mission_control.py

# This will:
# 1. Scan all sources
# 2. Generate MISSION_CONTROL.md dashboard
# 3. Generate mission_control_data.json export
# 4. Print action list for next 90 minutes
```

### GitHub Bot Integration

Add this command in any GitHub issue or issue comment:

```
@bot mission-control
```

The bot will run Mission Control and post results in the issue.

### Python API

```python
from mission_control import MissionControl, TaskCategory
import asyncio

async def main():
    mission = MissionControl()

    # Run full scan
    await mission.scan_all_sources()

    # Get top blockers
    blockers = mission.get_top_blockers(5)

    # Get high-impact tasks
    levers = mission.get_top_levers(10)

    # Get by category
    build_tasks = mission.get_by_category(TaskCategory.BUILD, 5)

    # Generate outputs
    dashboard = mission.generate_dashboard()
    action_list = mission.generate_action_list(7)

    # Export to JSON
    mission.export_to_json()

asyncio.run(main())
```

### GitHub Actions Automation

The system includes `.github/workflows/mission-control-scan.yml` which:

**Trigger Options:**
- Daily at 9 AM UTC (schedule)
- Manual trigger via `workflow_dispatch`
- Custom triggers (comments, issues)

**Outputs:**
- Creates daily issue with full report
- Uploads dashboard artifact
- Uploads JSON data artifact
- Comments on trigger issue (if applicable)

## Output Files

### MISSION_CONTROL.md
Markdown dashboard with:
- Summary statistics
- Top 5 blockers
- Top 5 levers (high impact)
- Tasks by category
- Time-critical tasks (<7 days)
- Cost risks

**Usage:**
- View in GitHub
- Post in Slack
- Review in editor
- Link in documentation

### mission_control_data.json
Machine-readable export with:
- Full task data
- Priority scores
- All metadata
- Summary statistics

**Schema:**
```json
{
  "timestamp": "2026-02-10T14:30:00",
  "summary": {
    "total_tasks": 42,
    "blockers": 3,
    "time_critical": 5,
    "cost_risks": 2
  },
  "tasks": [
    {
      "title": "Task name",
      "category": "BUILD",
      "priority": "HIGH",
      "impact": 8,
      "urgency": 6,
      "effort": 4,
      "priority_score": 264,
      "deadline": "2026-02-15T23:59:59",
      "cost_risk": "EUR 5000",
      "blocker": false,
      "source": "GitHub Issue",
      "url": "https://...",
      "description": "...",
      "tags": ["tag1", "tag2"],
      "assigned_to": "username"
    }
  ]
}
```

**Usage:**
- Integration with dashboards
- API endpoints
- Reporting systems
- Data analysis

## Extending the System

### Adding New Task Sources

```python
async def scan_custom_source(self):
    """Scan custom source for tasks."""
    # Get data from source
    data = await fetch_from_source()

    # Create Task objects
    for item in data:
        task = Task(
            title=item['name'],
            category=TaskCategory.BUILD,
            priority=Priority.MEDIUM,
            impact=item.get('value', 5),
            urgency=item.get('urgency', 5),
            effort=item.get('effort', 5),
            source="Custom Source",
            url=item.get('url'),
            description=item.get('description'),
            tags=item.get('tags', [])
        )
        self.tasks.append(task)

    print(f"✅ Custom Source: Found {len(data)} tasks")
```

Then call in `scan_all_sources()`:
```python
await self.scan_custom_source()
```

### Custom Prioritization

Override `prioritize_tasks()` with custom scoring:

```python
def prioritize_tasks(self):
    """Custom prioritization logic."""
    for task in self.tasks:
        # Apply custom scoring
        if task.category == TaskCategory.CONTENT:
            task.priority_score *= 1.2  # Boost content tasks

    self.tasks.sort(key=lambda t: t.priority_score, reverse=True)
```

### Custom Categories

Extend TaskCategory enum:

```python
class TaskCategory(Enum):
    BUILD = "Build"
    FIX = "Fix"
    AUTOMATE = "Automate"
    CONTENT = "Content"
    STRATEGY = "Strategy"
    CUSTOM = "Custom"  # Add new category
```

## Integration Points

### GitHub Actions
- Daily automated scans
- Issue creation with results
- Artifact uploads
- Workflow automation

### n8n Workflows
- Webhook trigger for scans
- Parse JSON output
- Create tasks in external systems
- Send notifications

### Brain System
- Read synapses database
- Extract knowledge graph
- Integrate with decision making

### Chat Interface
- Use `@bot mission-control` command
- Get current priorities
- Request action list

### Dashboards
- Post to Slack
- Update web dashboard
- Feed into analytics

## Best Practices

### 1. Keep Data Fresh
- Run daily scans
- Update GitHub labels for accuracy
- Keep task files current

### 2. Classify Correctly
- Use consistent category labels
- Set realistic impact/urgency/effort
- Include deadlines for time-critical work

### 3. Use Blockers Wisely
- Mark only truly blocking issues
- Review blockers daily
- Resolve quickly

### 4. Set Meaningful Deadlines
- Use ISO format: `YYYY-MM-DDTHH:MM:SS`
- Include time zone info
- Aim for deadline clarity

### 5. Document Cost Risks
- Record financial implications
- Track potential savings
- Link to business impact

### 6. Regular Review
- Review action list daily
- Adjust priorities as needed
- Celebrate completed tasks

### 7. Integrate Early
- Add to GitHub status checks
- Embed in daily standups
- Reference in planning

## Troubleshooting

### No Tasks Found
**Causes:**
- No GitHub token configured
- No sources connected
- All services unavailable

**Fix:**
```bash
# Test GitHub access
export GITHUB_TOKEN="your-token"
gh issue list

# Check local sources
ls -la atomic-reactor/tasks/
docker ps
```

### Tasks Not Updating
**Causes:**
- Stale task files
- Labels not recognized
- Scan timing issue

**Fix:**
- Run manual scan: `python3 mission_control.py`
- Check GitHub labels match expected patterns
- Verify workflow is running: Check Actions tab

### Priority Scores Unexpected
**Causes:**
- Misunderstanding of formula
- Task data errors
- Score not recalculated

**Fix:**
```python
# Debug a task
task = mission.tasks[0]
print(f"Title: {task.title}")
print(f"Impact: {task.impact}, Urgency: {task.urgency}, Effort: {task.effort}")
print(f"Score: {task.priority_score}")
print(f"Calculation: ({10-task.impact})*100 + ({10-task.urgency})*10 + {task.effort}")
```

### Export File Issues
**Causes:**
- Permission denied
- File path incorrect
- JSON serialization error

**Fix:**
```bash
# Check permissions
ls -la mission_control_data.json
chmod 644 mission_control_data.json

# Validate JSON
python3 -m json.tool mission_control_data.json

# Run with explicit path
python3 -c "from mission_control import MissionControl; m = MissionControl(); m.export_to_json('/tmp/export.json')"
```

## Performance

### Scan Times
- GitHub Issues: ~2-5 seconds
- Workflows: ~2-5 seconds
- Task Files: <1 second
- Docker: <1 second
- Brain System: ~1 second
- Logs: ~1 second
- **Total: ~10-20 seconds typical**

### Optimization
- Parallel scanning (multiple sources simultaneously)
- Task limit filters for large repos
- Caching layer (future)

### Scaling
- Works efficiently with 100+ tasks
- JSON export handles 1000+ items
- GitHub API rate limiting (60 requests/hour unauthenticated)

## Testing

Run the test suite:

```bash
# Run all tests
python3 test_mission_control.py

# Test results include:
# ✅ Basic functionality tests
# ✅ Real system scan test
# ✅ Priority calculation
# ✅ Category filtering
# ✅ Dashboard generation
# ✅ JSON export validation
```

## Version History

### v1.0.0 (2026-02-10)
- Initial release
- 5 task categories
- 6 source scanners
- Priority score formula
- Dashboard generation
- JSON export
- GitHub Actions automation

## License

Part of AI Empire Core - MIT License

## Support

For issues or questions:
- Create issue on GitHub
- Check troubleshooting section
- Review logs in GitHub Actions
- Test with `python3 mission_control.py`
