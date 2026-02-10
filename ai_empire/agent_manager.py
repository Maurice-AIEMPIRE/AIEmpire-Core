"""
Agent Manager - Agent Lifecycle & Registry.

Manages the creation, registration, health monitoring, and
decommissioning of all agents in the empire.

Usage:
    manager = AgentManager()
    agent_id = manager.register_agent("legal-timeline", role="legal", capabilities=["timeline"])
    manager.report_task_completion(agent_id, score=8.5)
    leaderboard = manager.get_leaderboard()
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

STATE_DIR = Path(__file__).parent.parent / "workflow-system" / "state"
RANKINGS_FILE = STATE_DIR / "agent_rankings.json"


@dataclass
class AgentRecord:
    """Represents a registered agent."""
    agent_id: str
    name: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "idle"  # idle | active | paused | decommissioned
    registered_at: str = ""
    tasks_completed: int = 0
    total_score: float = 0.0
    last_active: str = ""

    def average_score(self) -> float:
        if self.tasks_completed == 0:
            return 0.0
        return self.total_score / self.tasks_completed


class AgentManager:
    """Central registry and lifecycle manager for all agents."""

    def __init__(self):
        self.agents: Dict[str, AgentRecord] = {}
        self._next_id = 1
        self._load_rankings()

    def register_agent(
        self,
        name: str,
        role: str = "general",
        capabilities: Optional[List[str]] = None,
    ) -> str:
        """Register a new agent. Returns the agent_id."""
        agent_id = f"agent-{self._next_id:04d}"
        self._next_id += 1

        record = AgentRecord(
            agent_id=agent_id,
            name=name,
            role=role,
            capabilities=capabilities or [],
            status="idle",
            registered_at=datetime.now().isoformat(),
        )
        self.agents[agent_id] = record
        logger.info(f"Registered agent: {agent_id} ({name}, role={role})")
        self._save_rankings()
        return agent_id

    def report_task_completion(self, agent_id: str, score: float = 5.0, task_summary: str = "") -> None:
        """Record a completed task for an agent."""
        if agent_id not in self.agents:
            raise RuntimeError(f"Agent {agent_id} not registered. Register before reporting.")
        agent = self.agents[agent_id]
        agent.tasks_completed += 1
        agent.total_score += score
        agent.last_active = datetime.now().isoformat()
        logger.info(f"Agent {agent_id} completed task (score={score}): {task_summary[:60]}")
        self._save_rankings()

    def get_leaderboard(self, top_n: int = 20) -> List[Dict]:
        """Return agents ranked by average score."""
        ranked = sorted(
            self.agents.values(),
            key=lambda a: a.average_score(),
            reverse=True,
        )
        return [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "role": a.role,
                "tasks_completed": a.tasks_completed,
                "average_score": round(a.average_score(), 2),
                "status": a.status,
            }
            for a in ranked[:top_n]
        ]

    def set_status(self, agent_id: str, status: str) -> None:
        """Update an agent's status."""
        if agent_id not in self.agents:
            raise RuntimeError(f"Agent {agent_id} not registered.")
        self.agents[agent_id].status = status
        self.agents[agent_id].last_active = datetime.now().isoformat()

    def get_agent(self, agent_id: str) -> Optional[AgentRecord]:
        """Get an agent record by ID."""
        return self.agents.get(agent_id)

    def get_agents_by_role(self, role: str) -> List[AgentRecord]:
        """Get all agents with a specific role."""
        return [a for a in self.agents.values() if a.role == role and a.status != "decommissioned"]

    def decommission(self, agent_id: str) -> None:
        """Mark an agent as decommissioned."""
        if agent_id in self.agents:
            self.agents[agent_id].status = "decommissioned"
            self._save_rankings()

    def get_stats(self) -> Dict:
        """Return summary statistics."""
        active = [a for a in self.agents.values() if a.status != "decommissioned"]
        return {
            "total_agents": len(self.agents),
            "active_agents": len(active),
            "total_tasks": sum(a.tasks_completed for a in active),
            "avg_score": round(
                sum(a.average_score() for a in active) / max(len(active), 1), 2
            ),
            "roles": list(set(a.role for a in active)),
        }

    def _save_rankings(self) -> None:
        """Persist rankings to disk."""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "updated": datetime.now().isoformat(),
            "agents": {
                aid: {
                    "name": a.name,
                    "role": a.role,
                    "status": a.status,
                    "tasks_completed": a.tasks_completed,
                    "total_score": a.total_score,
                    "average_score": round(a.average_score(), 2),
                    "registered_at": a.registered_at,
                    "last_active": a.last_active,
                }
                for aid, a in self.agents.items()
            },
        }
        RANKINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _load_rankings(self) -> None:
        """Load previous rankings from disk."""
        if not RANKINGS_FILE.exists():
            return
        try:
            data = json.loads(RANKINGS_FILE.read_text())
            for aid, info in data.get("agents", {}).items():
                record = AgentRecord(
                    agent_id=aid,
                    name=info.get("name", "unknown"),
                    role=info.get("role", "general"),
                    status=info.get("status", "idle"),
                    tasks_completed=info.get("tasks_completed", 0),
                    total_score=info.get("total_score", 0.0),
                    registered_at=info.get("registered_at", ""),
                    last_active=info.get("last_active", ""),
                )
                self.agents[aid] = record
            if self.agents:
                max_id = max(int(aid.split("-")[1]) for aid in self.agents)
                self._next_id = max_id + 1
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Could not load agent rankings: {e}")
