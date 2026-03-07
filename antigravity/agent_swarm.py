"""
Agent Swarm Architecture — 100+ Parallel Agents
=================================================
Instead of 1 system with big context window → 100 small agents in parallel

Key Insight (from Kimi):
  - 100 sub-agents
  - 1500+ parallel tool calls
  - 4.5x faster than sequential
  - NO memory limit (each agent tiny)
  - Cloud-backed (Google Drive, iCloud)

Architecture:
  Swarm Controller
    ├─ Agent 1 (Task A)
    ├─ Agent 2 (Task B)
    ├─ Agent 3 (Task C)
    ... 100 agents ...
    └─ Agent 100 (Task Z)

  All coordinated, all parallel, all cloud-backed

Cost: $0 (Ollama only, no subscriptions)
Memory: Minimal (agents are lightweight)
Scale: Unlimited (add more agents = linear scale)
"""

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from antigravity.config import PROJECT_ROOT
from antigravity.offline_claude import OfflineClaude


class AgentRole(str, Enum):
    """Specialized agent roles."""
    ARCHITECT = "architect"
    CODER = "coder"
    ANALYST = "analyst"
    REVIEWER = "reviewer"
    CONTENT_WRITER = "content_writer"
    RESEARCHER = "researcher"
    EDITOR = "editor"
    VALIDATOR = "validator"


