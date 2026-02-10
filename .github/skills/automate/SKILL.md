# Automate Skill - AIEmpire-Core

## Purpose

Automate repetitive tasks within the AI Empire ecosystem. This skill handles creating, scheduling, and managing automated workflows across all system components.

## Capabilities

### 1. GitHub Actions Automation

Create or modify workflows in `.github/workflows/`:

```yaml
# Standard workflow template
name: [Workflow Name]
on:
  schedule:
    - cron: '[schedule]'
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: [Step]
        run: |
          [commands]
```

**Existing Workflows:**

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `auto-content-generation.yml` | Every 4h | Generate X/Twitter content |
| `claude-health-check.yml` | Every 30min | Monitor Claude API status |
| `issue-command-bot.yml` | On issue comment | Process @bot commands |
| `revenue-tracking.yml` | Daily 9 AM | Revenue report |
| `x-auto-poster.yml` | Daily 7 AM | Post to X/Twitter |
| `weekly-review.yml` | Weekly | System review |
| `gold-nugget-extractor.yml` | On trigger | Extract insights |
| `daily-content-engine.yml` | Daily | Full content pipeline |
| `deploy-mobile.yml` | On push | Deploy mobile PWA |

### 2. Atomic Reactor Tasks

Define new automated tasks in `atomic-reactor/tasks/`:

```yaml
# Task template
name: [task-name]
description: [what it does]
schedule: [cron or trigger]
model: [ollama|kimi|claude]
priority: [1-5]
steps:
  - action: [action-type]
    params:
      key: value
```

### 3. OpenClaw Cron Jobs

Modify or add cron jobs via `openclaw-config/jobs.json`:

```json
{
  "name": "[job-name]",
  "schedule": "*/30 * * * *",
  "skill": "[skill-name]",
  "model": "kimi-k2.5",
  "enabled": true
}
```

### 4. Workflow System Automation

Leverage the 5-step compound loop:

```bash
# Automate a full cycle
python workflow-system/orchestrator.py

# Schedule the cowork daemon
python workflow-system/cowork.py --daemon --interval 1800

# Focus on specific area
python workflow-system/cowork.py --daemon --focus revenue
```

### 5. N8N Workflows

Connect external services via `n8n-workflows/n8n_connector.py`.

## Automation Patterns

### Pattern: Content Pipeline

```
Trigger: Cron (daily 7 AM)
Steps:
  1. Trend scan (Ollama) → trending topics
  2. Content generation (Kimi) → 10 posts
  3. Quality filter (Ollama) → top 5
  4. Schedule posting (GitHub Action)
  5. Track engagement (CRM)
```

### Pattern: Lead Qualification

```
Trigger: New lead in CRM
Steps:
  1. Enrich lead data (web scrape)
  2. BANT scoring (Ollama)
  3. If score > 7: route to Sales Agent
  4. If score 4-7: add to nurture sequence
  5. If score < 4: add to content funnel
```

### Pattern: Revenue Tracking

```
Trigger: Cron (daily 9 AM)
Steps:
  1. Pull Gumroad sales
  2. Pull Fiverr earnings
  3. Aggregate totals
  4. Compare to targets
  5. Generate report → docs/kpi/
  6. Alert if below target
```

## Cost Rules

| Model | Use For | Cost |
|-------|---------|------|
| Ollama (local) | 95% of tasks - routine, bulk, filtering | FREE |
| Kimi K2.5 | Volume content, swarm tasks | ~0.001 EUR/call |
| Claude Haiku | Quick quality checks | ~0.01 EUR/call |
| Claude Sonnet | Code review, strategy | ~0.05 EUR/call |
| Claude Opus | Critical decisions only | ~0.15 EUR/call |

**Budget limit:** 100 EUR/month total. Always default to Ollama first.

## Resource Guard Integration

Before creating compute-heavy automations, check thresholds:

| Level | CPU | RAM | Action |
|-------|-----|-----|--------|
| NORMAL | < 70% | < 75% | Full concurrency |
| WARN | > 70% | > 75% | Reduce to 200 concurrent |
| CRITICAL | > 85% | > 85% | Reduce to 50, outsource to Kimi |
| EMERGENCY | > 95% | > 92% | Pause all agents |

## Creating New Automations

1. Define the trigger (cron, webhook, event, manual)
2. Choose the execution layer (GitHub Actions, Atomic Reactor, OpenClaw, n8n)
3. Select models by cost (Ollama first)
4. Set resource limits
5. Add error handling and fallback
6. Test with `--test` flag before full deployment
7. Monitor via KPI snapshots in `docs/kpi/`
