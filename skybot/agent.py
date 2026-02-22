"""
Skybot Agent - OpenClaw Agent 0
================================
Master controller that:
  1. Manages the Ant Protocol colony (Queen)
  2. Dispatches tasks from multiple sources (Telegram, API, cron)
  3. Monitors system health (CPU, RAM, disk, services)
  4. Auto-syncs data to iCloud/remote backup
  5. Provides unified command interface
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

log = logging.getLogger("skybot")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
ANT_API_URL = os.getenv("ANT_API_URL", "http://localhost:8900")
SKYBOT_DATA_DIR = PROJECT_ROOT / "skybot" / "data"
SKYBOT_DATA_DIR.mkdir(parents=True, exist_ok=True)


class Skybot:
    """OpenClaw Agent 0 - Master Controller for AI Empire."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self.start_time = time.time()
        self.commands_executed = 0

    async def connect(self):
        if aiohttp is None:
            raise ImportError("aiohttp required: pip install aiohttp")
        self._session = aiohttp.ClientSession()
        log.info("Skybot Agent 0 connected")

    async def close(self):
        if self._session:
            await self._session.close()

    # ── Colony Control ────────────────────────────────────

    async def colony_status(self) -> dict:
        """Get Ant Protocol colony status."""
        return await self._api_get("/status")

    async def create_task(self, title: str, description: str = "",
                          task_type: str = "general", priority: int = 5,
                          skills: list | None = None, payload: dict | None = None) -> dict:
        """Create a task in the Ant Protocol colony."""
        return await self._api_post("/task", {
            "title": title,
            "description": description,
            "task_type": task_type,
            "priority": priority,
            "skills": skills or [],
            "payload": payload or {},
        })

    async def create_batch(self, tasks: list[dict]) -> dict:
        """Create multiple tasks at once."""
        return await self._api_post("/batch", {"tasks": tasks})

    async def list_workers(self) -> dict:
        return await self._api_get("/workers")

    async def list_tasks(self, limit: int = 20) -> dict:
        return await self._api_get(f"/tasks?limit={limit}")

    async def boost_priority(self, task_type: str, strength: float = 5.0) -> dict:
        return await self._api_post("/pheromone/boost", {
            "task_type": task_type, "strength": strength
        })

    # ── System Health ─────────────────────────────────────

    def system_health(self) -> dict:
        """Check system health (CPU, RAM, disk, services)."""
        health = {
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self.start_time,
            "commands_executed": self.commands_executed,
        }

        # CPU + RAM
        try:
            import psutil
            health["cpu_percent"] = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            health["ram_total_gb"] = round(mem.total / (1024**3), 1)
            health["ram_used_gb"] = round(mem.used / (1024**3), 1)
            health["ram_percent"] = mem.percent
            disk = psutil.disk_usage("/")
            health["disk_total_gb"] = round(disk.total / (1024**3), 1)
            health["disk_used_gb"] = round(disk.used / (1024**3), 1)
            health["disk_percent"] = disk.percent
        except ImportError:
            health["note"] = "psutil not installed, install with: pip install psutil"

        # Docker services
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}: {{.Status}}"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                health["docker_services"] = result.stdout.strip().split("\n")
        except Exception:
            health["docker_services"] = []

        return health

    # ── Service Management ────────────────────────────────

    def service_status(self) -> dict:
        """Check status of all AI Empire services."""
        services = {}
        checks = {
            "redis": ("localhost", 6379),
            "litellm": ("localhost", 4000),
            "ollama": ("localhost", 11434),
            "chromadb": ("localhost", 8000),
            "ant_protocol": ("localhost", 8900),
            "crm": ("localhost", 3500),
        }
        import socket
        for name, (host, port) in checks.items():
            try:
                with socket.create_connection((host, port), timeout=2):
                    services[name] = "up"
            except (ConnectionRefusedError, socket.timeout, OSError):
                services[name] = "down"
        return services

    # ── Empire Dashboard ──────────────────────────────────

    async def dashboard(self) -> dict:
        """Full empire status dashboard."""
        colony = {}
        try:
            colony = await self.colony_status()
        except Exception as e:
            colony = {"error": str(e)}

        return {
            "skybot": {
                "version": "1.0.0",
                "agent": "Agent 0 (Skybot)",
                "uptime_sec": round(time.time() - self.start_time),
                "commands": self.commands_executed,
            },
            "system": self.system_health(),
            "services": self.service_status(),
            "colony": colony,
        }

    # ── Command Dispatcher ────────────────────────────────

    async def execute(self, command: str) -> dict:
        """Execute a Skybot command (natural language or structured)."""
        self.commands_executed += 1
        cmd = command.strip().lower()

        # Status commands
        if cmd in ("status", "dashboard", "health"):
            return await self.dashboard()
        if cmd in ("workers", "ants"):
            return await self.list_workers()
        if cmd in ("tasks", "queue"):
            return await self.list_tasks()
        if cmd in ("services", "ports"):
            return {"services": self.service_status()}
        if cmd in ("system", "hw", "hardware"):
            return {"system": self.system_health()}
        if cmd.startswith("colony"):
            return await self.colony_status()

        # Task creation
        if cmd.startswith("task:"):
            parts = cmd[5:].strip()
            return await self.create_task(title=parts, task_type="general")

        # Boost
        if cmd.startswith("boost:"):
            task_type = cmd[6:].strip()
            return await self.boost_priority(task_type)

        # Unknown → pass as task to colony
        return await self.create_task(
            title=f"Skybot command: {command[:100]}",
            description=command,
            task_type="general",
            priority=5,
        )

    # ── Internal ──────────────────────────────────────────

    async def _api_get(self, path: str) -> dict:
        async with self._session.get(f"{ANT_API_URL}{path}", timeout=aiohttp.ClientTimeout(total=10)) as resp:
            return await resp.json()

    async def _api_post(self, path: str, data: dict) -> dict:
        async with self._session.post(f"{ANT_API_URL}{path}", json=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            return await resp.json()


async def run_skybot():
    """Interactive Skybot loop."""
    bot = Skybot()
    await bot.connect()

    print("\n=== SKYBOT Agent 0 - AI Empire Master Controller ===")
    print("Commands: status, workers, tasks, services, system, colony")
    print("          task:<title>, boost:<type>, or any text as task")
    print("          quit to exit\n")

    try:
        while True:
            cmd = input("skybot> ").strip()
            if cmd.lower() in ("quit", "exit", "q"):
                break
            if not cmd:
                continue
            try:
                result = await bot.execute(cmd)
                print(json.dumps(result, indent=2, default=str))
            except Exception as e:
                print(f"Error: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_skybot())
