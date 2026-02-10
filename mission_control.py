#!/usr/bin/env python3
"""
MISSION CONTROL SYSTEM
======================
Scans ALL active & open tasks across systems and creates a single-page overview.
Maurice's AI Empire - 2026
"""

import os
import json
import asyncio
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TaskCategory(Enum):
    """Task categories for classification"""
    BUILD = "BUILD"
    FIX = "FIX"
    AUTOMATE = "AUTOMATE"
    CONTENT = "CONTENT"
    STRATEGY = "STRATEGY"


class Priority(Enum):
    """Priority levels"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class Task:
    """Represents a single task"""
    id: str
    title: str
    source: str
    category: TaskCategory
    priority: Priority
    impact: int  # 1-10
    urgency: int  # 1-10
    effort: int  # 1-10
    deadline: Optional[str] = None
    blocker: bool = False
    blocker_reason: Optional[str] = None
    cost_risk: Optional[str] = None
    description: Optional[str] = None

    @property
    def priority_score(self) -> float:
        """Calculate priority score: IMPACT > URGENCY > EFFORT (lower is better)"""
        return (10 - self.impact) * 100 + (10 - self.urgency) * 10 + self.effort


class MissionControl:
    """Mission Control System for scanning and prioritizing all tasks"""

    def __init__(self, repo_path: str = "/home/runner/work/AIEmpire-Core/AIEmpire-Core"):
        self.repo_path = Path(repo_path)
        self.tasks: List[Task] = []
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.repository = os.getenv("GITHUB_REPO", "mauricepfeifer-ctrl/AIEmpire-Core")

    async def scan_all_sources(self):
        """Scan all task sources"""
        print("Scanning all task sources...")

        await asyncio.gather(
            self.scan_github_issues(),
            self.scan_workflow_runs(),
            self.scan_task_files(),
            self.scan_docker_services(),
            self.scan_brain_system(),
            self.scan_logs()
        )

        print(f"Found {len(self.tasks)} total tasks")

    async def scan_github_issues(self):
        """Scan GitHub issues for open tasks"""
        print("  Scanning GitHub issues...")

        try:
            result = subprocess.run(
                ["gh", "issue", "list", "--json", "number,title,labels,state,createdAt"],
                capture_output=True, text=True, timeout=30,
                cwd=self.repo_path
            )

            if result.returncode == 0 and result.stdout.strip():
                issues = json.loads(result.stdout)

                for issue in issues:
                    if issue.get("state") == "OPEN":
                        labels = [l.get("name", "").lower() for l in issue.get("labels", [])]
                        category = self._categorize_from_labels(labels)

                        is_blocker = any("blocker" in l or "bug" in l or "critical" in l for l in labels)

                        task = Task(
                            id=f"GH-{issue['number']}",
                            title=issue["title"],
                            source="GitHub Issues",
                            category=category,
                            priority=Priority.HIGH if is_blocker else Priority.MEDIUM,
                            impact=8 if is_blocker else 6,
                            urgency=9 if is_blocker else 5,
                            effort=5,
                            blocker=is_blocker,
                            blocker_reason="Critical issue" if is_blocker else None
                        )
                        self.tasks.append(task)
        except Exception as e:
            print(f"    Could not scan GitHub issues: {e}")

    async def scan_workflow_runs(self):
        """Scan GitHub Actions workflow runs"""
        print("  Scanning workflow runs...")

        try:
            result = subprocess.run(
                ["gh", "run", "list", "--limit", "10", "--json", "name,status,conclusion"],
                capture_output=True, text=True, timeout=30,
                cwd=self.repo_path
            )

            if result.returncode == 0 and result.stdout.strip():
                runs = json.loads(result.stdout)

                failed_runs = [r for r in runs if r.get("conclusion") == "failure"]

                for run in failed_runs:
                    task = Task(
                        id=f"WF-{run['name'][:20]}",
                        title=f"Fix workflow: {run['name']}",
                        source="GitHub Actions",
                        category=TaskCategory.FIX,
                        priority=Priority.HIGH,
                        impact=7,
                        urgency=8,
                        effort=4,
                        blocker=True,
                        blocker_reason="Workflow failing"
                    )
                    self.tasks.append(task)
        except Exception as e:
            print(f"    Could not scan workflows: {e}")

    async def scan_task_files(self):
        """Scan atomic-reactor task files"""
        print("  Scanning task files...")

        tasks_dir = self.repo_path / "atomic-reactor" / "tasks"
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.yaml"):
                if task_file.name.startswith("._"):
                    continue

                try:
                    import yaml
                    with open(task_file) as f:
                        data = yaml.safe_load(f)

                    if data and isinstance(data, dict):
                        task = Task(
                            id=f"TASK-{task_file.stem}",
                            title=data.get("name", task_file.stem),
                            source="Atomic Reactor",
                            category=TaskCategory.BUILD,
                            priority=Priority.MEDIUM,
                            impact=data.get("impact", 5),
                            urgency=3,
                            effort=data.get("effort", 5),
                            description=data.get("description", "")
                        )
                        self.tasks.append(task)
                except Exception as e:
                    print(f"    Could not read {task_file}: {e}")

    async def scan_docker_services(self):
        """Scan Docker services for issues"""
        print("  Scanning Docker services...")

        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "json"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            container = json.loads(line)
                            if "exited" in container.get("State", "").lower():
                                task = Task(
                                    id=f"DOCKER-{container.get('Names', 'unknown')[:20]}",
                                    title=f"Restart Docker: {container.get('Names', 'unknown')}",
                                    source="Docker",
                                    category=TaskCategory.FIX,
                                    priority=Priority.MEDIUM,
                                    impact=5,
                                    urgency=6,
                                    effort=2,
                                    cost_risk="Container downtime"
                                )
                                self.tasks.append(task)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"    Could not scan Docker: {e}")

    async def scan_brain_system(self):
        """Scan brain system for pending tasks"""
        print("  Scanning brain system...")

        db_path = Path.home() / ".openclaw/brain-system/synapses.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                c = conn.cursor()
                c.execute('SELECT COUNT(*) FROM synapses WHERE processed = 0')
                pending = c.fetchone()[0]

                if pending > 5:
                    task = Task(
                        id="BRAIN-BACKLOG",
                        title=f"Process {pending} pending brain synapses",
                        source="Brain System",
                        category=TaskCategory.AUTOMATE,
                        priority=Priority.MEDIUM,
                        impact=6,
                        urgency=5,
                        effort=3
                    )
                    self.tasks.append(task)

                conn.close()
            except Exception as e:
                print(f"    Could not scan brain system: {e}")

    async def scan_logs(self):
        """Scan logs for errors"""
        print("  Scanning logs...")

        log_paths = [
            self.repo_path / "logs",
            Path("/var/log"),
        ]

        error_count = 0
        for log_dir in log_paths:
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    try:
                        with open(log_file) as f:
                            content = f.read()
                            if "ERROR" in content or "CRITICAL" in content:
                                error_count += 1
                    except Exception:
                        pass

        if error_count > 0:
            task = Task(
                id="LOGS-ERRORS",
                title=f"Review {error_count} log files with errors",
                source="System Logs",
                category=TaskCategory.FIX,
                priority=Priority.LOW,
                impact=4,
                urgency=3,
                effort=2
            )
            self.tasks.append(task)

    def _categorize_from_labels(self, labels: List[str]) -> TaskCategory:
        """Categorize task based on labels"""
        label_text = " ".join(labels).lower()

        if any(word in label_text for word in ["bug", "fix", "error", "broken"]):
            return TaskCategory.FIX
        elif any(word in label_text for word in ["content", "post", "blog", "social"]):
            return TaskCategory.CONTENT
        elif any(word in label_text for word in ["automation", "workflow", "ci", "cd"]):
            return TaskCategory.AUTOMATE
        elif any(word in label_text for word in ["strategy", "plan", "roadmap", "vision"]):
            return TaskCategory.STRATEGY
        else:
            return TaskCategory.BUILD

    def prioritize_tasks(self):
        """Prioritize all tasks by IMPACT > URGENCY > EFFORT"""
        self.tasks.sort(key=lambda t: t.priority_score)

    def get_top_blockers(self, limit: int = 10) -> List[Task]:
        """Get top blockers"""
        blockers = [t for t in self.tasks if t.blocker]
        return sorted(blockers, key=lambda t: t.priority_score)[:limit]

    def get_top_levers(self, limit: int = 10) -> List[Task]:
        """Get tasks with highest impact"""
        return sorted(self.tasks, key=lambda t: -t.impact)[:limit]

    def get_time_critical(self) -> List[Task]:
        """Get time-critical tasks with deadlines"""
        return [t for t in self.tasks if t.deadline]

    def get_cost_risks(self) -> List[Task]:
        """Get tasks with cost risks"""
        return [t for t in self.tasks if t.cost_risk]

    def get_by_category(self, category: TaskCategory, limit: int = 5) -> List[Task]:
        """Get tasks by category, limited to top N"""
        category_tasks = [t for t in self.tasks if t.category == category]
        return sorted(category_tasks, key=lambda t: t.priority_score)[:limit]

    def generate_dashboard(self) -> str:
        """Generate mission control dashboard"""
        self.prioritize_tasks()

        dashboard = "# MISSION CONTROL - System Overview\n\n"
        dashboard += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

        # Overview statistics
        dashboard += "## Overview\n\n"
        dashboard += f"- **Total Open Tasks:** {len(self.tasks)}\n"
        dashboard += f"- **Blockers:** {len([t for t in self.tasks if t.blocker])}\n"
        dashboard += f"- **High Priority:** {len([t for t in self.tasks if t.priority in [Priority.CRITICAL, Priority.HIGH]])}\n"
        dashboard += f"- **Time-Critical:** {len(self.get_time_critical())}\n"
        dashboard += f"- **Cost Risks:** {len(self.get_cost_risks())}\n\n"

        # Top 10 Blockers
        dashboard += "## Top 10 Blockers\n\n"
        blockers = self.get_top_blockers(10)
        if blockers:
            dashboard += "| ID | Task | Source | Cause |\n"
            dashboard += "|---|---|---|---|\n"
            for task in blockers:
                dashboard += f"| {task.id} | {task.title[:40]} | {task.source} | {task.blocker_reason or 'N/A'} |\n"
        else:
            dashboard += "*No blockers identified*\n"
        dashboard += "\n"

        # Top 10 Levers
        dashboard += "## Top 10 Levers (Highest Impact)\n\n"
        levers = self.get_top_levers(10)
        if levers:
            dashboard += "| ID | Task | Impact | Category |\n"
            dashboard += "|---|---|:---:|---|\n"
            for task in levers:
                dashboard += f"| {task.id} | {task.title[:40]} | {task.impact}/10 | {task.category.value} |\n"
        else:
            dashboard += "*No high-impact tasks*\n"
        dashboard += "\n"

        # Time-Critical Tasks
        time_critical = self.get_time_critical()
        if time_critical:
            dashboard += "## Time-Critical Tasks\n\n"
            dashboard += "| ID | Task | Deadline |\n"
            dashboard += "|---|---|---|\n"
            for task in time_critical:
                dashboard += f"| {task.id} | {task.title[:40]} | {task.deadline} |\n"
            dashboard += "\n"

        # Cost Risks
        cost_risks = self.get_cost_risks()
        if cost_risks:
            dashboard += "## Cost Risks\n\n"
            dashboard += "| ID | Task | Risk |\n"
            dashboard += "|---|---|---|\n"
            for task in cost_risks:
                dashboard += f"| {task.id} | {task.title[:40]} | {task.cost_risk} |\n"
            dashboard += "\n"

        # Tasks by Category
        dashboard += "## Tasks by Category (Top 5 Each)\n\n"

        for category in TaskCategory:
            tasks = self.get_by_category(category, limit=5)
            dashboard += f"### {category.value}\n\n"

            if tasks:
                dashboard += "| ID | Task | Priority | Impact | Urgency | Effort |\n"
                dashboard += "|---|---|:---:|:---:|:---:|:---:|\n"
                for task in tasks:
                    dashboard += f"| {task.id} | {task.title[:30]} | {task.priority.name} | {task.impact} | {task.urgency} | {task.effort} |\n"
            else:
                dashboard += "*No tasks in this category*\n"
            dashboard += "\n"

        # Next 90 Minutes Action List
        dashboard += "## What to do NOW (Next 90 Minutes)\n\n"
        dashboard += self.generate_action_list()

        return dashboard

    def generate_action_list(self, limit: int = 7) -> str:
        """Generate prioritized action list for next 90 minutes"""
        action_tasks = sorted(self.tasks, key=lambda t: t.priority_score)[:limit]

        action_list = ""
        for i, task in enumerate(action_tasks, 1):
            icon = "BLOCKER" if task.blocker else "HIGH" if task.impact >= 8 else "-"
            action_list += f"{i}. **{task.title}** ({task.category.value})\n"
            action_list += f"   - Source: {task.source}\n"
            action_list += f"   - Priority: Impact={task.impact}, Urgency={task.urgency}, Effort={task.effort}\n"
            if task.blocker:
                action_list += f"   - BLOCKER: {task.blocker_reason}\n"
            action_list += "\n"

        return action_list

    def export_to_json(self, output_path: Optional[Path] = None) -> str:
        """Export all task data to JSON for knowledge graph"""
        if output_path is None:
            output_path = self.repo_path / "mission_control_data.json"

        data = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_tasks": len(self.tasks),
                "by_category": {
                    cat.value: len([t for t in self.tasks if t.category == cat])
                    for cat in TaskCategory
                },
                "by_priority": {
                    pri.name: len([t for t in self.tasks if t.priority == pri])
                    for pri in Priority
                },
                "blockers": len([t for t in self.tasks if t.blocker]),
                "time_critical": len(self.get_time_critical()),
                "cost_risks": len(self.get_cost_risks())
            },
            "tasks": [asdict(task) for task in self.tasks]
        }

        for task in data["tasks"]:
            task["category"] = task["category"].value if hasattr(task["category"], "value") else str(task["category"])
            task["priority"] = task["priority"].name if hasattr(task["priority"], "name") else str(task["priority"])

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        return str(output_path)


async def main():
    """Main entry point"""
    print("=" * 70)
    print("MISSION CONTROL SYSTEM")
    print("=" * 70)
    print()

    mc = MissionControl()

    await mc.scan_all_sources()

    print("\nGenerating dashboard...\n")
    dashboard = mc.generate_dashboard()
    print(dashboard)

    print("Exporting to JSON...")
    json_path = mc.export_to_json()
    print(f"Data exported to: {json_path}")

    dashboard_path = mc.repo_path / "MISSION_CONTROL.md"
    with open(dashboard_path, 'w') as f:
        f.write(dashboard)
    print(f"Dashboard saved to: {dashboard_path}")


if __name__ == "__main__":
    asyncio.run(main())
