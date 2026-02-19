"""
Ant Protocol API - Remote Colony Control
==========================================
FastAPI endpoints for Skybot and external control.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError:
    FastAPI = None

from .colony import Colony
from .config import ANT_API_HOST, ANT_API_PORT, COLONY_ID
from .protocol import AntTask, TaskPriority
from .queen import Queen

log = logging.getLogger("ant.api")

# Global instances
_queen: Optional[Queen] = None
_queen_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app):
    """Start Queen on API startup."""
    global _queen, _queen_task
    _queen = Queen()
    _queen_task = asyncio.create_task(_queen.start())
    log.info("Queen started via API lifespan")
    yield
    if _queen:
        await _queen.stop()
    if _queen_task:
        _queen_task.cancel()


def create_app() -> "FastAPI":
    if FastAPI is None:
        raise ImportError("fastapi required: pip install fastapi uvicorn")

    app = FastAPI(
        title="Ant Protocol - Colony API",
        description="Remote control for the AI Empire Ant Colony",
        version="1.0.0",
        lifespan=lifespan,
    )

    # ── Models ────────────────────────────────────────────

    class TaskCreate(BaseModel):
        title: str
        description: str = ""
        task_type: str = "general"
        priority: int = TaskPriority.NORMAL
        skills: list[str] = []
        payload: dict = {}
        max_duration: int = 300

    class BatchCreate(BaseModel):
        tasks: list[TaskCreate]

    class PheromoneBoost(BaseModel):
        task_type: str
        strength: float = 5.0

    # ── Endpoints ─────────────────────────────────────────

    @app.get("/")
    async def root():
        return {"service": "Ant Protocol", "colony": COLONY_ID, "status": "running"}

    @app.get("/status")
    async def colony_status():
        if not _queen:
            raise HTTPException(503, "Queen not initialized")
        return await _queen.status()

    @app.get("/log")
    async def colony_log(limit: int = 50):
        if not _queen:
            raise HTTPException(503, "Queen not initialized")
        return await _queen.get_log(limit)

    @app.post("/task")
    async def create_task(task: TaskCreate):
        if not _queen:
            raise HTTPException(503, "Queen not initialized")
        task_id = await _queen.create_task(
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            priority=task.priority,
            skills=task.skills,
            payload=task.payload,
            max_duration=task.max_duration,
        )
        return {"task_id": task_id, "status": "posted"}

    @app.post("/batch")
    async def create_batch(batch: BatchCreate):
        if not _queen:
            raise HTTPException(503, "Queen not initialized")
        ids = await _queen.create_batch([t.model_dump() for t in batch.tasks])
        return {"task_ids": ids, "count": len(ids)}

    @app.post("/pheromone/boost")
    async def boost_pheromone(boost: PheromoneBoost):
        if not _queen:
            raise HTTPException(503, "Queen not initialized")
        await _queen.boost_priority(boost.task_type, boost.strength)
        return {"status": "boosted", "task_type": boost.task_type}

    @app.post("/pheromone/suppress")
    async def suppress_pheromone(boost: PheromoneBoost):
        if not _queen:
            raise HTTPException(503, "Queen not initialized")
        await _queen.suppress_type(boost.task_type)
        return {"status": "suppressed", "task_type": boost.task_type}

    @app.get("/workers")
    async def list_workers():
        if not _queen:
            raise HTTPException(503, "Queen not initialized")
        workers = await _queen.colony.get_workers()
        return {"workers": [w.__dict__ for w in workers]}

    @app.get("/tasks")
    async def list_tasks(limit: int = 20):
        if not _queen:
            raise HTTPException(503, "Queen not initialized")
        tasks = await _queen.colony.get_available_tasks(limit)
        return {"tasks": [t.__dict__ for t in tasks]}

    @app.get("/health")
    async def health():
        try:
            if _queen:
                status = await _queen.status()
                return {"healthy": True, "colony": status}
            return {"healthy": False, "reason": "queen not started"}
        except Exception as e:
            return {"healthy": False, "reason": str(e)}

    return app


def run_api():
    """Run the API server."""
    import uvicorn

    app = create_app()
    uvicorn.run(app, host=ANT_API_HOST, port=ANT_API_PORT)


if __name__ == "__main__":
    run_api()
