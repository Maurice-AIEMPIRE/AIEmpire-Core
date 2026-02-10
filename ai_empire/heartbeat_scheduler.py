"""
Heartbeat Scheduler - Scheduled Health Checks & Cron.

Provides periodic health monitoring for all empire subsystems,
plus a lightweight cron-like scheduler for recurring tasks.

Usage:
    scheduler = HeartbeatScheduler()
    scheduler.add_heartbeat("ollama", check_ollama_health, interval=60)
    scheduler.add_cron("content-gen", generate_content, interval=3600)
    await scheduler.start()
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HeartbeatEntry:
    """A registered heartbeat check."""
    name: str
    check_fn: Callable[[], Awaitable[Dict]]
    interval_sec: int
    last_check: float = 0.0
    last_result: Optional[Dict] = None
    consecutive_failures: int = 0
    enabled: bool = True


@dataclass
class CronEntry:
    """A registered cron-like task."""
    name: str
    task_fn: Callable[[], Awaitable[Any]]
    interval_sec: int
    last_run: float = 0.0
    last_result: Optional[str] = None
    run_count: int = 0
    enabled: bool = True


class HeartbeatScheduler:
    """Manages periodic health checks and scheduled tasks."""

    def __init__(self):
        self.heartbeats: Dict[str, HeartbeatEntry] = {}
        self.crons: Dict[str, CronEntry] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []

    def add_heartbeat(
        self,
        name: str,
        check_fn: Callable[[], Awaitable[Dict]],
        interval: int = 60,
    ) -> None:
        """Register a heartbeat check."""
        self.heartbeats[name] = HeartbeatEntry(
            name=name,
            check_fn=check_fn,
            interval_sec=interval,
        )

    def add_cron(
        self,
        name: str,
        task_fn: Callable[[], Awaitable[Any]],
        interval: int = 3600,
    ) -> None:
        """Register a cron-like recurring task."""
        self.crons[name] = CronEntry(
            name=name,
            task_fn=task_fn,
            interval_sec=interval,
        )

    async def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        logger.info(
            f"HeartbeatScheduler started: {len(self.heartbeats)} heartbeats, "
            f"{len(self.crons)} crons"
        )

        while self._running:
            now = time.time()

            # Run due heartbeats
            for entry in self.heartbeats.values():
                if not entry.enabled:
                    continue
                if now - entry.last_check >= entry.interval_sec:
                    asyncio.create_task(self._run_heartbeat(entry))

            # Run due crons
            for entry in self.crons.values():
                if not entry.enabled:
                    continue
                if now - entry.last_run >= entry.interval_sec:
                    asyncio.create_task(self._run_cron(entry))

            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False

    async def run_once(self) -> Dict:
        """Run all checks and crons once, return results."""
        results = {"heartbeats": {}, "crons": {}}

        for entry in self.heartbeats.values():
            if entry.enabled:
                await self._run_heartbeat(entry)
                results["heartbeats"][entry.name] = entry.last_result

        for entry in self.crons.values():
            if entry.enabled:
                await self._run_cron(entry)
                results["crons"][entry.name] = entry.last_result

        return results

    async def _run_heartbeat(self, entry: HeartbeatEntry) -> None:
        """Execute a single heartbeat check."""
        entry.last_check = time.time()
        try:
            result = await entry.check_fn()
            entry.last_result = result
            entry.consecutive_failures = 0
        except Exception as e:
            entry.consecutive_failures += 1
            entry.last_result = {"status": "error", "error": str(e)}
            logger.warning(
                f"Heartbeat {entry.name} failed "
                f"({entry.consecutive_failures} consecutive): {e}"
            )

    async def _run_cron(self, entry: CronEntry) -> None:
        """Execute a single cron task."""
        entry.last_run = time.time()
        try:
            result = await entry.task_fn()
            entry.run_count += 1
            entry.last_result = str(result)[:200] if result else "ok"
        except Exception as e:
            entry.last_result = f"error: {e}"
            logger.warning(f"Cron {entry.name} failed: {e}")

    def get_status(self) -> Dict:
        """Return current scheduler status."""
        return {
            "running": self._running,
            "heartbeats": {
                name: {
                    "enabled": e.enabled,
                    "interval_sec": e.interval_sec,
                    "last_result": e.last_result,
                    "consecutive_failures": e.consecutive_failures,
                    "last_check": datetime.fromtimestamp(e.last_check).isoformat()
                    if e.last_check > 0 else "never",
                }
                for name, e in self.heartbeats.items()
            },
            "crons": {
                name: {
                    "enabled": e.enabled,
                    "interval_sec": e.interval_sec,
                    "run_count": e.run_count,
                    "last_result": e.last_result,
                    "last_run": datetime.fromtimestamp(e.last_run).isoformat()
                    if e.last_run > 0 else "never",
                }
                for name, e in self.crons.items()
            },
        }

    def enable(self, name: str) -> None:
        """Enable a heartbeat or cron by name."""
        if name in self.heartbeats:
            self.heartbeats[name].enabled = True
        if name in self.crons:
            self.crons[name].enabled = True

    def disable(self, name: str) -> None:
        """Disable a heartbeat or cron by name."""
        if name in self.heartbeats:
            self.heartbeats[name].enabled = False
        if name in self.crons:
            self.crons[name].enabled = False
