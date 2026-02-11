"""
Task Lifecycle Manager
=======================
Structured task execution with three phases:
  PLANNING → EXECUTION → VERIFICATION

Each task produces artifacts:
  - implementation_plan.md (planning phase)
  - task.md (living checklist: [ ] / [/] / [x])
  - walkthrough.md (verification/summary)

Inspired by Google Antigravity's Task Boundary system.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).parent.parent
TASKS_DIR = PROJECT_ROOT / "antigravity" / "_tasks"
TASKS_DIR.mkdir(parents=True, exist_ok=True)


class TaskPhase(str, Enum):
    PLANNING = "PLANNING"
    EXECUTION = "EXECUTION"
    VERIFICATION = "VERIFICATION"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked_on_user"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskStep:
    """A single step in a task checklist."""
    description: str
    status: str = "pending"  # pending, in_progress, done
    notes: str = ""

    @property
    def marker(self) -> str:
        return {"pending": "[ ]", "in_progress": "[/]", "done": "[x]"}[self.status]


@dataclass
class Task:
    """A structured task with lifecycle tracking."""
    task_id: str
    name: str
    summary: str
    phase: str = TaskPhase.PLANNING
    status: str = TaskStatus.PENDING
    steps: list[dict] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    completed_at: str = ""
    confidence: float = 0.0
    blocked_reason: str = ""
    files_changed: list[str] = field(default_factory=list)
    notifications: list[str] = field(default_factory=list)

    def __post_init__(self):
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


class TaskLifecycle:
    """
    Manages structured task execution with artifact generation.

    Usage:
        tl = TaskLifecycle()
        task = tl.create_task("fix-api", "Fix API auth bug", steps=[...])
        tl.start_planning(task.task_id)
        tl.save_plan(task.task_id, "## Plan\n1. Find auth module...")
        tl.start_execution(task.task_id)
        tl.complete_step(task.task_id, 0)
        tl.start_verification(task.task_id)
        tl.save_walkthrough(task.task_id, "## Summary\nFixed auth...")
        tl.complete_task(task.task_id)
    """

    def __init__(self, tasks_dir: Optional[Path] = None):
        self.tasks_dir = tasks_dir or TASKS_DIR
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def create_task(
        self,
        task_id: str,
        name: str,
        summary: str = "",
        steps: Optional[list[str]] = None,
    ) -> Task:
        """Create a new task with optional steps."""
        task = Task(
            task_id=task_id,
            name=name,
            summary=summary or name,
            steps=[{"description": s, "status": "pending", "notes": ""} for s in (steps or [])],
        )

        # Create task directory
        task_dir = self.tasks_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        self._save_task(task)
        self._generate_task_md(task)

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Load a task by ID."""
        meta_path = self.tasks_dir / task_id / "meta.json"
        if not meta_path.exists():
            return None
        with open(meta_path) as f:
            data = json.load(f)
        return Task(**data)

    def start_planning(self, task_id: str) -> Optional[Task]:
        """Transition task to PLANNING phase."""
        task = self.get_task(task_id)
        if not task:
            return None
        task.phase = TaskPhase.PLANNING
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_task(task)
        return task

    def save_plan(self, task_id: str, plan_content: str) -> None:
        """Save the implementation plan artifact."""
        plan_path = self.tasks_dir / task_id / "implementation_plan.md"
        header = f"# Implementation Plan: {task_id}\n\n"
        plan_path.write_text(header + plan_content)

    def start_execution(self, task_id: str) -> Optional[Task]:
        """Transition task to EXECUTION phase."""
        task = self.get_task(task_id)
        if not task:
            return None
        task.phase = TaskPhase.EXECUTION
        task.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_task(task)
        self._generate_task_md(task)
        return task

    def complete_step(self, task_id: str, step_index: int, notes: str = "") -> Optional[Task]:
        """Mark a step as completed."""
        task = self.get_task(task_id)
        if not task or step_index >= len(task.steps):
            return None
        task.steps[step_index]["status"] = "done"
        if notes:
            task.steps[step_index]["notes"] = notes
        task.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")

        # Calculate confidence from completion ratio
        done = sum(1 for s in task.steps if s["status"] == "done")
        task.confidence = done / len(task.steps) if task.steps else 0

        self._save_task(task)
        self._generate_task_md(task)
        return task

    def start_step(self, task_id: str, step_index: int) -> Optional[Task]:
        """Mark a step as in progress."""
        task = self.get_task(task_id)
        if not task or step_index >= len(task.steps):
            return None
        task.steps[step_index]["status"] = "in_progress"
        task.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_task(task)
        self._generate_task_md(task)
        return task

    def block_task(self, task_id: str, reason: str) -> Optional[Task]:
        """Block task on user input."""
        task = self.get_task(task_id)
        if not task:
            return None
        task.phase = TaskPhase.BLOCKED
        task.status = TaskStatus.BLOCKED
        task.blocked_reason = reason
        task.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_task(task)
        return task

    def start_verification(self, task_id: str) -> Optional[Task]:
        """Transition task to VERIFICATION phase."""
        task = self.get_task(task_id)
        if not task:
            return None
        task.phase = TaskPhase.VERIFICATION
        task.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_task(task)
        return task

    def save_walkthrough(self, task_id: str, content: str) -> None:
        """Save the walkthrough/summary artifact."""
        path = self.tasks_dir / task_id / "walkthrough.md"
        header = f"# Walkthrough: {task_id}\n\n"
        path.write_text(header + content)

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark task as completed."""
        task = self.get_task(task_id)
        if not task:
            return None
        task.phase = TaskPhase.COMPLETED
        task.status = TaskStatus.COMPLETED
        task.confidence = 1.0
        task.completed_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        task.updated_at = task.completed_at
        self._save_task(task)
        self._generate_task_md(task)
        return task

    def add_notification(self, task_id: str, message: str) -> None:
        """Add a notification message (like Antigravity's notify_user)."""
        task = self.get_task(task_id)
        if not task:
            return
        timestamp = time.strftime("%H:%M:%S")
        task.notifications.append(f"[{timestamp}] {message}")
        task.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_task(task)

    def list_tasks(self, status: Optional[str] = None) -> list[dict[str, Any]]:
        """List all tasks, optionally filtered by status."""
        tasks = []
        for task_dir in sorted(self.tasks_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            meta_path = task_dir / "meta.json"
            if not meta_path.exists():
                continue
            with open(meta_path) as f:
                data = json.load(f)
            if status and data.get("status") != status:
                continue
            done = sum(1 for s in data.get("steps", []) if s.get("status") == "done")
            total = len(data.get("steps", []))
            tasks.append({
                "task_id": data["task_id"],
                "name": data["name"],
                "phase": data.get("phase", "?"),
                "status": data.get("status", "?"),
                "progress": f"{done}/{total}",
                "confidence": data.get("confidence", 0),
            })
        return tasks

    def status_report(self) -> str:
        """Get formatted status of all tasks."""
        tasks = self.list_tasks()
        if not tasks:
            return "No tasks. Create one with tl.create_task()."

        lines = [
            "=" * 60,
            "TASK LIFECYCLE STATUS",
            "=" * 60,
        ]

        phase_icons = {
            "PLANNING": "📋", "EXECUTION": "🔨",
            "VERIFICATION": "✅", "COMPLETED": "🏁", "BLOCKED": "🚫",
        }

        for t in tasks:
            icon = phase_icons.get(t["phase"], "?")
            conf = f"{t['confidence']:.0%}"
            lines.append(
                f"  {icon} {t['task_id']:25s} | {t['phase']:13s} | "
                f"{t['progress']:5s} | {conf}"
            )

        active = sum(1 for t in tasks if t["status"] == "in_progress")
        done = sum(1 for t in tasks if t["status"] == "completed")
        lines.append(f"\n  Active: {active} | Completed: {done} | Total: {len(tasks)}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _save_task(self, task: Task) -> None:
        """Save task metadata."""
        meta_path = self.tasks_dir / task.task_id / "meta.json"
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, "w") as f:
            json.dump(asdict(task), f, indent=2)

    def _generate_task_md(self, task: Task) -> None:
        """Generate the living task.md checklist."""
        lines = [
            f"# Task: {task.name}",
            f"**ID**: {task.task_id}",
            f"**Phase**: {task.phase}",
            f"**Status**: {task.status}",
            f"**Confidence**: {task.confidence:.0%}",
            "",
            "## Checklist",
        ]

        markers = {"pending": "[ ]", "in_progress": "[/]", "done": "[x]"}
        for i, step in enumerate(task.steps):
            marker = markers.get(step["status"], "[ ]")
            lines.append(f"- {marker} {step['description']}")
            if step.get("notes"):
                lines.append(f"  > {step['notes']}")

        if task.files_changed:
            lines.extend(["", "## Files Changed"])
            for f in task.files_changed:
                lines.append(f"- `{f}`")

        if task.notifications:
            lines.extend(["", "## Notifications"])
            for n in task.notifications[-5:]:  # Last 5
                lines.append(f"- {n}")

        md_path = self.tasks_dir / task.task_id / "task.md"
        md_path.write_text("\n".join(lines) + "\n")
