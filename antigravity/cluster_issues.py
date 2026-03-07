#!/usr/bin/env python3
"""
Issue Clusterer – Groups issues by root cause → ISSUES.json + ISSUES_KANBAN.md
Usage: python3 antigravity/cluster_issues.py
"""

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from antigravity.config import ISSUES_FILE, KANBAN_FILE, REPORTS_DIR

from rich.console import Console
from rich.table import Table

console = Console()

CLUSTERS = {
    "missing_deps": {"label": "Missing Dependencies", "owner": "fixer", "priority": 1},
    "import_cycle": {"label": "Import Cycles", "owner": "architect", "priority": 2},
    "syntax": {"label": "Syntax Errors", "owner": "fixer", "priority": 1},
    "init_error": {"label": "Init Order Errors", "owner": "fixer", "priority": 2},
    "import_error": {"label": "Import Errors", "owner": "fixer", "priority": 2},
    "logic_error": {"label": "Logic Errors", "owner": "coder", "priority": 3},
    "test_failure": {"label": "Test Failures", "owner": "fixer", "priority": 3},
    "style": {"label": "Style / Lint", "owner": "qa", "priority": 4},
}


def load_report():
    f = Path(REPORTS_DIR) / "full_report.json"
    if not f.exists():
        console.print("[red]No report. Run: python3 antigravity/collect_reports.py[/red]")
        sys.exit(1)
    return json.loads(f.read_text())


def cluster_issues(issues):
    groups = defaultdict(list)
    for i in issues:
        groups[i.get("cluster", "style")].append(i)
    tasks, tid = [], 1
    for key, items in sorted(groups.items(), key=lambda x: CLUSTERS.get(x[0], {}).get("priority", 9)):
        cd = CLUSTERS.get(key, {"label": key, "owner": "coder", "priority": 5})
        files = list(set(i["file"] for i in items))
        tasks.append(
            {
                "id": f"TASK-{tid:03d}",
                "cluster": key,
                "label": cd["label"],
                "owner_agent": cd["owner"],
                "priority": cd["priority"],
                "status": "backlog",
                "issue_count": len(items),
                "files_affected": files,
                "acceptance_criteria": [
                    f"All {len(items)} issues resolved",
                    "Tests pass",
                    "No regressions",
                ],
                "issues": items[:50],
            }
        )
        tid += 1
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_tasks": len(tasks),
        "total_issues": len(issues),
        "tasks": tasks,
    }


def generate_kanban(data):
    lines = [
        "# 🔥 ANTIGRAVITY – Issues Kanban",
        f"_Generated: {data['generated_at']}_ | Issues: {data['total_issues']}",
        "",
        "## 📋 Backlog",
        "",
    ]
    for t in data["tasks"]:
        icon = {1: "🔴", 2: "🟡", 3: "🔵", 4: "⚪"}.get(t["priority"], "⚫")
        lines += [
            f"### {icon} {t['id']}: {t['label']}",
            f"- Owner: `{t['owner_agent'].upper()}` | Issues: {t['issue_count']}",
            f"- Files: {', '.join(f'`{f}`' for f in t['files_affected'][:10])}",
            "",
        ]
    lines += ["## 🚧 In Progress", "", "## ✅ Done", ""]
    return "\n".join(lines)


def main():
    report = load_report()
    issues = report.get("issues", [])
    if not issues:
        console.print("[yellow]No issues found![/yellow]")
        return
    data = cluster_issues(issues)
    Path(ISSUES_FILE).write_text(json.dumps(data, indent=2))
    Path(KANBAN_FILE).write_text(generate_kanban(data))
    console.print(f"[green]✓[/green] {ISSUES_FILE}\n[green]✓[/green] {KANBAN_FILE}")
    table = Table(title="🧬 CLUSTERED TASKS", border_style="cyan")
    table.add_column("ID")
    table.add_column("Cluster")
    table.add_column("Owner")
    table.add_column("Issues", justify="right")
    for t in data["tasks"]:
        table.add_row(t["id"], t["label"], t["owner_agent"].upper(), str(t["issue_count"]))
    console.print(table)


if __name__ == "__main__":
    main()
