#!/usr/bin/env python3
"""
MISSION CONTROL - AI Empire Dashboard
Scans all sources, prioritizes tasks, generates actionable dashboard.
Maurice's AI Empire - 2026
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any


class TaskCategory(Enum):
    BUILD = "build"
    FIX = "fix"
    AUTOMATE = "automate"
    CONTENT = "content"
    STRATEGY = "strategy"


class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Task:
    id: str
    title: str
    source: str
    category: TaskCategory
    priority: Priority
    impact: int = 5       # 1-10
    urgency: int = 5      # 1-10
    effort: int = 5       # 1-10
    deadline: Optional[str] = None
    blocker: bool = False
    blocker_reason: str = ""
    cost_risk: float = 0.0
    description: str = ""

    @property
    def priority_score(self) -> int:
        """Lower score = higher priority. Combines impact, urgency, and effort."""
        return (10 - self.impact) * 100 + (10 - self.urgency) * 10 + self.effort


class MissionControl:
    """Central mission control that scans all sources and prioritizes tasks."""

    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or os.getenv(
            "REPO_PATH",
            "/home/runner/work/AIEmpire-Core/AIEmpire-Core"
        )
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_repo = os.getenv("GITHUB_REPO", "mauricepfeifer-ctrl/AIEmpire-Core")
        self.tasks: List[Task] = []
        self.scan_results: Dict[str, Any] = {}
        self.scan_time: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    async def scan_all_sources(self) -> List[Task]:
        """Run all scanners in parallel and collect tasks."""
        self.scan_time = datetime.utcnow()
        self.tasks = []
        self.scan_results = {}

        scanners = [
            self._scan_github_issues(),
            self._scan_workflow_runs(),
            self._scan_task_files(),
            self._scan_docker_services(),
            self._scan_brain_system(),
            self._scan_logs(),
        ]

        results = await asyncio.gather(*scanners, return_exceptions=True)
        scanner_names = [
            "github_issues", "workflow_runs", "task_files",
            "docker_services", "brain_system", "logs",
        ]

        for name, result in zip(scanner_names, results):
            if isinstance(result, Exception):
                self.scan_results[name] = {"error": str(result), "count": 0}
            elif isinstance(result, list):
                self.scan_results[name] = {"count": len(result)}
                self.tasks.extend(result)
            else:
                self.scan_results[name] = {"count": 0}

        self.tasks = self.prioritize_tasks(self.tasks)
        return self.tasks

    async def _scan_github_issues(self) -> List[Task]:
        """Scan open GitHub issues for tasks."""
        tasks: List[Task] = []
        try:
            cmd = [
                "gh", "issue", "list",
                "--repo", self.github_repo,
                "--state", "open",
                "--json", "number,title,labels,body,createdAt",
                "--limit", "50",
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                return tasks

            issues = json.loads(stdout.decode())
            for issue in issues:
                labels = [l.get("name", "") for l in issue.get("labels", [])]
                category = self._categorize_by_labels(labels)
                priority = self._priority_by_labels(labels)
                is_blocker = "blocker" in labels or "blocking" in labels

                task = Task(
                    id=f"gh-{issue['number']}",
                    title=issue.get("title", "Untitled"),
                    source="github-issues",
                    category=category,
                    priority=priority,
                    impact=8 if is_blocker else 5,
                    urgency=8 if is_blocker else 5,
                    effort=5,
                    blocker=is_blocker,
                    blocker_reason="Labeled as blocker" if is_blocker else "",
                    description=(issue.get("body", "") or "")[:200],
                )
                tasks.append(task)
        except FileNotFoundError:
            pass  # gh CLI not available
        except Exception:
            pass
        return tasks

    async def _scan_workflow_runs(self) -> List[Task]:
        """Scan recent GitHub Actions workflow runs for failures."""
        tasks: List[Task] = []
        try:
            cmd = [
                "gh", "run", "list",
                "--repo", self.github_repo,
                "--status", "failure",
                "--json", "databaseId,name,conclusion,createdAt,headBranch",
                "--limit", "20",
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                return tasks

            runs = json.loads(stdout.decode())
            for run in runs:
                task = Task(
                    id=f"wf-{run.get('databaseId', 'unknown')}",
                    title=f"Fix failed workflow: {run.get('name', 'unknown')}",
                    source="workflow-runs",
                    category=TaskCategory.FIX,
                    priority=Priority.HIGH,
                    impact=7,
                    urgency=7,
                    effort=3,
                    blocker=True,
                    blocker_reason=f"Workflow '{run.get('name')}' failed on {run.get('headBranch', 'unknown')}",
                    description=f"Conclusion: {run.get('conclusion', 'unknown')}",
                )
                tasks.append(task)
        except FileNotFoundError:
            pass
        except Exception:
            pass
        return tasks

    async def _scan_task_files(self) -> List[Task]:
        """Scan atomic-reactor task YAML files."""
        tasks: List[Task] = []
        task_dir = Path(self.repo_path) / "atomic-reactor" / "tasks"
        if not task_dir.exists():
            return tasks

        try:
            import yaml
        except ImportError:
            return tasks

        for yaml_file in task_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    continue

                task = Task(
                    id=f"task-{yaml_file.stem}",
                    title=data.get("name", yaml_file.stem),
                    source="atomic-reactor",
                    category=self._map_category(data.get("category", "build")),
                    priority=self._map_priority(data.get("priority", "medium")),
                    impact=int(data.get("impact", 5)),
                    urgency=int(data.get("urgency", 5)),
                    effort=int(data.get("effort", 5)),
                    deadline=data.get("deadline"),
                    description=(data.get("description", "") or "")[:200],
                )
                tasks.append(task)
            except Exception:
                continue
        return tasks

    async def _scan_docker_services(self) -> List[Task]:
        """Scan Docker services for issues."""
        tasks: List[Task] = []
        try:
            cmd = ["docker", "ps", "-a", "--format", "{{json .}}"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                return tasks

            for line in stdout.decode().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    container = json.loads(line)
                except json.JSONDecodeError:
                    continue

                status = container.get("Status", "")
                name = container.get("Names", "unknown")

                if "Exited" in status or "Dead" in status:
                    task = Task(
                        id=f"docker-{name}",
                        title=f"Restart stopped service: {name}",
                        source="docker",
                        category=TaskCategory.FIX,
                        priority=Priority.HIGH,
                        impact=7,
                        urgency=8,
                        effort=2,
                        blocker=True,
                        blocker_reason=f"Container {name} is {status}",
                        description=f"Image: {container.get('Image', 'unknown')}",
                    )
                    tasks.append(task)
        except FileNotFoundError:
            pass
        except Exception:
            pass
        return tasks

    async def _scan_brain_system(self) -> List[Task]:
        """Scan brain system synapses database for pending items."""
        tasks: List[Task] = []
        db_path = Path.home() / ".openclaw" / "brain-system" / "synapses.db"
        if not db_path.exists():
            return tasks

        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check for pending synapses
            cursor.execute(
                "SELECT id, title, category, priority, status FROM synapses "
                "WHERE status = 'pending' ORDER BY priority LIMIT 20"
            )
            rows = cursor.fetchall()

            for row in rows:
                syn_id, title, category, priority, status = row
                task = Task(
                    id=f"brain-{syn_id}",
                    title=title or f"Brain synapse {syn_id}",
                    source="brain-system",
                    category=self._map_category(category or "strategy"),
                    priority=self._map_priority(priority or "medium"),
                    impact=5,
                    urgency=5,
                    effort=5,
                    description=f"Synapse status: {status}",
                )
                tasks.append(task)

            conn.close()
        except Exception:
            pass
        return tasks

    async def _scan_logs(self) -> List[Task]:
        """Scan log files for errors and critical messages."""
        tasks: List[Task] = []
        log_dirs = [
            Path(self.repo_path) / "logs",
            Path.home() / ".openclaw" / "logs",
            Path("/var/log/openclaw"),
        ]

        for log_dir in log_dirs:
            if not log_dir.exists():
                continue
            for log_file in log_dir.glob("*.log"):
                try:
                    # Read last 200 lines
                    with open(log_file) as f:
                        lines = f.readlines()[-200:]

                    error_count = 0
                    critical_count = 0
                    last_error = ""
                    for line in lines:
                        if "ERROR" in line:
                            error_count += 1
                            last_error = line.strip()[:150]
                        if "CRITICAL" in line:
                            critical_count += 1
                            last_error = line.strip()[:150]

                    if error_count > 0 or critical_count > 0:
                        prio = Priority.CRITICAL if critical_count > 0 else Priority.HIGH
                        task = Task(
                            id=f"log-{log_file.stem}",
                            title=f"Errors in {log_file.name}: {error_count}E/{critical_count}C",
                            source="logs",
                            category=TaskCategory.FIX,
                            priority=prio,
                            impact=8 if critical_count > 0 else 6,
                            urgency=8 if critical_count > 0 else 5,
                            effort=3,
                            description=last_error,
                        )
                        tasks.append(task)
                except Exception:
                    continue
        return tasks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _categorize_by_labels(self, labels: List[str]) -> TaskCategory:
        label_set = {l.lower() for l in labels}
        if label_set & {"bug", "fix", "error", "broken"}:
            return TaskCategory.FIX
        if label_set & {"automation", "automate", "ci", "cd"}:
            return TaskCategory.AUTOMATE
        if label_set & {"content", "marketing", "x-twitter", "social"}:
            return TaskCategory.CONTENT
        if label_set & {"strategy", "planning", "revenue", "business"}:
            return TaskCategory.STRATEGY
        return TaskCategory.BUILD

    def _priority_by_labels(self, labels: List[str]) -> Priority:
        label_set = {l.lower() for l in labels}
        if label_set & {"critical", "p0", "urgent"}:
            return Priority.CRITICAL
        if label_set & {"high", "p1", "important"}:
            return Priority.HIGH
        if label_set & {"low", "p3", "minor"}:
            return Priority.LOW
        return Priority.MEDIUM

    def _map_category(self, cat: str) -> TaskCategory:
        mapping = {
            "build": TaskCategory.BUILD,
            "fix": TaskCategory.FIX,
            "automate": TaskCategory.AUTOMATE,
            "content": TaskCategory.CONTENT,
            "strategy": TaskCategory.STRATEGY,
        }
        return mapping.get(cat.lower(), TaskCategory.BUILD)

    def _map_priority(self, prio: str) -> Priority:
        mapping = {
            "critical": Priority.CRITICAL,
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW,
        }
        return mapping.get(prio.lower(), Priority.MEDIUM)

    # ------------------------------------------------------------------
    # Prioritization & Filtering
    # ------------------------------------------------------------------

    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority score (lower = higher priority)."""
        return sorted(tasks, key=lambda t: t.priority_score)

    def get_top_blockers(self, limit: int = 10) -> List[Task]:
        """Get top blocker tasks."""
        blockers = [t for t in self.tasks if t.blocker]
        return blockers[:limit]

    def get_top_levers(self, limit: int = 10) -> List[Task]:
        """Get highest-impact, lowest-effort tasks (best levers)."""
        scored = sorted(
            self.tasks,
            key=lambda t: (t.impact * 10 - t.effort * 5),
            reverse=True,
        )
        return scored[:limit]

    def get_time_critical(self) -> List[Task]:
        """Get tasks with approaching deadlines."""
        critical = []
        now = datetime.utcnow()
        for task in self.tasks:
            if task.deadline:
                try:
                    dl = datetime.fromisoformat(task.deadline)
                    if dl - now < timedelta(days=3):
                        critical.append(task)
                except (ValueError, TypeError):
                    pass
        return critical

    def get_cost_risks(self) -> List[Task]:
        """Get tasks with cost risk."""
        return [t for t in self.tasks if t.cost_risk > 0]

    def get_by_category(self, category: TaskCategory) -> List[Task]:
        """Get tasks by category."""
        return [t for t in self.tasks if t.category == category]

    # ------------------------------------------------------------------
    # Dashboard Generation
    # ------------------------------------------------------------------

    def generate_dashboard(self) -> str:
        """Generate a full markdown dashboard."""
        now = self.scan_time or datetime.utcnow()
        total = len(self.tasks)
        blockers = self.get_top_blockers()
        levers = self.get_top_levers()
        time_critical = self.get_time_critical()
        cost_risks = self.get_cost_risks()

        cat_counts = {}
        for cat in TaskCategory:
            cat_counts[cat.value] = len(self.get_by_category(cat))

        prio_counts = {}
        for prio in Priority:
            prio_counts[prio.value] = len([t for t in self.tasks if t.priority == prio])

        lines = []
        lines.append("# MISSION CONTROL DASHBOARD")
        lines.append(f"**Scan Time:** {now.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("")

        # Overview
        lines.append("## Overview")
        lines.append(f"- **Total Tasks:** {total}")
        lines.append(f"- **Blockers:** {len(blockers)}")
        lines.append(f"- **Time-Critical:** {len(time_critical)}")
        lines.append(f"- **Cost Risks:** {len(cost_risks)}")
        lines.append("")
        lines.append("### By Priority")
        for prio in Priority:
            lines.append(f"- {prio.value.upper()}: {prio_counts[prio.value]}")
        lines.append("")
        lines.append("### By Category")
        for cat in TaskCategory:
            lines.append(f"- {cat.value.upper()}: {cat_counts[cat.value]}")
        lines.append("")

        # Sources scanned
        lines.append("### Sources Scanned")
        for source, info in self.scan_results.items():
            status = "OK" if "error" not in info else f"ERROR: {info['error'][:60]}"
            lines.append(f"- {source}: {info.get('count', 0)} tasks ({status})")
        lines.append("")

        # Top Blockers
        lines.append("## Top 10 Blockers")
        if blockers:
            lines.append("| # | Task | Source | Priority | Impact | Reason |")
            lines.append("|---|------|--------|----------|--------|--------|")
            for i, t in enumerate(blockers[:10], 1):
                lines.append(
                    f"| {i} | {t.title[:50]} | {t.source} | {t.priority.value} | {t.impact}/10 | {t.blocker_reason[:40]} |"
                )
        else:
            lines.append("No blockers found.")
        lines.append("")

        # Top Levers
        lines.append("## Top 10 Levers (High Impact, Low Effort)")
        if levers:
            lines.append("| # | Task | Source | Impact | Effort | Score |")
            lines.append("|---|------|--------|--------|--------|-------|")
            for i, t in enumerate(levers[:10], 1):
                lever_score = t.impact * 10 - t.effort * 5
                lines.append(
                    f"| {i} | {t.title[:50]} | {t.source} | {t.impact}/10 | {t.effort}/10 | {lever_score} |"
                )
        else:
            lines.append("No tasks found.")
        lines.append("")

        # Time-Critical
        lines.append("## Time-Critical Tasks")
        if time_critical:
            for t in time_critical:
                lines.append(f"- **{t.title}** (deadline: {t.deadline})")
        else:
            lines.append("No time-critical tasks.")
        lines.append("")

        # Cost Risks
        lines.append("## Cost Risks")
        if cost_risks:
            for t in cost_risks:
                lines.append(f"- **{t.title}** - Risk: EUR {t.cost_risk:.2f}")
        else:
            lines.append("No cost risks identified.")
        lines.append("")

        # Tasks by Category
        lines.append("## Tasks by Category")
        for cat in TaskCategory:
            cat_tasks = self.get_by_category(cat)
            icon = {"build": "hammer", "fix": "wrench", "automate": "gear", "content": "pencil", "strategy": "chess"}.get(cat.value, "")
            lines.append(f"\n### {cat.value.upper()} ({len(cat_tasks)} tasks)")
            for t in cat_tasks[:5]:
                lines.append(f"- [{t.priority.value.upper()}] {t.title} (impact: {t.impact}, effort: {t.effort})")
            if len(cat_tasks) > 5:
                lines.append(f"- ... and {len(cat_tasks) - 5} more")
        lines.append("")

        # Action List
        lines.append("## 90-Minute Action List")
        action_list = self.generate_action_list()
        lines.append(action_list)
        lines.append("")

        lines.append("---")
        lines.append(f"*Generated by Mission Control at {now.strftime('%Y-%m-%d %H:%M UTC')}*")

        return "\n".join(lines)

    def generate_action_list(self) -> str:
        """Generate a prioritized 90-minute action list (top 7 tasks)."""
        top_tasks = self.tasks[:7]
        if not top_tasks:
            return "No tasks to act on."

        lines = []
        icons = {
            TaskCategory.FIX: "[FIX]",
            TaskCategory.BUILD: "[BUILD]",
            TaskCategory.AUTOMATE: "[AUTO]",
            TaskCategory.CONTENT: "[CONTENT]",
            TaskCategory.STRATEGY: "[STRATEGY]",
        }

        for i, task in enumerate(top_tasks, 1):
            icon = icons.get(task.category, "[TASK]")
            blocker_tag = " **BLOCKER**" if task.blocker else ""
            effort_min = task.effort * 3  # rough estimate: effort * 3 minutes
            lines.append(
                f"{i}. {icon} {task.title} (~{effort_min}min, impact: {task.impact}/10){blocker_tag}"
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_to_json(self) -> Dict[str, Any]:
        """Export complete scan data to JSON-serializable dict."""
        return {
            "scan_time": (self.scan_time or datetime.utcnow()).isoformat(),
            "total_tasks": len(self.tasks),
            "scan_results": self.scan_results,
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "source": t.source,
                    "category": t.category.value,
                    "priority": t.priority.value,
                    "impact": t.impact,
                    "urgency": t.urgency,
                    "effort": t.effort,
                    "deadline": t.deadline,
                    "blocker": t.blocker,
                    "blocker_reason": t.blocker_reason,
                    "cost_risk": t.cost_risk,
                    "description": t.description,
                    "priority_score": t.priority_score,
                }
                for t in self.tasks
            ],
            "summary": {
                "blockers": len(self.get_top_blockers()),
                "time_critical": len(self.get_time_critical()),
                "cost_risks": len(self.get_cost_risks()),
                "by_category": {
                    cat.value: len(self.get_by_category(cat))
                    for cat in TaskCategory
                },
                "by_priority": {
                    prio.value: len([t for t in self.tasks if t.priority == prio])
                    for prio in Priority
                },
            },
        }


