"""
Planning Mode — Inspired by Google Antigravity
================================================
Multi-phase workflow with approval gates, change classification,
and implementation plans. No code changes without a verified plan.

Phases:
  1. RESEARCH  — Analyze codebase, identify requirements
  2. PLAN      — Create implementation_plan with change classification
  3. APPROVE   — Human or AI approval gate (no bypass)
  4. EXECUTE   — Implement changes per approved plan
  5. VERIFY    — Cross-agent verification of results

Change Classification:
  [NEW]    — New file or component
  [MODIFY] — Change to existing file
  [DELETE] — Remove file or component
  [CONFIG] — Configuration change only

Based on patterns from:
  - Google Antigravity (planning-mode.txt)
  - Ryan Carson's "agents verify each other" principle
  - DeepReinforce IterX (iterative refinement)
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from antigravity.config import PROJECT_ROOT


# ─── Types ────────────────────────────────────────────────────────────────────

class Phase(str, Enum):
    RESEARCH = "RESEARCH"
    PLAN = "PLAN"
    APPROVE = "APPROVE"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ChangeType(str, Enum):
    NEW = "NEW"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    CONFIG = "CONFIG"


@dataclass
class PlannedChange:
    """A single planned change to a file."""
    file_path: str
    change_type: ChangeType
    description: str
    component: str = ""  # Group changes by component
    risk_level: str = "low"  # low, medium, high, critical
    dependencies: list = field(default_factory=list)
    estimated_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "file": self.file_path,
            "type": self.change_type.value,
            "description": self.description,
            "component": self.component,
            "risk": self.risk_level,
            "dependencies": self.dependencies,
        }


@dataclass
class ImplementationPlan:
    """Full implementation plan with approval gate."""
    task_id: str
    title: str
    objective: str
    phase: Phase = Phase.RESEARCH
    changes: list = field(default_factory=list)
    verification_strategy: str = ""
    approved_by: str = ""
    approved_at: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    execution_log: list = field(default_factory=list)
    result: Optional[dict] = None

    def add_change(self, change: PlannedChange):
        self.changes.append(change)

    def get_changes_by_component(self) -> dict[str, list]:
        """Group changes by component for organized review."""
        groups: dict[str, list] = {}
        for c in self.changes:
            comp = c.component or "general"
            groups.setdefault(comp, []).append(c)
        return groups

    def get_risk_summary(self) -> dict:
        """Summarize risk levels across all changes."""
        risks = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for c in self.changes:
            risks[c.risk_level] = risks.get(c.risk_level, 0) + 1
        return risks

    def approve(self, approver: str = "human"):
        """Mark plan as approved. Cannot be undone."""
        if self.phase != Phase.PLAN:
            raise ValueError(f"Cannot approve in phase {self.phase}. Must be in PLAN phase.")
        self.approved_by = approver
        self.approved_at = datetime.now().isoformat()
        self.phase = Phase.APPROVE

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "objective": self.objective,
            "phase": self.phase.value,
            "changes": [c.to_dict() for c in self.changes],
            "verification": self.verification_strategy,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "created_at": self.created_at,
            "execution_log": self.execution_log,
            "risk_summary": self.get_risk_summary(),
        }

    def to_markdown(self) -> str:
        """Generate a markdown implementation plan (like Antigravity's implementation_plan.md)."""
        lines = [
            f"# Implementation Plan: {self.title}",
            f"",
            f"**Task ID:** {self.task_id}",
            f"**Phase:** {self.phase.value}",
            f"**Created:** {self.created_at}",
            f"**Objective:** {self.objective}",
            f"",
            f"## Risk Summary",
            f"",
        ]

        risks = self.get_risk_summary()
        for level, count in risks.items():
            if count > 0:
                marker = {"low": "", "medium": "> [!IMPORTANT]", "high": "> [!WARNING]", "critical": "> [!CAUTION]"}
                lines.append(f"- **{level.upper()}**: {count} changes")

        lines.extend(["", "## Planned Changes", ""])

        for component, changes in self.get_changes_by_component().items():
            lines.append(f"### {component}")
            lines.append("")
            for c in changes:
                icon = {"NEW": "+", "MODIFY": "~", "DELETE": "-", "CONFIG": "#"}
                lines.append(f"- `[{c.change_type.value}]` **{c.file_path}**")
                lines.append(f"  {c.description}")
                if c.dependencies:
                    lines.append(f"  Dependencies: {', '.join(c.dependencies)}")
            lines.append("")

        if self.verification_strategy:
            lines.extend([
                "## Verification Strategy",
                "",
                self.verification_strategy,
                "",
            ])

        if self.approved_by:
            lines.extend([
                "## Approval",
                "",
                f"- **Approved by:** {self.approved_by}",
                f"- **Approved at:** {self.approved_at}",
                "",
            ])

        return "\n".join(lines)


# ─── Planning Mode Controller ─────────────────────────────────────────────────

class PlanningController:
    """
    Controls the multi-phase workflow.

    Usage:
        controller = PlanningController()
        plan = controller.create_plan("fix-auth", "Fix Auth Bug", "Fix login timeout")
        plan.add_change(PlannedChange("auth.py", ChangeType.MODIFY, "Add timeout handling"))
        controller.advance_to_plan(plan)
        plan.approve("claude")
        controller.advance_to_execute(plan)
        # ... execute changes ...
        controller.advance_to_verify(plan)
        # ... verify with cross-agent ...
        controller.complete(plan)
    """

    PLANS_DIR = Path(PROJECT_ROOT) / "workflow_system" / "plans"

    def __init__(self):
        self.PLANS_DIR.mkdir(parents=True, exist_ok=True)

    def create_plan(self, task_id: str, title: str, objective: str) -> ImplementationPlan:
        """Create a new plan in RESEARCH phase."""
        plan = ImplementationPlan(
            task_id=task_id,
            title=title,
            objective=objective,
            phase=Phase.RESEARCH,
        )
        self._save_plan(plan)
        return plan

    def advance_to_plan(self, plan: ImplementationPlan):
        """Move from RESEARCH to PLAN phase."""
        if plan.phase != Phase.RESEARCH:
            raise ValueError(f"Cannot advance to PLAN from {plan.phase}")
        if not plan.changes:
            raise ValueError("Cannot advance to PLAN without any planned changes")
        plan.phase = Phase.PLAN
        self._save_plan(plan)
        # Generate markdown plan file
        plan_md = plan.to_markdown()
        plan_file = self.PLANS_DIR / f"{plan.task_id}_plan.md"
        plan_file.write_text(plan_md)

    def advance_to_execute(self, plan: ImplementationPlan):
        """Move from APPROVE to EXECUTE phase. Requires approval."""
        if plan.phase != Phase.APPROVE:
            raise ValueError(f"Cannot execute from {plan.phase}. Must be APPROVED first.")
        if not plan.approved_by:
            raise ValueError("Plan must be approved before execution")
        plan.phase = Phase.EXECUTE
        self._save_plan(plan)

    def advance_to_verify(self, plan: ImplementationPlan):
        """Move from EXECUTE to VERIFY phase."""
        if plan.phase != Phase.EXECUTE:
            raise ValueError(f"Cannot verify from {plan.phase}")
        plan.phase = Phase.VERIFY
        self._save_plan(plan)

    def complete(self, plan: ImplementationPlan, result: Optional[dict] = None):
        """Mark plan as complete."""
        plan.phase = Phase.COMPLETE
        plan.result = result
        self._save_plan(plan)

    def fail(self, plan: ImplementationPlan, reason: str):
        """Mark plan as failed."""
        plan.phase = Phase.FAILED
        plan.execution_log.append({"event": "FAILED", "reason": reason, "ts": datetime.now().isoformat()})
        self._save_plan(plan)

    def load_plan(self, task_id: str) -> Optional[ImplementationPlan]:
        """Load a saved plan by task ID."""
        plan_file = self.PLANS_DIR / f"{task_id}.json"
        if not plan_file.exists():
            return None
        try:
            data = json.loads(plan_file.read_text())
            plan = ImplementationPlan(
                task_id=data["task_id"],
                title=data["title"],
                objective=data["objective"],
                phase=Phase(data["phase"]),
                created_at=data.get("created_at", ""),
                approved_by=data.get("approved_by", ""),
                approved_at=data.get("approved_at", ""),
                execution_log=data.get("execution_log", []),
                verification_strategy=data.get("verification", ""),
            )
            for c in data.get("changes", []):
                plan.add_change(PlannedChange(
                    file_path=c["file"],
                    change_type=ChangeType(c["type"]),
                    description=c["description"],
                    component=c.get("component", ""),
                    risk_level=c.get("risk", "low"),
                    dependencies=c.get("dependencies", []),
                ))
            return plan
        except (json.JSONDecodeError, KeyError):
            return None

    def list_plans(self) -> list[dict]:
        """List all saved plans."""
        plans = []
        for f in self.PLANS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                plans.append({
                    "task_id": data["task_id"],
                    "title": data["title"],
                    "phase": data["phase"],
                    "created": data.get("created_at", ""),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(plans, key=lambda x: x.get("created", ""), reverse=True)

    def _save_plan(self, plan: ImplementationPlan):
        """Atomic save of plan state."""
        plan_file = self.PLANS_DIR / f"{plan.task_id}.json"
        tmp_file = plan_file.with_suffix(".json.tmp")
        try:
            tmp_file.write_text(json.dumps(plan.to_dict(), indent=2, ensure_ascii=False))
            tmp_file.rename(plan_file)
        except Exception:
            if tmp_file.exists():
                tmp_file.unlink()
            raise


# ─── Auto-Execute Annotations (from Antigravity) ──────────────────────────────

def parse_turbo_annotations(workflow_text: str) -> dict:
    """
    Parse Antigravity-style auto-execute annotations.

    Annotations:
      // turbo      — Auto-execute this single step
      // turbo-all  — Auto-execute all remaining steps

    Returns:
      {"turbo_steps": [step_indices], "turbo_all_from": step_index or None}
    """
    result = {"turbo_steps": [], "turbo_all_from": None}
    for i, line in enumerate(workflow_text.splitlines()):
        stripped = line.strip()
        if "// turbo-all" in stripped:
            result["turbo_all_from"] = i
        elif "// turbo" in stripped:
            result["turbo_steps"].append(i)
    return result
