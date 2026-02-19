"""
Skybot Web API - Remote Control for Agent 0
=============================================
FastAPI endpoints to control the entire AI Empire via HTTP.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError:
    FastAPI = None

from .agent import Skybot

log = logging.getLogger("skybot.api")

_bot: Optional[Skybot] = None


@asynccontextmanager
async def lifespan(app):
    global _bot
    _bot = Skybot()
    await _bot.connect()
    log.info("Skybot Agent 0 API started")
    yield
    if _bot:
        await _bot.close()


def create_app() -> "FastAPI":
    if FastAPI is None:
        raise ImportError("fastapi required: pip install fastapi uvicorn")

    app = FastAPI(
        title="Skybot - AI Empire Master Controller",
        description="OpenClaw Agent 0 - Remote command interface",
        version="1.0.0",
        lifespan=lifespan,
    )

    class CommandRequest(BaseModel):
        command: str

    class TaskRequest(BaseModel):
        title: str
        description: str = ""
        task_type: str = "general"
        priority: int = 5

    @app.get("/")
    async def root():
        return {
            "service": "Skybot Agent 0",
            "version": "1.0.0",
            "uptime_sec": round(time.time() - _bot.start_time) if _bot else 0,
        }

    @app.get("/dashboard")
    async def dashboard():
        if not _bot:
            raise HTTPException(503, "Skybot not initialized")
        return await _bot.dashboard()

    @app.get("/health")
    async def health():
        if not _bot:
            return {"healthy": False, "reason": "not initialized"}
        return {"healthy": True, "system": _bot.system_health()}

    @app.get("/services")
    async def services():
        if not _bot:
            raise HTTPException(503, "Skybot not initialized")
        return {"services": _bot.service_status()}

    @app.get("/system")
    async def system():
        if not _bot:
            raise HTTPException(503, "Skybot not initialized")
        return {"system": _bot.system_health()}

    @app.post("/execute")
    async def execute(req: CommandRequest):
        if not _bot:
            raise HTTPException(503, "Skybot not initialized")
        return await _bot.execute(req.command)

    @app.post("/task")
    async def create_task(req: TaskRequest):
        if not _bot:
            raise HTTPException(503, "Skybot not initialized")
        return await _bot.create_task(
            title=req.title,
            description=req.description,
            task_type=req.task_type,
            priority=req.priority,
        )

    @app.get("/colony")
    async def colony():
        if not _bot:
            raise HTTPException(503, "Skybot not initialized")
        return await _bot.colony_status()

    @app.get("/workers")
    async def workers():
        if not _bot:
            raise HTTPException(503, "Skybot not initialized")
        return await _bot.list_workers()

    @app.get("/tasks")
    async def tasks(limit: int = 20):
        if not _bot:
            raise HTTPException(503, "Skybot not initialized")
        return await _bot.list_tasks(limit)

    return app


def run_api():
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8901)


if __name__ == "__main__":
    run_api()
