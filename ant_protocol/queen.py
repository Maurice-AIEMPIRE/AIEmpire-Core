"""
Ant Queen - Colony Controller (Skybot / Agent 0)
==================================================
The Queen:
  1. Creates and distributes tasks
  2. Monitors colony health
  3. Manages pheromone trails
  4. Runs automated cron jobs (from OpenClaw jobs.json)
  5. Auto-scales workers
  6. Cleans up dead workers and expired tasks
  7. Provides API for remote control (Skybot)
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional

from .colony import Colony
from .config import (
    COLONY_ID,
    QUEEN_MODEL,
    LITELLM_BASE_URL,
)
from .protocol import (
    AntTask,
    PheromoneTrail,
    TaskPriority,
    TaskStatus,
)

log = logging.getLogger("ant.queen")

# Path to OpenClaw jobs.json
JOBS_FILE = Path(__file__).parent.parent / "openclaw-config" / "jobs.json"


class Queen:
    """Colony controller - creates tasks, monitors health, manages pheromones."""

    def __init__(self, colony_id: str = COLONY_ID):
        self.colony = Colony(colony_id)
        self.colony_id = colony_id
        self._running = False
        self._cron_jobs: list[dict] = []

    async def start(self):
        """Start the Queen's main loops."""
        await self.colony.connect()
        self._load_cron_jobs()
        self._running = True

        log.info(f"Queen started for colony '{self.colony_id}'")
        log.info(f"Loaded {len(self._cron_jobs)} cron jobs from OpenClaw")

        await asyncio.gather(
            self._health_monitor_loop(),
            self._cron_scheduler_loop(),
            self._pheromone_decay_loop(),
            self._cleanup_loop(),
        )

    async def stop(self):
        self._running = False
        await self.colony.close()
        log.info("Queen stopped")

    # ── Task Creation ─────────────────────────────────────────

    async def create_task(
        self,
        title: str,
        description: str = "",
        task_type: str = "general",
        priority: int = TaskPriority.NORMAL,
        skills: list[str] | None = None,
        payload: dict | None = None,
        max_duration: int = 300,
    ) -> str:
        """Create and post a new task to the colony."""
        task = AntTask(
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            required_skills=skills or [],
            payload=payload or {},
            max_duration=max_duration,
        )
        task_id = await self.colony.post_task(task)
        log.info(f"Queen created task: {task_id} '{title}' (P{priority})")
        return task_id

    async def create_batch(self, tasks: list[dict]) -> list[str]:
        """Create multiple tasks at once."""
        ids = []
        for t in tasks:
            tid = await self.create_task(**t)
            ids.append(tid)
        return ids

    # ── Pheromone Control ─────────────────────────────────────

    async def boost_priority(self, task_type: str, strength: float = 5.0):
        """Lay strong pheromone trail to attract workers to a task type."""
        trail = PheromoneTrail(
            trail_id=f"queen:boost:{task_type}",
            task_type=task_type,
            strength=strength,
            direction="attract",
        )
        await self.colony.lay_pheromone(trail)
        log.info(f"Queen boosted pheromone for '{task_type}' (strength={strength})")

    async def suppress_type(self, task_type: str):
        """Weaken pheromone for a task type (workers will avoid it)."""
        trail = PheromoneTrail(
            trail_id=f"queen:suppress:{task_type}",
            task_type=task_type,
            strength=0.1,
            direction="repel",
            decay_rate=0.01,
        )
        await self.colony.lay_pheromone(trail)
        log.info(f"Queen suppressed pheromone for '{task_type}'")

    # ── Colony Status ─────────────────────────────────────────

    async def status(self) -> dict:
        """Get full colony status report."""
        colony_status = await self.colony.status()
        return {
            "queen": {
                "colony_id": self.colony_id,
                "cron_jobs": len(self._cron_jobs),
                "running": self._running,
            },
            "colony": colony_status,
        }

    async def get_log(self, limit: int = 50) -> list[dict]:
        return await self.colony.get_log(limit)

    # ── Cron Job Scheduler ────────────────────────────────────

    def _load_cron_jobs(self):
        """Load cron jobs from OpenClaw jobs.json."""
        if not JOBS_FILE.exists():
            log.warning(f"No jobs file at {JOBS_FILE}")
            return
        try:
            data = json.loads(JOBS_FILE.read_text())
            self._cron_jobs = [j for j in data.get("jobs", []) if j.get("enabled")]
            log.info(f"Loaded {len(self._cron_jobs)} enabled cron jobs")
        except Exception as e:
            log.error(f"Failed to load cron jobs: {e}")

    async def _cron_scheduler_loop(self):
        """Check and dispatch cron jobs every 60 seconds."""
        while self._running:
            try:
                now = time.time()
                for job in self._cron_jobs:
                    state = job.get("state", {})
                    next_run = state.get("nextRunAtMs", 0) / 1000
                    if next_run and now >= next_run:
                        await self._dispatch_cron_job(job)
            except Exception as e:
                log.error(f"Cron scheduler error: {e}")
            await asyncio.sleep(60)

    async def _dispatch_cron_job(self, job: dict):
        """Convert a cron job to an Ant Protocol task."""
        payload = job.get("payload", {})
        message = payload.get("message", job.get("description", ""))
        agent_id = job.get("agentId", "general")

        # Map agent types to task types
        type_map = {
            "research": "research",
            "content": "content",
            "product": "revenue",
            "finance": "revenue",
            "community": "content",
            "ops": "general",
            "analytics": "research",
        }

        await self.create_task(
            title=job.get("name", "Cron Job"),
            description=message,
            task_type=type_map.get(agent_id, "general"),
            priority=TaskPriority.NORMAL,
            skills=[agent_id],
            payload={
                "source": "cron",
                "job_id": job.get("id"),
                "agent_id": agent_id,
            },
        )
        log.info(f"Cron job dispatched: {job.get('name')}")

    # ── Health Monitor ────────────────────────────────────────

    async def _health_monitor_loop(self):
        """Monitor colony health every 30 seconds."""
        while self._running:
            try:
                status = await self.colony.status()
                workers = status["workers"]

                # Alert if no workers alive
                if workers["alive"] == 0 and workers["total"] > 0:
                    log.warning("COLONY ALERT: No alive workers!")

                # Alert if all workers busy (might need scaling)
                if workers["alive"] > 0 and workers["idle"] == 0:
                    log.warning("COLONY ALERT: All workers busy, consider scaling")

                # Alert if too many dead workers
                if workers["dead"] > workers["alive"]:
                    log.warning(f"COLONY ALERT: {workers['dead']} dead workers > {workers['alive']} alive")

            except Exception as e:
                log.error(f"Health monitor error: {e}")
            await asyncio.sleep(30)

    # ── Pheromone Decay ───────────────────────────────────────

    async def _pheromone_decay_loop(self):
        """Periodically clean up expired pheromone trails."""
        while self._running:
            try:
                trails = await self.colony.get_pheromones()
                for trail in trails:
                    if trail.current_strength <= 0.1:
                        # Trail has decayed, Redis TTL will handle cleanup
                        pass
            except Exception as e:
                log.error(f"Pheromone decay error: {e}")
            await asyncio.sleep(300)

    # ── Cleanup ───────────────────────────────────────────────

    async def _cleanup_loop(self):
        """Periodic cleanup of dead workers and expired tasks."""
        while self._running:
            try:
                removed = await self.colony.remove_dead_workers()
                if removed:
                    log.info(f"Cleaned up {removed} dead workers")
            except Exception as e:
                log.error(f"Cleanup error: {e}")
            await asyncio.sleep(60)


async def run_queen():
    """Start the Queen."""
    queen = Queen()
    try:
        await queen.start()
    except KeyboardInterrupt:
        await queen.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    asyncio.run(run_queen())
