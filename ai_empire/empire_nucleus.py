#!/usr/bin/env python3
"""
Empire Nucleus - Central Orchestrator.

The brain of the AI Empire. Boots all subsystems, validates their
health, and provides a single entry point for all operations.

Fail-fast design: if any critical component cannot initialize,
a clear RuntimeError is raised at startup - never a NoneType later.

Usage:
    nucleus = EmpireNucleus()
    await nucleus.boot()
    await nucleus.run_health_check()
    print(nucleus.status_report())
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .ollama_engine import OllamaEngine
from .agent_manager import AgentManager
from .memory_core import MemoryCore
from .heartbeat_scheduler import HeartbeatScheduler
from .guarded_tools import GuardedTools
from .skills_library import SkillsLibrary

logger = logging.getLogger(__name__)

EMPIRE_ROOT = Path(__file__).parent.parent


class BootError(RuntimeError):
    """Raised when a critical component fails to initialize."""
    pass


class EmpireNucleus:
    """Central orchestrator for the AI Empire."""

    def __init__(self, empire_root: Optional[Path] = None):
        self.root = empire_root or EMPIRE_ROOT
        self.booted = False
        self.boot_time: Optional[str] = None

        # Initialize all components - fail fast if any constructor raises
        try:
            self.ollama = OllamaEngine()
        except Exception as e:
            raise BootError(f"OllamaEngine init failed: {e}") from e

        try:
            self.agents = AgentManager()
        except Exception as e:
            raise BootError(f"AgentManager init failed: {e}") from e

        try:
            self.memory = MemoryCore()
        except Exception as e:
            raise BootError(f"MemoryCore init failed: {e}") from e

        try:
            self.scheduler = HeartbeatScheduler()
        except Exception as e:
            raise BootError(f"HeartbeatScheduler init failed: {e}") from e

        try:
            self.tools = GuardedTools()
        except Exception as e:
            raise BootError(f"GuardedTools init failed: {e}") from e

        try:
            self.skills = SkillsLibrary()
        except Exception as e:
            raise BootError(f"SkillsLibrary init failed: {e}") from e

        # Validate nothing is None
        self._validate_components()

    def _validate_components(self) -> None:
        """Ensure all components are properly initialized."""
        components = {
            "ollama": self.ollama,
            "agents": self.agents,
            "memory": self.memory,
            "scheduler": self.scheduler,
            "tools": self.tools,
            "skills": self.skills,
        }
        for name, component in components.items():
            if component is None:
                raise BootError(
                    f"Component '{name}' is None after initialization. "
                    f"This indicates a bug in the {name} module constructor."
                )

    async def boot(self) -> Dict:
        """Boot the empire - initialize all subsystems and run health checks."""
        print("""
╔══════════════════════════════════════════════════════════╗
║              EMPIRE NUCLEUS - BOOTING                    ║
╚══════════════════════════════════════════════════════════╝
        """)

        report = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "warnings": [],
            "errors": [],
        }

        # 1. Check Ollama
        print("  [1/6] Checking Ollama engine...")
        ollama_ok = await self.ollama.check_health()
        models = await self.ollama.list_models() if ollama_ok else []
        report["components"]["ollama"] = {
            "status": "online" if ollama_ok else "offline",
            "models": [m.name for m in models],
        }
        if not ollama_ok:
            report["warnings"].append(
                "Ollama is offline. Local model inference unavailable. "
                "Start with: ollama serve"
            )
        print(f"         {'ONLINE' if ollama_ok else 'OFFLINE'} ({len(models)} models)")

        # 2. Agent Manager
        print("  [2/6] Loading agent registry...")
        agent_stats = self.agents.get_stats()
        report["components"]["agents"] = agent_stats
        print(f"         {agent_stats['total_agents']} agents registered")

        # 3. Memory Core
        print("  [3/6] Initializing memory core...")
        memory_stats = self.memory.get_stats()
        report["components"]["memory"] = memory_stats
        print(f"         {memory_stats['namespaces']} namespaces, {memory_stats['total_keys']} keys")

        # 4. Heartbeat Scheduler
        print("  [4/6] Preparing heartbeat scheduler...")
        self._register_default_heartbeats()
        scheduler_status = self.scheduler.get_status()
        report["components"]["scheduler"] = {
            "heartbeats": len(scheduler_status["heartbeats"]),
            "crons": len(scheduler_status["crons"]),
        }
        print(f"         {len(scheduler_status['heartbeats'])} heartbeats, {len(scheduler_status['crons'])} crons")

        # 5. Guarded Tools
        print("  [5/6] Initializing guarded tools...")
        tool_stats = self.tools.get_stats()
        report["components"]["tools"] = tool_stats
        print(f"         Ready (max file: {self.tools.max_file_size_mb}MB, timeout: {self.tools.default_timeout}s)")

        # 6. Skills Library
        print("  [6/6] Scanning skills library...")
        available_skills = self.skills.list_skills()
        report["components"]["skills"] = {
            "available": len(available_skills),
            "names": available_skills,
        }
        print(f"         {len(available_skills)} skills available")

        self.booted = True
        self.boot_time = datetime.now().isoformat()
        report["boot_time"] = self.boot_time
        report["status"] = "booted"

        # Summary
        warnings = len(report["warnings"])
        errors = len(report["errors"])
        print(f"""