class TaskStatus(str, Enum):
    """Task lifecycle in swarm."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


@dataclass
class SwarmTask:
    """A single task for a swarm agent."""
    task_id: str
    role: AgentRole
    description: str
    prompt: str
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    agent_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0


@dataclass
class SwarmAgent:
    """A lightweight agent in the swarm."""
    agent_id: str
    role: AgentRole
    capacity: int = 5  # Can handle 5 concurrent tasks
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_runtime_seconds: float = 0.0
    last_active: float = field(default_factory=time.time)

    @property
    def is_available(self) -> bool:
        """Can this agent take more tasks?"""
        return self.active_tasks < self.capacity

    @property
    def efficiency(self) -> float:
        """Success rate of this agent."""
        total = self.completed_tasks + self.failed_tasks
        if total == 0:
            return 1.0
        return self.completed_tasks / total


class AgentSwarm:
    """
    Manages 100+ parallel agents.

    Usage:
        swarm = AgentSwarm(num_agents=100)

        # Add tasks
        task = SwarmTask(
            role=AgentRole.CONTENT_WRITER,
            description="Write YouTube script",
            prompt="Create a 10-minute script about..."
        )
        await swarm.add_task(task)

        # Run swarm (all tasks in parallel)
        results = await swarm.run()
    """

    SWARM_DIR = Path(PROJECT_ROOT) / "antigravity" / "_swarm"
    TASKS_LOG = SWARM_DIR / "tasks.jsonl"
    AGENTS_LOG = SWARM_DIR / "agents.json"
    RESULTS_LOG = SWARM_DIR / "results.jsonl"

    def __init__(self, num_agents: int = 100):
        self.agents: Dict[str, SwarmAgent] = {}
        self.tasks: Dict[str, SwarmTask] = {}
        self.pending_tasks: List[str] = []
        self.completed_results: List[Dict[str, Any]] = []

        # Create lightweight agents (just Ollama, not heavy processes)
        for i in range(num_agents):
            agent_id = f"agent_{i:03d}"
            role = list(AgentRole)[i % len(AgentRole)]
            self.agents[agent_id] = SwarmAgent(
                agent_id=agent_id,
                role=role,
                capacity=5,  # Each agent handles 5 tasks
            )

        self._ensure_directories()
        print(f"🐝 Swarm initialized: {num_agents} agents ready")

    def _ensure_directories(self) -> None:
        """Create swarm directories."""
        self.SWARM_DIR.mkdir(parents=True, exist_ok=True)

    async def add_task(
        self,
        role: AgentRole,
        description: str,
        prompt: str,
        dependencies: Optional[List[str]] = None,
    ) -> str:
        """Add task to swarm queue."""
        task_id = f"task_{uuid4().hex[:8]}"

        task = SwarmTask(
            task_id=task_id,
            role=role,
            description=description,
            prompt=prompt,
            dependencies=dependencies or [],
        )

        self.tasks[task_id] = task
        self.pending_tasks.append(task_id)

        return task_id

    async def run(self, max_concurrent: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Execute all tasks in parallel.

        Returns results from all agents.
        """
        print(f"\n🚀 Running swarm with {len(self.pending_tasks)} tasks")

        # Determine max concurrency
        if max_concurrent is None:
            max_concurrent = len(self.agents) * 5  # 100 agents * 5 tasks each

        # Create batches of tasks
        batches = [
            self.pending_tasks[i : i + max_concurrent]
            for i in range(0, len(self.pending_tasks), max_concurrent)
        ]

        all_results = []

        for batch_num, batch in enumerate(batches):
            print(f"\n📦 Batch {batch_num + 1}/{len(batches)} ({len(batch)} tasks)")

            # Execute batch in parallel
            batch_results = await asyncio.gather(
                *[self._execute_task(task_id) for task_id in batch],
                return_exceptions=False,
            )

            all_results.extend(batch_results)

        self._log_results(all_results)
        return all_results

    async def _execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute single task (assigned to available agent)."""
        task = self.tasks[task_id]

        # Find available agent
        agent = self._find_available_agent(task.role)
        if not agent:
            task.status = TaskStatus.FAILED
            task.error = "No available agents"
            return task.to_dict()

        # Assign to agent
        task.agent_id = agent.agent_id
        task.status = TaskStatus.ASSIGNED
        agent.active_tasks += 1

        try:
            # Check dependencies
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    raise ValueError(f"Dependency {dep_id} not found")
                dep = self.tasks[dep_id]
                if dep.status != TaskStatus.COMPLETED:
                    task.status = TaskStatus.PENDING
                    agent.active_tasks -= 1
                    return task.to_dict()

            # Execute with Offline Claude
            task.started_at = time.time()
            task.status = TaskStatus.RUNNING

            claude = OfflineClaude()
            result = await claude.think(
                task=task.prompt,
                role=task.role.value,
            )

            if "error" in result:
                task.error = result["error"]
                task.status = TaskStatus.FAILED
                agent.failed_tasks += 1
            else:
                task.result = result.get("response", "")
                task.status = TaskStatus.COMPLETED
                agent.completed_tasks += 1

        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            agent.failed_tasks += 1

        finally:
            task.completed_at = time.time()
            agent.active_tasks -= 1
            agent.total_runtime_seconds += task.duration_seconds
            agent.last_active = time.time()

        return task.to_dict()

    def _find_available_agent(self, role: AgentRole) -> Optional[SwarmAgent]:
        """Find an available agent (preferring matching role)."""
        # First, try to find agent with matching role
        for agent in self.agents.values():
            if agent.role == role and agent.is_available:
                return agent

        # Otherwise, find any available agent
        for agent in self.agents.values():
            if agent.is_available:
                return agent

        return None

    def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm status."""
        total_completed = sum(a.completed_tasks for a in self.agents.values())
        total_failed = sum(a.failed_tasks for a in self.agents.values())
        total_active = sum(a.active_tasks for a in self.agents.values())

        return {
            "agents": {
                "total": len(self.agents),
                "active": len([a for a in self.agents.values() if a.active_tasks > 0]),
                "available": len([a for a in self.agents.values() if a.is_available]),
            },
            "tasks": {
                "pending": len(self.pending_tasks),
                "active": total_active,
                "completed": total_completed,
                "failed": total_failed,
                "total": len(self.tasks),
            },
            "efficiency": {
                "avg_agent_efficiency": sum(a.efficiency for a in self.agents.values())
                / len(self.agents),
                "success_rate": (
                    total_completed / (total_completed + total_failed)
                    if (total_completed + total_failed) > 0
                    else 0
                ),
            },
        }

    def _log_results(self, results: List[Dict[str, Any]]) -> None:
        """Log all results."""
        try:
            with open(self.RESULTS_LOG, "a") as f:
                for result in results:
                    f.write(json.dumps(result) + "\n")

            with open(self.AGENTS_LOG, "w") as f:
                agents_dict = {
                    agent_id: asdict(agent) for agent_id, agent in self.agents.items()
                }
                json.dump(agents_dict, f, indent=2)

        except Exception as e:
            print(f"❌ Error logging results: {e}")

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics per agent."""
        return {
            agent_id: {
                "role": agent.role.value,
                "completed": agent.completed_tasks,
                "failed": agent.failed_tasks,
                "efficiency": agent.efficiency,
                "avg_time": (
                    agent.total_runtime_seconds / agent.completed_tasks
                    if agent.completed_tasks > 0
                    else 0
                ),
            }
            for agent_id, agent in self.agents.items()
        }


# ─── Global Swarm Instance ──────────────────────────────────────────────────

_global_swarm: Optional[AgentSwarm] = None


def get_swarm(num_agents: int = 100) -> AgentSwarm:
    """Get or create global swarm."""
    global _global_swarm
    if _global_swarm is None:
        _global_swarm = AgentSwarm(num_agents=num_agents)
    return _global_swarm


# ─── Example Usage ──────────────────────────────────────────────────────────

async def example_content_generation():
    """Example: Generate 100 pieces of content in parallel."""
    swarm = get_swarm(num_agents=100)

    print("\n" + "=" * 60)
    print("🐝 AGENT SWARM CONTENT GENERATION")
    print("=" * 60 + "\n")

    topics = [
        "AI Automation",
        "Business Scaling",
        "Deep Learning",
        "Startups",
        "Revenue Growth",
    ] * 20  # 100 topics

    # Add tasks
    print("Adding 100 content generation tasks...")
    for i, topic in enumerate(topics):
        await swarm.add_task(
            role=AgentRole.CONTENT_WRITER,
            description=f"Write content piece #{i+1}",
            prompt=f"Write a viral-worthy article about {topic}. Make it engaging, specific, and actionable. 500-1000 words.",
        )

    # Run swarm
    print("Running swarm (all agents working in parallel)...\n")
    results = await swarm.run()

    # Show results
    status = swarm.get_swarm_status()
    print("\n📊 FINAL SWARM STATUS:")
    print(json.dumps(status, indent=2))

    # Show sample result
    if results:
        first = results[0]
        print(f"\n✅ Sample result (Task {first['task_id']}):")
        print(f"   Status: {first['status']}")
        print(f"   Duration: {first['duration_seconds']:.2f}s")
        if first.get("result"):
            print(f"   Content: {first['result'][:200]}...")


if __name__ == "__main__":
    asyncio.run(example_content_generation())
