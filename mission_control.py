#!/usr/bin/env python3
"""
MISSION CONTROL SYSTEM
Multi-dimensional task prioritization and strategic oversight.
Maurice's AI Empire - 2026
"""

import os
import json
import asyncio
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import yaml


class TaskCategory(Enum):
    """Task categories for strategic organization."""
    BUILD = "Build"
    FIX = "Fix"
    AUTOMATE = "Automate"
    CONTENT = "Content"
    STRATEGY = "Strategy"


class Priority(Enum):
    """Priority levels."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class Task:
    """Task data structure with intelligent prioritization."""
    title: str
    category: TaskCategory
    priority: Priority
    impact: int = 5  # 1-10
    urgency: int = 5  # 1-10
    effort: int = 5  # 1-10
    deadline: Optional[str] = None
    cost_risk: Optional[str] = None
    blocker: bool = False
    source: str = ""
    url: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None

    @property
    def priority_score(self) -> float:
        """Calculate priority score based on impact, urgency, and effort.

        Formula: (10-impact)*100 + (10-urgency)*10 + effort
        Lower score = higher priority (impact dominates, then urgency, then effort).
        """
        return (10 - self.impact) * 100 + (10 - self.urgency) * 10 + self.effort


class MissionControl:
    """Complete mission control system for task management and prioritization."""

    def __init__(self, repo_path: str = "."):
        """Initialize Mission Control.

        Args:
            repo_path: Path to the repository (default: current directory)
        """
        self.repo_path = Path(repo_path)
        self.tasks: List[Task] = []
        # Prefer GitHub Actions env defaults, but work locally with `gh auth login` too.
        self.github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or ""
        self.github_repo = os.getenv("GITHUB_REPO") or os.getenv("GITHUB_REPOSITORY") or ""

    async def scan_all_sources(self) -> None:
        """Scan all available sources for tasks."""
        print("🔍 Scanning all sources...")

        await self.scan_github_issues()
        await self.scan_workflow_runs()
        self.scan_task_files()
        self.scan_docker_services()
        self.scan_brain_system()
        self.scan_logs()

        print(f"✅ Found {len(self.tasks)} total tasks")

    async def scan_github_issues(self) -> None:
        """Scan GitHub issues using gh CLI."""
        try:
            result = subprocess.run(
                ["gh", "issue", "list", "--json", "number,title,body,labels,state,createdAt"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                print(f"⚠️  GitHub scan failed: {result.stderr}")
                return

            issues = json.loads(result.stdout) if result.stdout else []

            for issue in issues:
                # Categorize by labels
                labels = issue.get("labels", [])
                label_names = [label.get("name", "") for label in labels]
                label_names_lc = [name.lower() for name in label_names]

                category = TaskCategory.BUILD
                if any(x in label_names_lc for x in ["fix", "bug"]):
                    category = TaskCategory.FIX
                elif any(x in label_names_lc for x in ["automate", "automation"]):
                    category = TaskCategory.AUTOMATE
                elif any(x in label_names_lc for x in ["content"]):
                    category = TaskCategory.CONTENT
                elif any(x in label_names_lc for x in ["strategy"]):
                    category = TaskCategory.STRATEGY

                priority = Priority.MEDIUM
                if any("critical" in x for x in label_names_lc):
                    priority = Priority.CRITICAL
                elif any("high" in x for x in label_names_lc):
                    priority = Priority.HIGH
                elif any("low" in x for x in label_names_lc):
                    priority = Priority.LOW

                issue_number = issue.get("number")
                issue_url = None
                if self.github_repo and issue_number:
                    issue_url = f"https://github.com/{self.github_repo}/issues/{issue_number}"

                task = Task(
                    title=issue.get("title", ""),
                    category=category,
                    priority=priority,
                    source="GitHub Issue",
                    url=issue_url,
                    description=issue.get("body", "")[:200],
                    tags=label_names,
                )
                self.tasks.append(task)

            print(f"✅ GitHub: Found {len(issues)} issues")
        except Exception as e:
            print(f"❌ GitHub scan error: {e}")

    async def scan_workflow_runs(self) -> None:
        """Scan GitHub workflow runs using gh CLI."""
        try:
            result = subprocess.run(
                ["gh", "run", "list", "--json", "name,status,conclusion,createdAt"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return

            runs = json.loads(result.stdout) if result.stdout else []

            for run in runs:
                conclusion = (run.get("conclusion") or "").lower()
                if conclusion == "failure":
                    task = Task(
                        title=f"Fix Failed Workflow: {run.get('name')}",
                        category=TaskCategory.FIX,
                        priority=Priority.HIGH,
                        impact=8,
                        urgency=8,
                        effort=6,
                        source="GitHub Workflows",
                        blocker=True,
                    )
                    self.tasks.append(task)

            print(f"✅ Workflows: Scanned {len(runs)} runs")
        except Exception as e:
            print(f"❌ Workflow scan error: {e}")

    def scan_task_files(self) -> None:
        """Scan atomic-reactor/tasks/*.yaml files."""
        task_dir = self.repo_path / "atomic-reactor" / "tasks"

        if not task_dir.exists():
            print(f"⚠️  Task directory not found: {task_dir}")
            return

        try:
            count = 0
            for task_file in task_dir.glob("*.yaml"):
                if task_file.name.startswith("._"):
                    continue
                try:
                    with open(task_file) as f:
                        data = yaml.safe_load(f)
                        if data:
                            category_key = str(data.get("category", "BUILD")).upper()
                            priority_key = str(data.get("priority", "MEDIUM")).upper()

                            category = (
                                TaskCategory[category_key]
                                if category_key in TaskCategory.__members__
                                else TaskCategory.BUILD
                            )
                            priority = (
                                Priority[priority_key]
                                if priority_key in Priority.__members__
                                else Priority.MEDIUM
                            )

                            task = Task(
                                title=data.get("title", task_file.stem),
                                category=category,
                                priority=priority,
                                impact=data.get("impact", 5),
                                urgency=data.get("urgency", 5),
                                effort=data.get("effort", 5),
                                deadline=data.get("deadline"),
                                cost_risk=data.get("cost_risk"),
                                source="Task File",
                                url=str(task_file),
                                description=data.get("description", ""),
                                tags=data.get("tags", []),
                            )
                            self.tasks.append(task)
                            count += 1
                except Exception as e:
                    print(f"⚠️  Error reading {task_file}: {e}")

            print(f"✅ Tasks: Found {count} task files")
        except Exception as e:
            print(f"❌ Task file scan error: {e}")

    def scan_docker_services(self) -> None:
        """Scan Docker services using docker ps."""
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                print("⚠️  Docker not available or failed")
                return

            services: List[Dict[str, Any]] = []
            for line in (result.stdout or "").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    services.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

            for service in services:
                status = str(service.get("Status", "") or "")
                state = str(service.get("State", "") or "")
                status_lc = status.lower()
                state_lc = state.lower()
                if "exited" in status_lc or "dead" in status_lc or state_lc in {"exited", "dead"}:
                    name = service.get("Names") or service.get("Name") or "unknown"
                    task = Task(
                        title=f"Restart Docker Service: {name}",
                        category=TaskCategory.FIX,
                        priority=Priority.HIGH,
                        impact=7,
                        urgency=7,
                        effort=3,
                        source="Docker",
                        blocker=True,
                    )
                    self.tasks.append(task)

            print(f"✅ Docker: Scanned {len(services)} services")
        except Exception as e:
            print(f"⚠️  Docker scan error: {e}")

    def scan_brain_system(self) -> None:
        """Scan Brain System synapses.db."""
        brain_db = Path.home() / ".openclaw" / "brain-system" / "synapses.db"

        if not brain_db.exists():
            print(f"⚠️  Brain system not found: {brain_db}")
            return

        try:
            conn = sqlite3.connect(brain_db)
            cursor = conn.cursor()

            # Try to find relevant tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' LIMIT 10"
            )
            tables = cursor.fetchall()

            if tables:
                print(f"✅ Brain System: Found {len(tables)} tables")
            conn.close()
        except Exception as e:
            print(f"⚠️  Brain system scan error: {e}")

    def scan_logs(self) -> None:
        """Scan log files for ERROR/CRITICAL."""
        log_patterns = [
            self.repo_path / "logs" / "*.log",
            self.repo_path / "*.log",
        ]

        error_count = 0
        for pattern in log_patterns:
            for log_file in self.repo_path.glob(str(pattern).replace(str(self.repo_path) + "/", "")):
                try:
                    with open(log_file) as f:
                        for line in f:
                            if "ERROR" in line or "CRITICAL" in line:
                                error_count += 1
                                if error_count <= 5:  # Only create tasks for first 5 errors
                                    task = Task(
                                        title=f"Log Error in {log_file.name}",
                                        category=TaskCategory.FIX,
                                        priority=Priority.HIGH,
                                        impact=6,
                                        urgency=6,
                                        effort=4,
                                        source="Logs",
                                    )
                                    self.tasks.append(task)
                except Exception as e:
                    pass

        if error_count > 0:
            print(f"✅ Logs: Found {error_count} error entries")

    def prioritize_tasks(self) -> None:
        """Sort tasks by priority score."""
        # Lower score = higher priority.
        self.tasks.sort(key=lambda t: t.priority_score)

    def get_top_blockers(self, limit: int = 10) -> List[Task]:
        """Get top blocker tasks."""
        blockers = [t for t in self.tasks if t.blocker]
        blockers.sort(key=lambda t: t.priority_score)
        return blockers[:limit]

    def get_top_levers(self, limit: int = 10) -> List[Task]:
        """Get highest impact tasks (levers)."""
        by_impact = sorted(self.tasks, key=lambda t: t.impact, reverse=True)
        return by_impact[:limit]

    def get_time_critical(self) -> List[Task]:
        """Get tasks with deadlines coming soon."""
        critical = []
        now = datetime.now()

        for task in self.tasks:
            if task.deadline:
                try:
                    deadline = datetime.fromisoformat(task.deadline)
                    if deadline < now + timedelta(days=7):
                        critical.append(task)
                except:
                    pass

        critical.sort(key=lambda t: t.deadline or "")
        return critical

    def get_cost_risks(self) -> List[Task]:
        """Get tasks with cost risks."""
        return [t for t in self.tasks if t.cost_risk]

    def get_by_category(self, category: TaskCategory, limit: int = 5) -> List[Task]:
        """Get tasks by category."""
        cat_tasks = [t for t in self.tasks if t.category == category]
        cat_tasks.sort(key=lambda t: t.priority_score)
        return cat_tasks[:limit]

    def generate_dashboard(self) -> str:
        """Generate markdown dashboard."""
        self.prioritize_tasks()

        dashboard = "# 🎯 Mission Control Dashboard\n\n"
        dashboard += f"**Generated:** {datetime.now().isoformat()}\n\n"

        # Summary stats
        blocker_count = sum(1 for t in self.tasks if t.blocker)
        dashboard += "## 📊 Summary Stats\n\n"
        dashboard += f"- **Total Tasks:** {len(self.tasks)}\n"
        dashboard += f"- **Blockers:** {blocker_count}\n"
        dashboard += f"- **Time Critical:** {len(self.get_time_critical())}\n"
        dashboard += f"- **Cost Risks:** {len(self.get_cost_risks())}\n\n"

        # Top blockers
        dashboard += "## 🚫 Top Blockers\n\n"
        blockers = self.get_top_blockers(5)
        if blockers:
            for i, task in enumerate(blockers, 1):
                dashboard += f"{i}. **{task.title}** ({task.category.value})\n"
                dashboard += f"   - Impact: {task.impact}/10 | Urgency: {task.urgency}/10\n"
                if task.url:
                    dashboard += f"   - [View]({task.url})\n"
                dashboard += "\n"
        else:
            dashboard += "✅ No blockers identified\n\n"

        # Top levers
        dashboard += "## 🎯 Top Levers (High Impact)\n\n"
        levers = self.get_top_levers(5)
        for i, task in enumerate(levers, 1):
            dashboard += f"{i}. **{task.title}** (Impact: {task.impact}/10)\n"
            dashboard += f"   - Category: {task.category.value}\n"
            if task.url:
                dashboard += f"   - [View]({task.url})\n"
            dashboard += "\n"

        # By category
        dashboard += "## 📁 By Category\n\n"
        for cat in TaskCategory:
            cat_tasks = self.get_by_category(cat, 5)
            if cat_tasks:
                dashboard += f"### {cat.value}\n"
                for task in cat_tasks:
                    dashboard += f"- {task.title}\n"
                dashboard += "\n"

        # Time critical
        critical = self.get_time_critical()
        if critical:
            dashboard += "## ⏰ Time Critical (Due <7 days)\n\n"
            for task in critical[:5]:
                dashboard += f"- **{task.title}** - Due: {task.deadline}\n"
            dashboard += "\n"

        # Cost risks
        risks = self.get_cost_risks()
        if risks:
            dashboard += "## 💰 Cost Risks\n\n"
            for task in risks[:5]:
                dashboard += f"- {task.title} - Risk: {task.cost_risk}\n"
            dashboard += "\n"

        return dashboard

    def generate_action_list(self, limit: int = 7) -> str:
        """Generate next 90 minutes action list."""
        self.prioritize_tasks()

        action_list = "# ⚡ Next 90 Minutes - Action List\n\n"
        action_list += f"**Generated:** {datetime.now().isoformat()}\n\n"

        # Filter by quick wins and critical items
        candidates = []
        for task in self.tasks:
            if task.blocker or task.priority in [Priority.CRITICAL, Priority.HIGH]:
                if task.effort <= 5:  # Quick tasks
                    candidates.append(task)

        candidates.sort(key=lambda t: t.priority_score)

        action_list += f"## Your Next {limit} Actions\n\n"

        for i, task in enumerate(candidates[:limit], 1):
            action_list += f"{i}. **{task.title}**\n"
            action_list += f"   - Category: {task.category.value}\n"
            action_list += f"   - Effort: {task.effort}/10 | Impact: {task.impact}/10\n"
            if task.url:
                action_list += f"   - [Details]({task.url})\n"
            action_list += "\n"

        if len(candidates) < limit:
            action_list += f"\n📝 Only {len(candidates)} high-priority quick tasks available.\n"

        return action_list

    def export_to_json(self, filename: str = "mission_control_data.json") -> None:
        """Export tasks to JSON."""
        self.prioritize_tasks()

        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tasks": len(self.tasks),
                "blockers": sum(1 for t in self.tasks if t.blocker),
                "time_critical": len(self.get_time_critical()),
                "cost_risks": len(self.get_cost_risks()),
            },
            "tasks": [
                {
                    **asdict(task),
                    "category": task.category.name,
                    "priority": task.priority.name,
                    "priority_score": task.priority_score,
                }
                for task in self.tasks
            ],
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Exported to {filename}")


async def main():
    """Main entry point."""
    print("=" * 60)
    print("MISSION CONTROL SYSTEM")
    print("=" * 60)
    print()

    # Initialize Mission Control
    mission = MissionControl()

    # Run comprehensive scan
    await mission.scan_all_sources()

    # Generate outputs
    print("\n📊 Generating outputs...")

    # Generate and save dashboard
    dashboard = mission.generate_dashboard()
    action_list = mission.generate_action_list()
    combined = f"{dashboard}\n\n---\n\n{action_list}\n"
    with open("MISSION_CONTROL.md", "w") as f:
        f.write(combined)
    print("✅ Dashboard saved to MISSION_CONTROL.md")

    # Generate action list
    print("\n" + action_list)

    # Export to JSON
    mission.export_to_json()

    print("\n" + "=" * 60)
    print("Mission Control scan complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
