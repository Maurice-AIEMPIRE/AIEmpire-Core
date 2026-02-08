# 🎯 Mission Control System

**Comprehensive task scanning and prioritization system for AI Empire**

## Overview

The Mission Control System scans ALL active & open tasks across multiple systems and provides a single-page overview with intelligent prioritization and actionable insights.

## Features

### 🔍 Multi-System Scanning

Scans tasks from:
- **GitHub Issues** - Open issues and labels
- **GitHub Actions** - Failed workflow runs
- **Atomic Reactor** - Task YAML files
- **Docker** - Container status and health
- **Brain System** - Pending synapses and messages
- **System Logs** - Error and critical events

### 📊 Smart Categorization

Automatically categorizes tasks into 5 categories:
- **BUILD** - New features, products, implementations
- **FIX** - Bugs, errors, broken functionality
- **AUTOMATE** - Workflow improvements, CI/CD
- **CONTENT** - Posts, blogs, marketing materials
- **STRATEGY** - Planning, roadmaps, vision

### 🎯 Intelligent Prioritization

Prioritizes tasks using the formula: **IMPACT > URGENCY > EFFORT**

- **Impact** (1-10): How much value this task creates
- **Urgency** (1-10): How time-sensitive the task is
- **Effort** (1-10): How much work is required

### 📈 Comprehensive Dashboard

Generates a single-page overview with:
- **Total Statistics** - Open tasks, blockers, high priority items
- **Top 10 Blockers** - Critical issues with root causes
- **Top 10 Levers** - Highest impact opportunities
- **Time-Critical Tasks** - Items with deadlines
- **Cost Risks** - Token/compute/infrastructure concerns
- **Tasks by Category** - Top 5 per category with full metrics
- **90-Minute Action List** - What to do NOW (max 7 items)

### 💾 Knowledge Graph Export

Exports complete task data to JSON for:
- Knowledge graph integration
- Historical tracking
- Analytics and reporting
- External system integration

## Usage

### Command Line

```bash
# Run full mission control scan
python3 mission_control.py

# Output:
# - Console dashboard
# - MISSION_CONTROL.md (saved to repo)
# - mission_control_data.json (full data export)
```

### GitHub Bot Integration

Use the GitHub Control Interface to run from any issue:

```
@bot mission-control
```

The bot will:
1. Scan all systems
2. Generate the dashboard
3. Post results as a comment
4. Export data to JSON

### Python API

```python
from mission_control import MissionControl

async def run():
    mc = MissionControl()
    
    # Scan all sources
    await mc.scan_all_sources()
    
    # Get specific insights
    blockers = mc.get_top_blockers(10)
    levers = mc.get_top_levers(10)
    
    # Generate dashboard
    dashboard = mc.generate_dashboard()
    print(dashboard)
    
    # Export data
    json_path = mc.export_to_json()
```

## Task Data Structure

Each task contains:

```python
@dataclass
class Task:
    id: str                    # Unique identifier
    title: str                 # Task description
    source: str                # Where it came from
    category: TaskCategory     # BUILD/FIX/AUTOMATE/CONTENT/STRATEGY
    priority: Priority         # CRITICAL/HIGH/MEDIUM/LOW
    impact: int                # 1-10
    urgency: int               # 1-10
    effort: int                # 1-10
    deadline: Optional[str]    # ISO date if applicable
    blocker: bool              # Is this blocking other work?
    blocker_reason: str        # Why is it a blocker?
    cost_risk: str             # Token/compute/infrastructure risk
    description: str           # Full details
```

## Output Files

### MISSION_CONTROL.md

Human-readable dashboard with:
- Executive summary
- Top blockers and levers
- Tasks by category
- 90-minute action list

### mission_control_data.json

Machine-readable data with:
- Complete task list
- Summary statistics
- Category breakdowns
- Priority distributions

Structure:
```json
{
  "generated_at": "2026-02-08T13:51:50",
  "summary": {
    "total_tasks": 42,
    "by_category": { "BUILD": 15, "FIX": 12, ... },
    "by_priority": { "HIGH": 8, "MEDIUM": 20, ... },
    "blockers": 3,
    "time_critical": 5,
    "cost_risks": 2
  },
  "tasks": [
    {
      "id": "GH-123",
      "title": "Implement feature X",
      "source": "GitHub Issues",
      "category": "BUILD",
      ...
    }
  ]
}
```

## Extending the System

### Add New Task Sources

To scan additional systems, add a new method to `MissionControl`:

