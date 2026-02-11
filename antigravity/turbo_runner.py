"""
Turbo Workflow Runner
=====================
Execute workflow steps with turbo annotations for auto-execution.

Annotations (in workflow markdown):
  // turbo       → Auto-run this single step
  // turbo-all   → Auto-run ALL subsequent run_command steps
  // safe        → Mark as safe to auto-run (no confirmation)
  // dangerous   → Always require user confirmation

Inspired by Google Antigravity's workflow turbo system.

Usage:
    runner = TurboRunner()
    runner.load_workflow("deploy.md")
    runner.run()  # Auto-runs turbo steps, prompts for others
"""

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).parent.parent
WORKFLOWS_DIR = PROJECT_ROOT / "antigravity" / "_workflows"
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    index: int
    description: str
    command: str = ""
    turbo: bool = False
    safe: bool = False
    dangerous: bool = False
    status: str = "pending"  # pending, running, done, failed, skipped
    output: str = ""
    exit_code: int = -1
    duration_ms: float = 0.0


@dataclass
class Workflow:
    """A workflow with annotated steps."""
    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    turbo_all: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%S")


class TurboRunner:
    """
    Executes workflow steps with turbo auto-execution.

    Safe commands that auto-run without confirmation:
    - python -m compileall, pytest, ruff, git status, git diff
    - ls, cat, echo, pwd, which, npm test, npm run build

    Dangerous commands that always require confirmation:
    - rm, git push, docker, sudo, kill, drop, delete
    """

    SAFE_COMMANDS = [
        "python", "pytest", "ruff", "mypy", "black", "isort",
        "git status", "git diff", "git log", "git branch",
        "ls", "cat", "echo", "pwd", "which", "type",
        "npm test", "npm run build", "npm run lint",
        "node", "pip list", "pip show",
    ]

    DANGEROUS_PATTERNS = [
        r"\brm\b", r"\bgit\s+push\b", r"\bgit\s+reset\b",
        r"\bdocker\b", r"\bsudo\b", r"\bkill\b",
        r"\bdrop\b", r"\bdelete\b", r"\btruncate\b",
        r"--force", r"--hard", r"-rf",
    ]

    def __init__(self, workflows_dir: Optional[Path] = None):
        self.workflows_dir = workflows_dir or WORKFLOWS_DIR
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def parse_workflow(self, content: str, name: str = "unnamed") -> Workflow:
        """Parse a markdown workflow with turbo annotations."""
        lines = content.strip().split("\n")
        workflow = Workflow(name=name)
        turbo_all = False

        # Extract description from YAML frontmatter
        if lines and lines[0].strip() == "---":
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    lines = lines[i + 1:]
                    break
                if line.startswith("description:"):
                    workflow.description = line.split(":", 1)[1].strip()

        step_idx = 0
        for line in lines:
            stripped = line.strip()

            # Check for turbo-all annotation
            if "// turbo-all" in stripped:
                turbo_all = True
                workflow.turbo_all = True
                continue

            # Check for numbered step
            match = re.match(r"^(\d+)\.\s+(.+)$", stripped)
            if not match:
                # Check for turbo annotation on next step
                if "// turbo" in stripped and "turbo-all" not in stripped:
                    # Next step will be turbo
                    continue
                continue

            description = match.group(2)

            # Extract command from backticks
            cmd_match = re.search(r"`(.+?)`", description)
            command = cmd_match.group(1) if cmd_match else ""

            # Check annotations
            is_turbo = turbo_all or "// turbo" in stripped
            is_safe = "// safe" in stripped
            is_dangerous = "// dangerous" in stripped

            step = WorkflowStep(
                index=step_idx,
                description=description,
                command=command,
                turbo=is_turbo,
                safe=is_safe,
                dangerous=is_dangerous,
            )

            # Auto-detect safety
            if not is_dangerous and command:
                if any(command.strip().startswith(safe) for safe in self.SAFE_COMMANDS):
                    step.safe = True

            workflow.steps.append(step)
            step_idx += 1

        return workflow

    def load_workflow(self, filename: str) -> Workflow:
        """Load a workflow from the workflows directory."""
        path = self.workflows_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Workflow not found: {path}")
        content = path.read_text()
        return self.parse_workflow(content, name=filename)

    def save_workflow(self, workflow: Workflow) -> Path:
        """Save a workflow to disk."""
        path = self.workflows_dir / f"{workflow.name}.json"
        data = {
            "name": workflow.name,
            "description": workflow.description,
            "turbo_all": workflow.turbo_all,
            "created_at": workflow.created_at,
            "steps": [
                {
                    "index": s.index,
                    "description": s.description,
                    "command": s.command,
                    "turbo": s.turbo,
                    "safe": s.safe,
                    "dangerous": s.dangerous,
                    "status": s.status,
                    "output": s.output[:1000],  # Truncate large outputs
                    "exit_code": s.exit_code,
                    "duration_ms": s.duration_ms,
                }
                for s in workflow.steps
            ],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to auto-execute."""
        cmd = command.strip().lower()

        # Check dangerous patterns first
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, cmd):
                return False

        # Check safe prefixes
        for safe in self.SAFE_COMMANDS:
            if cmd.startswith(safe.lower()):
                return True

        return False

    def run_step(self, step: WorkflowStep, timeout: float = 120.0) -> WorkflowStep:
        """Execute a single workflow step."""
        if not step.command:
            step.status = "skipped"
            return step

        step.status = "running"
        start = time.time()

        try:
            result = subprocess.run(
                step.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(PROJECT_ROOT),
            )
            step.output = result.stdout + result.stderr
            step.exit_code = result.returncode
            step.status = "done" if result.returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            step.output = f"Command timed out after {timeout}s"
            step.exit_code = -1
            step.status = "failed"
        except Exception as exc:
            step.output = str(exc)
            step.exit_code = -1
            step.status = "failed"

        step.duration_ms = (time.time() - start) * 1000
        return step

    def run(
        self,
        workflow: Workflow,
        auto_turbo: bool = True,
        dry_run: bool = False,
    ) -> Workflow:
        """
        Execute a workflow.

        Args:
            workflow: The workflow to execute
            auto_turbo: Auto-execute turbo/safe steps
            dry_run: Just print what would run without executing
        """
        print(f"\n{'=' * 60}")
        print(f"TURBO RUNNER: {workflow.name}")
        print(f"{'=' * 60}")
        if workflow.description:
            print(f"  {workflow.description}")
        print(f"  Steps: {len(workflow.steps)}")
        print(f"  Turbo-all: {workflow.turbo_all}")
        print()

        for step in workflow.steps:
            should_auto = (
                auto_turbo
                and (step.turbo or step.safe or workflow.turbo_all)
                and not step.dangerous
            )

            icon = "⚡" if should_auto else "⏸️"
            safe_label = " [SAFE]" if step.safe else ""
            turbo_label = " [TURBO]" if step.turbo else ""
            danger_label = " [DANGEROUS]" if step.dangerous else ""

            print(f"  {icon} Step {step.index + 1}: {step.description}{safe_label}{turbo_label}{danger_label}")

            if step.command:
                print(f"     $ {step.command}")

            if dry_run:
                step.status = "skipped"
                continue

            if should_auto and step.command:
                self.run_step(step)
                status_icon = "✅" if step.status == "done" else "❌"
                print(f"     {status_icon} Exit: {step.exit_code} ({step.duration_ms:.0f}ms)")
                if step.output and step.status == "failed":
                    print(f"     Output: {step.output[:200]}")
            elif not should_auto and step.command:
                print("     [Requires manual execution or user confirmation]")
                step.status = "skipped"
            else:
                step.status = "skipped"

        # Summary
        done = sum(1 for s in workflow.steps if s.status == "done")
        failed = sum(1 for s in workflow.steps if s.status == "failed")
        skipped = sum(1 for s in workflow.steps if s.status == "skipped")

        print(f"\n  Summary: {done} done, {failed} failed, {skipped} skipped")
        print(f"{'=' * 60}\n")

        return workflow

    def create_workflow(
        self,
        name: str,
        description: str,
        steps: list[dict[str, Any]],
    ) -> Workflow:
        """Create and save a new workflow."""
        workflow = Workflow(name=name, description=description)

        for i, step_data in enumerate(steps):
            step = WorkflowStep(
                index=i,
                description=step_data.get("description", f"Step {i+1}"),
                command=step_data.get("command", ""),
                turbo=step_data.get("turbo", False),
                safe=step_data.get("safe", False),
                dangerous=step_data.get("dangerous", False),
            )
            # Auto-detect safety
            if step.command and not step.dangerous:
                step.safe = self.is_safe_command(step.command)
            workflow.steps.append(step)

        self.save_workflow(workflow)
        return workflow
