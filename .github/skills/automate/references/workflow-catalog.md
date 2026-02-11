# Workflow Catalog

## GitHub Actions Workflows

| File | Trigger | Main function |
| --- | --- | --- |
| `.github/workflows/auto-content-generation.yml` | `cron: 0 */4 * * *`, `workflow_dispatch` | Generate X content and open review issue |
| `.github/workflows/auto-process-issues.yml` | `issues(opened,labeled)`, `workflow_dispatch` | Auto-handle labeled issues and stale cleanup |
| `.github/workflows/claude-health-check.yml` | `cron: */30 * * * *`, `workflow_dispatch` | Detect Claude API failure and create failover issue |
| `.github/workflows/daily-content-engine.yml` | `cron: 0 6/10/16/22 * * *`, `workflow_dispatch` | Multi-block daily content, product, and engagement tasks |
| `.github/workflows/deploy-mobile.yml` | `push main` on `mobile-command-center/**`, `workflow_dispatch` | Deploy mobile command center to GitHub Pages |
| `.github/workflows/gold-nugget-extractor.yml` | `push main` on `gold-nuggets/**` or `docs/**`, `cron: 0 20 * * *`, `workflow_dispatch` | Build nugget index and create follow-up issues |
| `.github/workflows/issue-command-bot.yml` | `issues(opened)`, `issue_comment(created)` | Execute `@bot` commands and trigger workflows |
| `.github/workflows/mission-control-scan.yml` | `cron: 0 9 * * *`, `workflow_dispatch` | Run mission control scan and publish daily report |
| `.github/workflows/revenue-tracking.yml` | `cron: 0 9 * * *`, `workflow_dispatch` | Generate daily revenue report issue |
| `.github/workflows/weekly-review.yml` | `cron: 0 8 * * 0`, `workflow_dispatch` | Build weekly review and planning issue |
| `.github/workflows/x-auto-poster.yml` | `cron: 0 7 * * *`, `workflow_dispatch` | Generate daily X posting guide and issue |

## Command Routing Rules

1. Keep `workflow_id` values unchanged when dispatched by `actions.createWorkflowDispatch`.
2. Preserve existing labels used for triage (`content`, `auto-generated`, `revenue`, `planning`, `daily-report`).
3. If you change schedule times, update comments in the file to avoid operator confusion.