async def main():
    """Main entry point - scan all sources and generate dashboard."""
    print("MISSION CONTROL - Starting scan...")
    print("=" * 60)

    mc = MissionControl()
    tasks = await mc.scan_all_sources()

    print(f"Scan complete. Found {len(tasks)} tasks.")
    print()

    # Generate dashboard
    dashboard = mc.generate_dashboard()

    # Save dashboard
    dashboard_path = Path(mc.repo_path) / "MISSION_CONTROL.md"
    try:
        with open(dashboard_path, "w") as f:
            f.write(dashboard)
        print(f"Dashboard saved to {dashboard_path}")
    except Exception as e:
        # Fallback to current directory
        fallback_path = Path.cwd() / "MISSION_CONTROL.md"
        with open(fallback_path, "w") as f:
            f.write(dashboard)
        print(f"Dashboard saved to {fallback_path}")

    # Export JSON data
    json_data = mc.export_to_json()
    json_path = Path(mc.repo_path) / "mission_control_data.json"
    try:
        with open(json_path, "w") as f:
            json.dump(json_data, f, indent=2)
        print(f"JSON data saved to {json_path}")
    except Exception as e:
        fallback_path = Path.cwd() / "mission_control_data.json"
        with open(fallback_path, "w") as f:
            json.dump(json_data, f, indent=2)
        print(f"JSON data saved to {fallback_path}")

    # Print dashboard to stdout
    print()
    print(dashboard)

    return mc


if __name__ == "__main__":
    asyncio.run(main())