╔══════════════════════════════════════════════════════════╗
║              EMPIRE NUCLEUS - ONLINE                     ║
╠══════════════════════════════════════════════════════════╣
  Boot time:   {self.boot_time}
  Components:  6/6 initialized
  Warnings:    {warnings}
  Errors:      {errors}
  Skills:      {len(available_skills)}
  Agents:      {agent_stats['total_agents']}
╚══════════════════════════════════════════════════════════╝
        """)

        # Store boot report in memory
        self.memory.store("system", "last_boot", report)

        return report

    async def run_health_check(self) -> Dict:
        """Run a full health check across all subsystems."""
        checks = {}

        # Ollama
        checks["ollama"] = {
            "healthy": await self.ollama.check_health(),
            "stats": self.ollama.get_stats(),
        }

        # Agent Manager
        checks["agents"] = self.agents.get_stats()

        # Memory
        checks["memory"] = self.memory.get_stats()

        # Tools
        checks["tools"] = self.tools.get_stats()

        # Skills
        checks["skills"] = {
            "available": len(self.skills.list_skills()),
        }

        # Workflow system
        wf_state = self.root / "workflow-system" / "state" / "current_state.json"
        if wf_state.exists():
            try:
                state = json.loads(wf_state.read_text())
                checks["workflow"] = {
                    "cycle": state.get("cycle", 0),
                    "steps_completed": len(state.get("steps_completed", [])),
                }
            except json.JSONDecodeError:
                checks["workflow"] = {"status": "corrupted_state"}
        else:
            checks["workflow"] = {"status": "not_initialized"}

        checks["timestamp"] = datetime.now().isoformat()
        return checks

    def status_report(self) -> str:
        """Generate a human-readable status report."""
        agent_stats = self.agents.get_stats()
        memory_stats = self.memory.get_stats()
        tool_stats = self.tools.get_stats()
        skills = self.skills.list_skills()

        return f"""
╔══════════════════════════════════════════════════════════╗
║              EMPIRE NUCLEUS STATUS                       ║
╠══════════════════════════════════════════════════════════╣
  Booted:       {self.booted}
  Boot time:    {self.boot_time or 'N/A'}
  Agents:       {agent_stats['total_agents']} total, {agent_stats['active_agents']} active
  Memory:       {memory_stats['namespaces']} ns, {memory_stats['total_keys']} keys
  Tools:        {tool_stats['total_calls']} calls ({tool_stats['success_rate']}% success)
  Skills:       {len(skills)} available
  Ollama:       {self.ollama.get_stats().get('available', 'unknown')}
╚══════════════════════════════════════════════════════════╝
"""

    def _register_default_heartbeats(self) -> None:
        """Register default health check heartbeats."""

        async def check_ollama():
            healthy = await self.ollama.check_health()
            return {"status": "online" if healthy else "offline"}

        async def check_disk():
            import os
            st = os.statvfs("/")
            free_gb = (st.f_bavail * st.f_frsize) / (1024 ** 3)
            return {"free_gb": round(free_gb, 1), "status": "ok" if free_gb > 1 else "low"}

        self.scheduler.add_heartbeat("ollama", check_ollama, interval=60)
        self.scheduler.add_heartbeat("disk", check_disk, interval=300)


async def main():
    """CLI entry point for Empire Nucleus."""
    import argparse

    parser = argparse.ArgumentParser(description="Empire Nucleus - Central Orchestrator")
    parser.add_argument("--boot", action="store_true", help="Boot the empire")
    parser.add_argument("--health", action="store_true", help="Run health check")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--skills", action="store_true", help="List available skills")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        nucleus = EmpireNucleus()
    except BootError as e:
        print(f"BOOT FAILED: {e}")
        sys.exit(1)

    if args.boot or not any([args.health, args.status, args.skills]):
        report = await nucleus.boot()
        if report.get("errors"):
            print("ERRORS during boot:")
            for err in report["errors"]:
                print(f"  - {err}")

    if args.health:
        checks = await nucleus.run_health_check()
        print(json.dumps(checks, indent=2))

    if args.status:
        print(nucleus.status_report())

    if args.skills:
        skills = nucleus.skills.list_skills()
        print(f"Available skills ({len(skills)}):")
        for s in skills:
            summary = nucleus.skills.get_skill_summary(s)
            purpose = summary.get("purpose", "")[:60] if summary else ""
            print(f"  {s:25s} {purpose}")


if __name__ == "__main__":
    asyncio.run(main())