```python
async def scan_your_system(self):
    """Scan your custom system"""
    print("  🔧 Scanning Your System...")
    
    # Your scanning logic here
    tasks = await fetch_tasks_from_system()
    
    for task_data in tasks:
        task = Task(
            id=f"SYSTEM-{task_data['id']}",
            title=task_data['title'],
            source="Your System",
            category=self._categorize(task_data),
            priority=Priority.MEDIUM,
            impact=task_data.get('impact', 5),
            urgency=task_data.get('urgency', 5),
            effort=task_data.get('effort', 5)
        )
        self.tasks.append(task)
```

Then add it to `scan_all_sources()`:

```python
await asyncio.gather(
    ...existing scanners...,
    self.scan_your_system()
)
```

### Custom Prioritization

Modify the `priority_score` property in the `Task` class:

```python
@property
def priority_score(self) -> float:
    """Custom priority calculation"""
    # Your formula here
    return custom_calculation(self.impact, self.urgency, self.effort)
```

### Custom Categories

Add new categories to the `TaskCategory` enum:

```python
class TaskCategory(Enum):
    BUILD = "BUILD"
    FIX = "FIX"
    AUTOMATE = "AUTOMATE"
    CONTENT = "CONTENT"
    STRATEGY = "STRATEGY"
    YOUR_CATEGORY = "YOUR_CATEGORY"  # Add here
```

## Integration Points

### GitHub Actions

Create a workflow to run mission control automatically:

```yaml
name: Mission Control Daily Scan
on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM UTC
  workflow_dispatch:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install aiohttp pyyaml
      - name: Run Mission Control
        run: python3 mission_control.py
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: mission-control-report
          path: |
            MISSION_CONTROL.md
            mission_control_data.json
```

### n8n Workflows

Trigger mission control from n8n:

1. Create HTTP Request node
2. Call GitHub Actions workflow dispatch API
3. Wait for completion
4. Fetch artifact with results
5. Parse and route to Slack/Email/Dashboard

### Brain System

Integrate with the orchestrator:

```python
# In brain-system/orchestrator.py
def run_mission_control():
    """Run mission control scan"""
    import subprocess
    result = subprocess.run(
        ["python3", "mission_control.py"],
        capture_output=True,
        text=True
    )
    
    # Send results to prefrontal brain
    send_synapse("orchestrator", "prefrontal", "MISSION_CONTROL", 
                {"dashboard": result.stdout}, priority=1)
```

## Best Practices

### Regular Scanning

Run mission control:
- **Daily** - Morning briefing (9 AM)
- **Before sprints** - Planning sessions
- **After incidents** - Post-mortem reviews
- **On-demand** - When feeling overwhelmed

### Task Hygiene

Keep task sources clean:
- Close completed GitHub issues promptly
- Remove outdated task files
- Update Docker services regularly
- Clean up old logs

### Prioritization Discipline

When setting task metrics:
- **Impact**: Focus on business value
- **Urgency**: Consider real deadlines, not urgency bias
- **Effort**: Estimate honestly, including overhead

### Action List Usage

The 90-minute list should be:
- ✅ **Actionable** - Can start immediately
- ✅ **Scoped** - Completable in ~90 minutes
- ✅ **Prioritized** - Highest value first
- ❌ **Not** - Vague, blocked, or requiring research

## Troubleshooting

### No Tasks Found

- Check GitHub CLI is installed: `gh --version`
- Verify GitHub auth: `gh auth status`
- Ensure task files exist in `atomic-reactor/tasks/`
- Check Docker is running: `docker ps`

### Missing Dependencies

```bash
pip install aiohttp pyyaml
```

### Permission Errors

Ensure the script has access to:
- GitHub repository (via `gh` CLI or `GITHUB_TOKEN`)
- Docker socket (user in docker group)
- Brain system database (`~/.openclaw/brain-system/`)
- Log files (read permissions)

## Future Enhancements

Planned features:
- [ ] AI-powered task description enhancement
- [ ] Automatic blocker detection using NLP
- [ ] Cost estimation for compute tasks
- [ ] Integration with Notion/Linear/Jira
- [ ] Real-time dashboard (web UI)
- [ ] Mobile notifications for blockers
- [ ] Historical trend analysis
- [ ] Team workload balancing

## Support

For issues or questions:
1. Check this README
2. Review `mission_control.py` source code
3. Run with verbose logging: `python3 mission_control.py --verbose`
4. Create a GitHub issue with logs

---

**Maurice's AI Empire - 2026**
*Automating everything, one system at a time* 🚀
