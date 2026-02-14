"""
Autonomous Daemon — Continuous Operation Without Human Input
=============================================================
Runs 24/7, completes tasks autonomously, handles context limits gracefully.

Features:
  1. Persistent task queue
  2. Multi-model execution (Claude→Ollama fallback)
  3. Automatic checkpointing
  4. Context-aware continuation
  5. Self-healing on errors
  6. Work logging for audit trail

Perfect for:
  - Background automation
  - 24/7 lead generation
  - Continuous code improvement
  - Revenue stream operation
  - Unattended execution
"""

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional, List

from antigravity.config import PROJECT_ROOT
from antigravity.state_recovery import StateCheckpoint
from antigravity.resource_aware import get_executor
from antigravity.offline_claude import OfflineClaude, ClaudeRole


class TaskStatus(str, Enum):
    """Task lifecycle."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    DEFERRED = "deferred"


class TaskPriority(int, Enum):
    """Task priority levels."""
    CRITICAL = 10
    HIGH = 7
    NORMAL = 5
    LOW = 3
    BACKGROUND = 1


@dataclass
class AutonomousTask:
    """A task for autonomous daemon to execute."""
    task_id: str
    name: str
    description: str
    agent_role: str  # architect, coder, reviewer, analyst
    prompt: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None
    tokens_used: int = 0
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict:
        """Convert to dict for JSON storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AutonomousTask":
        """Create from dict."""
        return cls(**data)

    def duration_seconds(self) -> float:
        """How long did task take."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0


class AutonomousDaemon:
    """
    Background daemon that runs tasks autonomously.

    Usage:
        daemon = AutonomousDaemon()
        await daemon.add_task(
            name="Generate leads",
            description="Find 50 SaaS founders interested in automation",
            agent_role="analyst",
            prompt="Research and list..."
        )
        await daemon.run()  # Runs forever
    """

    TASK_QUEUE_FILE = Path(PROJECT_ROOT) / "antigravity" / "_daemon" / "queue.jsonl"
    WORK_LOG_FILE = Path(PROJECT_ROOT) / "antigravity" / "_daemon" / "work.jsonl"
    STATUS_FILE = Path(PROJECT_ROOT) / "antigravity" / "_daemon" / "status.json"

    def __init__(self):
        self.tasks: dict[str, AutonomousTask] = {}
        self.task_queue: List[str] = []
        self.claude = OfflineClaude()
        self.executor = get_executor()
        self.is_running = False
        self.start_time = time.time()
        self.tasks_completed = 0
        self.tasks_failed = 0

        self._ensure_directories()
        self._load_queue()

    def _ensure_directories(self) -> None:
        """Create daemon directories."""
        self.TASK_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_queue(self) -> None:
        """Load task queue from disk."""
        try:
            if self.TASK_QUEUE_FILE.exists():
                with open(self.TASK_QUEUE_FILE) as f:
                    for line in f:
                        data = json.loads(line)
                        task = AutonomousTask.from_dict(data)
                        self.tasks[task.task_id] = task
                        if task.status in (
                            TaskStatus.PENDING,
                            TaskStatus.PAUSED,
                        ):
                            self.task_queue.append(task.task_id)
        except Exception as e:
            print(f"⚠️  Error loading queue: {e}")

    def _save_queue(self) -> None:
        """Save task queue to disk."""
        try:
            with open(self.TASK_QUEUE_FILE, "w") as f:
                for task_id in self.task_queue:
                    if task_id in self.tasks:
                        task = self.tasks[task_id]
                        f.write(json.dumps(task.to_dict()) + "\n")
        except Exception as e:
            print(f"❌ Error saving queue: {e}")

    def _log_work(self, task: AutonomousTask) -> None:
        """Log completed work."""
        try:
            with open(self.WORK_LOG_FILE, "a") as f:
                log_entry = {
                    "timestamp": time.time(),
                    "task_id": task.task_id,
                    "name": task.name,
                    "status": task.status.value,
                    "duration": task.duration_seconds(),
                    "tokens": task.tokens_used,
                    "error": task.error,
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"❌ Error logging work: {e}")

    async def add_task(
        self,
        name: str,
        description: str,
        agent_role: str,
        prompt: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_id: Optional[str] = None,
    ) -> str:
        """Add new task to queue."""
        if not task_id:
            task_id = f"task_{int(time.time())}_{len(self.tasks)}"

        task = AutonomousTask(
            task_id=task_id,
            name=name,
            description=description,
            agent_role=agent_role,
            prompt=prompt,
            priority=priority,
        )

        self.tasks[task_id] = task
        self.task_queue.append(task_id)

        # Sort by priority
        self.task_queue.sort(
            key=lambda tid: -self.tasks[tid].priority.value,
            reverse=False,
        )

        self._save_queue()

        print(f"✓ Task added: {task_id} ({name})")
        return task_id

    async def run(self, max_runtime_hours: Optional[float] = None) -> None:
        """
        Run daemon forever (or for specified hours).

        Handles:
          - Task execution in priority order
          - Resource constraints (pauses if memory tight)
          - Automatic retries on failure
          - Graceful shutdown
          - Context limit handling
        """
        self.is_running = True
        print(f"\n{'='*60}")
        print("🤖 Autonomous Daemon Started")
        print(f"{'='*60}\n")

        start_time = time.time()

        try:
            while self.is_running:
                # Check runtime limit
                if max_runtime_hours:
                    elapsed = (time.time() - start_time) / 3600
                    if elapsed > max_runtime_hours:
                        print(f"⏱️  Runtime limit reached ({elapsed:.1f}h)")
                        break

                # Check resources
                resources = self.executor.get_system_resources()
                if resources.tier.value == "critical":
                    print("⚠️  System in CRITICAL state, pausing")
                    await asyncio.sleep(60)
                    continue

                # Get next task
                task_id = await self._get_next_task()
                if not task_id:
                    print("⏸️  No tasks, sleeping...")
                    await asyncio.sleep(300)  # Sleep 5 min
                    continue

                # Execute task
                task = self.tasks[task_id]
                await self._execute_task(task)

        except KeyboardInterrupt:
            print("\n⏹️  Daemon interrupted")
        except Exception as e:
            print(f"❌ Daemon error: {e}")
        finally:
            self.is_running = False
            self._save_status()
            print("\n✓ Daemon shut down cleanly")

    async def _get_next_task(self) -> Optional[str]:
        """Get next task from queue."""
        # Remove completed tasks from queue
        self.task_queue = [
            tid
            for tid in self.task_queue
            if self.tasks[tid].status
            not in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        ]

        # Return first pending task
        for task_id in self.task_queue:
            task = self.tasks[task_id]
            if task.status == TaskStatus.PENDING:
                return task_id

        return None

    async def _execute_task(self, task: AutonomousTask) -> None:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()

        print(f"\n🚀 {task.name}")
        print(f"   ID: {task.task_id}")
        print(f"   Role: {task.agent_role}")

        try:
            # Create checkpoint before execution
            checkpoint = StateCheckpoint(
                task.task_id,
                agent_key=task.agent_role,
                phase="EXECUTE",
            )

            # Execute with offline Claude
            result = await self.claude.think(
                task=task.prompt,
                role=ClaudeRole(task.agent_role),
                task_type="code" if "code" in task.agent_role else "reasoning",
            )

            if "error" in result:
                task.error = result["error"]
                task.status = TaskStatus.FAILED
                task.retry_count += 1

                if task.retry_count < task.max_retries:
                    print(f"  ⚠️  Failed, will retry (attempt {task.retry_count})")
                    task.status = TaskStatus.PENDING  # Re-queue
                else:
                    print(f"  ❌ Failed after {task.max_retries} retries")
                    self.tasks_failed += 1

            else:
                task.result = result.get("response", "")
                task.tokens_used = result.get("tokens_used", 0)
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()

                print(f"  ✓ Completed in {task.duration_seconds():.1f}s")
                print(f"  📊 Tokens: {task.tokens_used}")

                self.tasks_completed += 1

                # Save checkpoint of result
                checkpoint.save(
                    {
                        "result": task.result,
                        "tokens": task.tokens_used,
                        "completed": True,
                    },
                    phase="COMPLETED",
                )

        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            print(f"  ❌ Error: {e}")
            self.tasks_failed += 1

        finally:
            task.completed_at = time.time()
            self._log_work(task)
            self._save_queue()

    def _save_status(self) -> None:
        """Save daemon status."""
        runtime = time.time() - self.start_time

        status = {
            "is_running": self.is_running,
            "runtime_seconds": runtime,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "total_tasks": len(self.tasks),
            "tasks_pending": len(
                [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
            ),
            "last_status_update": time.time(),
        }

        with open(self.STATUS_FILE, "w") as f:
            json.dump(status, f, indent=2)

    def get_status(self) -> dict:
        """Get daemon status."""
        runtime = time.time() - self.start_time

        return {
            "is_running": self.is_running,
            "uptime_seconds": runtime,
            "tasks": {
                "completed": self.tasks_completed,
                "failed": self.tasks_failed,
                "pending": len(
                    [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
                ),
                "total": len(self.tasks),
            },
            "model": self.claude.model,
            "status_file": str(self.STATUS_FILE),
        }


# ─── Standalone CLI ────────────────────────────────────────────────────────

async def run_daemon(hours: Optional[float] = None) -> None:
    """Run daemon from command line."""
    daemon = AutonomousDaemon()

    # Load some example tasks if queue is empty
    if not daemon.task_queue:
        print("\n📋 Loading example tasks...\n")
        await daemon.add_task(
            name="Analyze system architecture",
            description="Review and analyze current system design",
            agent_role="architect",
            prompt="Review the AIEmpire-Core system architecture and suggest improvements for EUR 100M scale",
            priority=TaskPriority.HIGH,
        )

        await daemon.add_task(
            name="Identify optimization opportunities",
            description="Find code optimization opportunities",
            agent_role="coder",
            prompt="Analyze the antigravity module for performance optimization opportunities",
            priority=TaskPriority.NORMAL,
        )

    await daemon.run(max_runtime_hours=hours)


if __name__ == "__main__":
    import sys

    # Run daemon
    hours = float(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(run_daemon(hours))
