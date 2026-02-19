"""
Ant Colony - Shared State Management
======================================
Manages the colony via Redis:
  - Task Board (sorted set by priority)
  - Worker Registry (hash)
  - Pheromone Trails (sorted set with decay)
  - Colony Stats + Logs
"""

import asyncio
import json
import logging
import time
from typing import Optional

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from .config import (
    COLONY_ID,
    COLONY_LOG_KEY,
    COLONY_STATS_KEY,
    HEARTBEAT_TIMEOUT,
    MAX_WORKERS,
    PHEROMONE_DECAY_SEC,
    PHEROMONE_KEY,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    RESULT_KEY,
    TASK_BOARD_KEY,
    TASK_CLAIM_TTL,
    TASK_DATA_KEY,
    WORKER_HEARTBEAT_KEY,
    WORKER_REGISTRY_KEY,
)
from .protocol import (
    AntTask,
    ColonyMessage,
    MessageType,
    PheromoneTrail,
    TaskPriority,
    TaskStatus,
    WorkerInfo,
    WorkerStatus,
)

log = logging.getLogger("ant.colony")


class Colony:
    """Central colony state manager backed by Redis."""

    def __init__(self, colony_id: str = COLONY_ID):
        self.colony_id = colony_id
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub = None

    async def connect(self):
        if aioredis is None:
            raise ImportError("redis[asyncio] required: pip install redis")
        self._redis = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD or None,
            decode_responses=True,
        )
        await self._redis.ping()
        log.info(f"Colony '{self.colony_id}' connected to Redis {REDIS_HOST}:{REDIS_PORT}")

    async def close(self):
        if self._redis:
            await self._redis.close()

    # ── Task Board ────────────────────────────────────────────

    async def post_task(self, task: AntTask) -> str:
        """Post a task to the colony task board."""
        # Store task data
        await self._redis.set(f"{TASK_DATA_KEY}:{task.task_id}", task.to_json())
        # Add to sorted set (score = priority * pheromone)
        score = task.priority * task.pheromone_strength
        await self._redis.zadd(TASK_BOARD_KEY, {task.task_id: score})
        # Publish notification
        await self._publish(MessageType.TASK_CREATED, {
            "task_id": task.task_id,
            "title": task.title,
            "priority": task.priority,
            "task_type": task.task_type,
        })
        await self._log(f"Task posted: {task.task_id} '{task.title}' (P{task.priority})")
        return task.task_id

    async def get_available_tasks(self, limit: int = 10) -> list[AntTask]:
        """Get highest-priority unclaimed tasks."""
        task_ids = await self._redis.zrevrange(TASK_BOARD_KEY, 0, limit * 2)
        tasks = []
        for tid in task_ids:
            raw = await self._redis.get(f"{TASK_DATA_KEY}:{tid}")
            if raw:
                task = AntTask.from_json(raw)
                if task.status == TaskStatus.PENDING and not task.is_expired:
                    tasks.append(task)
                    if len(tasks) >= limit:
                        break
        return tasks

    async def claim_task(self, task_id: str, worker_id: str) -> Optional[AntTask]:
        """Atomically claim a task for a worker. Returns task if claimed, None if already taken."""
        key = f"{TASK_DATA_KEY}:{task_id}"
        raw = await self._redis.get(key)
        if not raw:
            return None
        task = AntTask.from_json(raw)
        if task.status != TaskStatus.PENDING:
            return None

        # Atomic claim via WATCH/MULTI
        task.status = TaskStatus.CLAIMED
        task.claimed_by = worker_id
        task.claimed_at = time.time()
        await self._redis.set(key, task.to_json())
        # Set TTL for auto-release
        await self._redis.expire(f"{TASK_DATA_KEY}:{task_id}:claim", TASK_CLAIM_TTL)

        await self._publish(MessageType.TASK_CLAIMED, {
            "task_id": task_id,
            "worker_id": worker_id,
        })
        await self._log(f"Task {task_id} claimed by {worker_id}")
        return task

    async def complete_task(self, task_id: str, worker_id: str, result: dict):
        """Mark task as completed with result."""
        key = f"{TASK_DATA_KEY}:{task_id}"
        raw = await self._redis.get(key)
        if not raw:
            return
        task = AntTask.from_json(raw)
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = time.time()
        await self._redis.set(key, task.to_json())
        # Remove from active board
        await self._redis.zrem(TASK_BOARD_KEY, task_id)
        # Store result
        await self._redis.lpush(RESULT_KEY, json.dumps({
            "task_id": task_id,
            "worker_id": worker_id,
            "result": result,
            "completed_at": task.completed_at,
        }))

        # Strengthen pheromone for this task type (positive feedback)
        await self.strengthen_pheromone(task.task_type, 0.5)

        await self._publish(MessageType.TASK_COMPLETED, {
            "task_id": task_id,
            "worker_id": worker_id,
        })
        await self._log(f"Task {task_id} completed by {worker_id}")

    async def fail_task(self, task_id: str, worker_id: str, error: str):
        """Mark task as failed."""
        key = f"{TASK_DATA_KEY}:{task_id}"
        raw = await self._redis.get(key)
        if not raw:
            return
        task = AntTask.from_json(raw)
        task.attempts += 1
        if task.attempts < task.max_attempts:
            # Re-queue
            task.status = TaskStatus.PENDING
            task.claimed_by = ""
            task.claimed_at = 0.0
            task.pheromone_strength *= 0.8  # weaken trail slightly
            await self._redis.set(key, task.to_json())
            await self._log(f"Task {task_id} failed ({task.attempts}/{task.max_attempts}), re-queued")
        else:
            task.status = TaskStatus.FAILED
            task.error = error
            await self._redis.set(key, task.to_json())
            await self._redis.zrem(TASK_BOARD_KEY, task_id)
            await self._log(f"Task {task_id} permanently failed: {error}")

        await self._publish(MessageType.TASK_FAILED, {
            "task_id": task_id,
            "worker_id": worker_id,
            "error": error,
            "attempts": task.attempts,
        })

    # ── Worker Registry ───────────────────────────────────────

    async def register_worker(self, worker: WorkerInfo) -> bool:
        """Register a worker ant in the colony."""
        count = await self._redis.hlen(WORKER_REGISTRY_KEY)
        if count >= MAX_WORKERS:
            log.warning(f"Colony full ({count}/{MAX_WORKERS}), rejecting {worker.worker_id}")
            return False

        await self._redis.hset(WORKER_REGISTRY_KEY, worker.worker_id, worker.to_json())
        await self._redis.hset(WORKER_HEARTBEAT_KEY, worker.worker_id, str(time.time()))
        await self._publish(MessageType.WORKER_REGISTERED, {
            "worker_id": worker.worker_id,
            "skills": worker.skills,
        })
        await self._log(f"Worker registered: {worker.worker_id} ({worker.name})")
        return True

    async def heartbeat(self, worker_id: str, load: float = 0.0):
        """Update worker heartbeat."""
        await self._redis.hset(WORKER_HEARTBEAT_KEY, worker_id, str(time.time()))
        # Update load
        raw = await self._redis.hget(WORKER_REGISTRY_KEY, worker_id)
        if raw:
            w = WorkerInfo.from_json(raw)
            w.last_heartbeat = time.time()
            w.load = load
            await self._redis.hset(WORKER_REGISTRY_KEY, worker_id, w.to_json())

    async def get_workers(self) -> list[WorkerInfo]:
        """Get all registered workers with status."""
        data = await self._redis.hgetall(WORKER_REGISTRY_KEY)
        workers = []
        now = time.time()
        for wid, raw in data.items():
            w = WorkerInfo.from_json(raw)
            # Check heartbeat
            hb = await self._redis.hget(WORKER_HEARTBEAT_KEY, wid)
            if hb and (now - float(hb)) > HEARTBEAT_TIMEOUT:
                w.status = WorkerStatus.DEAD
            workers.append(w)
        return workers

    async def remove_dead_workers(self) -> int:
        """Remove workers that missed heartbeat. Returns count removed."""
        workers = await self.get_workers()
        removed = 0
        for w in workers:
            if w.status == WorkerStatus.DEAD:
                await self._redis.hdel(WORKER_REGISTRY_KEY, w.worker_id)
                await self._redis.hdel(WORKER_HEARTBEAT_KEY, w.worker_id)
                # Release any claimed tasks
                task_ids = await self._redis.zrange(TASK_BOARD_KEY, 0, -1)
                for tid in task_ids:
                    raw = await self._redis.get(f"{TASK_DATA_KEY}:{tid}")
                    if raw:
                        task = AntTask.from_json(raw)
                        if task.claimed_by == w.worker_id and task.status == TaskStatus.CLAIMED:
                            task.status = TaskStatus.PENDING
                            task.claimed_by = ""
                            task.claimed_at = 0.0
                            await self._redis.set(f"{TASK_DATA_KEY}:{tid}", task.to_json())
                removed += 1
                await self._log(f"Dead worker removed: {w.worker_id}")
        return removed

    # ── Pheromone System ──────────────────────────────────────

    async def lay_pheromone(self, trail: PheromoneTrail):
        """Lay a pheromone trail to guide workers."""
        await self._redis.zadd(PHEROMONE_KEY, {trail.trail_id: trail.strength})
        await self._redis.set(
            f"{PHEROMONE_KEY}:{trail.trail_id}",
            trail.to_json(),
            ex=PHEROMONE_DECAY_SEC,
        )

    async def strengthen_pheromone(self, task_type: str, amount: float):
        """Strengthen pheromone for a task type (positive reinforcement)."""
        trail_id = f"type:{task_type}"
        existing = await self._redis.get(f"{PHEROMONE_KEY}:{trail_id}")
        if existing:
            trail = PheromoneTrail.from_json(existing)
            trail.strength = min(trail.strength + amount, 10.0)
        else:
            trail = PheromoneTrail(
                trail_id=trail_id,
                task_type=task_type,
                strength=1.0 + amount,
                direction="attract",
            )
        await self.lay_pheromone(trail)

    async def get_pheromones(self) -> list[PheromoneTrail]:
        """Get active pheromone trails sorted by strength."""
        trail_ids = await self._redis.zrevrange(PHEROMONE_KEY, 0, -1, withscores=True)
        trails = []
        for tid, score in trail_ids:
            raw = await self._redis.get(f"{PHEROMONE_KEY}:{tid}")
            if raw:
                trail = PheromoneTrail.from_json(raw)
                if trail.current_strength > 0.1:
                    trails.append(trail)
        return trails

    # ── Colony Status ─────────────────────────────────────────

    async def status(self) -> dict:
        """Get full colony status."""
        workers = await self.get_workers()
        tasks = await self.get_available_tasks(100)
        pheromones = await self.get_pheromones()
        total_results = await self._redis.llen(RESULT_KEY)

        alive = [w for w in workers if w.status != WorkerStatus.DEAD]
        busy = [w for w in alive if w.status == WorkerStatus.BUSY]

        return {
            "colony_id": self.colony_id,
            "workers": {
                "total": len(workers),
                "alive": len(alive),
                "busy": len(busy),
                "idle": len(alive) - len(busy),
                "dead": len(workers) - len(alive),
            },
            "tasks": {
                "pending": len(tasks),
                "total_completed": total_results,
            },
            "pheromones": len(pheromones),
            "timestamp": time.time(),
        }

    # ── Internal ──────────────────────────────────────────────

    async def _publish(self, msg_type: MessageType, payload: dict):
        """Publish message to colony channel."""
        msg = ColonyMessage(
            msg_type=msg_type,
            sender="colony",
            payload=payload,
            colony_id=self.colony_id,
        )
        channel = f"ant:{self.colony_id}:events"
        await self._redis.publish(channel, msg.to_json())

    async def _log(self, message: str):
        """Append to colony log."""
        entry = json.dumps({"ts": time.time(), "msg": message})
        await self._redis.lpush(COLONY_LOG_KEY, entry)
        await self._redis.ltrim(COLONY_LOG_KEY, 0, 999)
        log.info(f"[{self.colony_id}] {message}")

    async def get_log(self, limit: int = 50) -> list[dict]:
        """Get recent colony log entries."""
        entries = await self._redis.lrange(COLONY_LOG_KEY, 0, limit - 1)
        return [json.loads(e) for e in entries]
