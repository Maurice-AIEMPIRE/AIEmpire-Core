"""
Ant Protocol - Message Protocol
================================
Defines all message types between Queen, Workers, and Colony.
Uses Redis pub/sub for real-time + Redis lists for persistence.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class TaskPriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class WorkerStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    DEAD = "dead"


class MessageType(str, Enum):
    # Queen -> Colony
    TASK_CREATED = "task_created"
    TASK_CANCELLED = "task_cancelled"
    COLONY_COMMAND = "colony_command"
    PHEROMONE_UPDATE = "pheromone_update"

    # Worker -> Colony
    TASK_CLAIMED = "task_claimed"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    WORKER_HEARTBEAT = "worker_heartbeat"
    WORKER_REGISTERED = "worker_registered"

    # Colony -> All
    COLONY_STATUS = "colony_status"


@dataclass
class AntTask:
    """A task in the colony task board."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    title: str = ""
    description: str = ""
    task_type: str = "general"  # general, content, code, research, revenue
    priority: int = TaskPriority.NORMAL
    status: str = TaskStatus.PENDING
    required_skills: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)

    # Assignment
    claimed_by: str = ""
    claimed_at: float = 0.0

    # Result
    result: dict = field(default_factory=dict)
    error: str = ""

    # Timing
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    deadline: float = 0.0  # 0 = no deadline
    max_duration: int = 300  # seconds

    # Pheromone
    pheromone_strength: float = 1.0

    # Retry
    attempts: int = 0
    max_attempts: int = 3

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, data: str | dict) -> "AntTask":
        if isinstance(data, str):
            data = json.loads(data)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @property
    def is_expired(self) -> bool:
        if self.deadline and time.time() > self.deadline:
            return True
        if self.claimed_at and self.status == TaskStatus.CLAIMED:
            return (time.time() - self.claimed_at) > self.max_duration
        return False

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


@dataclass
class WorkerInfo:
    """Worker ant registration info."""
    worker_id: str = field(default_factory=lambda: f"ant-{str(uuid.uuid4())[:8]}")
    name: str = ""
    skills: list = field(default_factory=list)
    model: str = ""
    status: str = WorkerStatus.IDLE
    current_task: str = ""
    tasks_completed: int = 0
    tasks_failed: int = 0
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    load: float = 0.0  # 0.0-1.0

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, data: str | dict) -> "WorkerInfo":
        if isinstance(data, str):
            data = json.loads(data)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ColonyMessage:
    """Message in the colony pub/sub channel."""
    msg_type: str = ""
    sender: str = ""
    payload: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    colony_id: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, data: str | dict) -> "ColonyMessage":
        if isinstance(data, str):
            data = json.loads(data)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PheromoneTrail:
    """Pheromone trail - guides workers to high-priority tasks."""
    trail_id: str = ""
    task_type: str = ""
    strength: float = 1.0
    direction: str = ""  # "attract" or "repel"
    created_at: float = field(default_factory=time.time)
    decay_rate: float = 0.1  # strength lost per hour
    metadata: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, data: str | dict) -> "PheromoneTrail":
        if isinstance(data, str):
            data = json.loads(data)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @property
    def current_strength(self) -> float:
        age_hours = (time.time() - self.created_at) / 3600
        decayed = self.strength - (self.decay_rate * age_hours)
        return max(0.0, decayed)
