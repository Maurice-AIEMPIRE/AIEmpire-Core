#!/usr/bin/env python3
"""
AGENT REGISTRY - Zentrale Agent-Verwaltung fuer 100+ Agents.
Source of Truth: Welche Agents gibt es, was koennen sie, wie performen sie.

Features:
- Agent Registration + Discovery
- Capability Matching (Task → best Agent)
- Health Monitoring (alive/dead/busy)
- Output Schema Validation
- Performance Tracking (revenue, speed, quality)

Usage:
    python agent_registry.py                  # Status / Alle Agents
    python agent_registry.py --register       # Neuen Agent registrieren
    python agent_registry.py --find "content" # Agent fuer Task finden
    python agent_registry.py --health         # Health Check aller Agents
    python agent_registry.py --report         # Performance Report
"""

import asyncio
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

STATE_DIR = Path(__file__).parent / "state"
REGISTRY_FILE = STATE_DIR / "agent_registry.json"

# ── Agent Capabilities ───────────────────────────────────────

CAPABILITIES = {
    "content_generation": "Generiert Content (Posts, Scripts, Threads)",
    "lead_generation": "Findet und bewertet Leads",
    "code_generation": "Schreibt und optimiert Code",
    "data_analysis": "Analysiert Daten und erstellt Reports",
    "product_design": "Designt Produkte und Offers",
    "marketing": "Erstellt Marketing-Material",
    "sales": "Verkauft und nurturet Leads",
    "research": "Recherchiert Trends und Wettbewerber",
    "automation": "Baut und verwaltet Workflows",
    "monitoring": "Ueberwacht Systeme und Metriken",
    "support": "Beantwortet Fragen und hilft Nutzern",
    "translation": "Uebersetzt und lokalisiert Content",
}

# ── Standard Output Schema ───────────────────────────────────

OUTPUT_SCHEMA = {
    "required_fields": ["agent_id", "task_id", "status", "output", "timestamp"],
    "status_values": ["success", "partial", "failed", "pending"],
    "metadata_fields": ["duration_ms", "tokens_used", "model", "cost"],
}


class Agent:
    """Einzelner Agent im Registry."""

    def __init__(self, agent_id: str, name: str, capabilities: List[str],
                 provider: str = "ollama", model: str = "qwen2.5-coder:7b",
                 squad: str = "general", priority: int = 5):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.provider = provider
        self.model = model
        self.squad = squad
        self.priority = priority  # 1-10, 10 = hoechste Prioritaet
        self.status = "idle"  # idle, busy, offline, error
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_revenue": 0.0,
            "avg_duration_ms": 0,
            "last_active": None,
        }
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "provider": self.provider,
            "model": self.model,
            "squad": self.squad,
            "priority": self.priority,
            "status": self.status,
            "stats": self.stats,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        agent = cls(
            agent_id=data["agent_id"],
            name=data["name"],
            capabilities=data.get("capabilities", []),
            provider=data.get("provider", "ollama"),
            model=data.get("model", "qwen2.5-coder:7b"),
            squad=data.get("squad", "general"),
            priority=data.get("priority", 5),
        )
        agent.status = data.get("status", "idle")
        agent.stats = data.get("stats", agent.stats)
        agent.created_at = data.get("created_at", agent.created_at)
        return agent


class AgentRegistry:
    """Zentrale Agent-Verwaltung."""

    def __init__(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.agents: Dict[str, Agent] = {}
        self._load()

    def _load(self):
        if REGISTRY_FILE.exists():
            try:
                data = json.loads(REGISTRY_FILE.read_text())
                for agent_data in data.get("agents", []):
                    agent = Agent.from_dict(agent_data)
                    self.agents[agent.agent_id] = agent
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        data = {
            "agents": [a.to_dict() for a in self.agents.values()],
            "updated": datetime.now().isoformat(),
            "total": len(self.agents),
        }
        REGISTRY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # ── Registration ─────────────────────────────────────────

    def register(self, agent_id: str, name: str, capabilities: List[str],
                 **kwargs) -> Agent:
        """Registriert einen neuen Agent."""
        agent = Agent(agent_id=agent_id, name=name, capabilities=capabilities, **kwargs)
        self.agents[agent_id] = agent
        self.save()
        return agent

    def unregister(self, agent_id: str) -> bool:
        """Entfernt einen Agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.save()
            return True
        return False

    # ── Discovery ────────────────────────────────────────────

    def find_by_capability(self, capability: str) -> List[Agent]:
        """Findet Agents nach Capability."""
        results = []
        for agent in self.agents.values():
            if capability in agent.capabilities and agent.status != "offline":
                results.append(agent)
        # Sortiert nach Priority (hoch zuerst) und Performance
        results.sort(key=lambda a: (a.priority, a.stats["tasks_completed"]), reverse=True)
        return results

    def find_best_for_task(self, task_type: str) -> Optional[Agent]:
        """Findet den besten Agent fuer einen Task-Typ."""
        candidates = self.find_by_capability(task_type)
        idle = [a for a in candidates if a.status == "idle"]
        return idle[0] if idle else (candidates[0] if candidates else None)

    def find_by_squad(self, squad: str) -> List[Agent]:
        """Findet alle Agents eines Squads."""
        return [a for a in self.agents.values() if a.squad == squad]

    # ── Status Management ────────────────────────────────────

    def set_status(self, agent_id: str, status: str):
        """Setzt Agent-Status."""
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            self.save()

    def report_task(self, agent_id: str, success: bool, duration_ms: float = 0, revenue: float = 0):
        """Meldet Task-Ergebnis."""
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]
        if success:
            agent.stats["tasks_completed"] += 1
        else:
            agent.stats["tasks_failed"] += 1

        agent.stats["total_revenue"] += revenue
        agent.stats["last_active"] = datetime.now().isoformat()

        # Running Average
        total_tasks = agent.stats["tasks_completed"] + agent.stats["tasks_failed"]
        if total_tasks > 0:
            prev_avg = agent.stats["avg_duration_ms"]
            agent.stats["avg_duration_ms"] = (
                (prev_avg * (total_tasks - 1) + duration_ms) / total_tasks
            )

        self.save()

    def health_check(self) -> dict:
        """Prueft Gesundheit aller Agents."""
        total = len(self.agents)
        idle = sum(1 for a in self.agents.values() if a.status == "idle")
        busy = sum(1 for a in self.agents.values() if a.status == "busy")
        offline = sum(1 for a in self.agents.values() if a.status == "offline")
        error = sum(1 for a in self.agents.values() if a.status == "error")

        return {
            "total": total,
            "idle": idle,
            "busy": busy,
            "offline": offline,
            "error": error,
            "health_pct": round((idle + busy) / max(total, 1) * 100, 1),
        }

    # ── Seed Default Agents ──────────────────────────────────

    def seed_defaults(self):
        """Registriert die Standard-Agents des Empire."""
        if self.agents:
            return  # Bereits initialisiert

        defaults = [
            ("content-x", "X Content Agent", ["content_generation", "marketing"], "content", 8),
            ("content-tiktok", "TikTok Script Agent", ["content_generation"], "content", 7),
            ("content-thread", "Thread Writer", ["content_generation", "marketing"], "content", 7),
            ("lead-finder", "Lead Discovery Agent", ["lead_generation", "research"], "sales", 9),
            ("lead-scorer", "Lead Scoring Agent", ["lead_generation", "data_analysis"], "sales", 8),
            ("dm-nurture", "DM Nurture Agent", ["sales", "content_generation"], "sales", 8),
            ("reply-engine", "Viral Reply Engine", ["content_generation", "lead_generation"], "engagement", 7),
            ("product-designer", "Product Design Agent", ["product_design", "marketing"], "product", 9),
            ("product-builder", "Asset Builder Agent", ["product_design", "code_generation"], "product", 8),
            ("market-gen", "Marketing Content Agent", ["marketing", "content_generation"], "marketing", 8),
            ("email-writer", "Email Sequence Agent", ["marketing", "sales"], "marketing", 7),
            ("trend-scanner", "Trend Research Agent", ["research", "data_analysis"], "intelligence", 6),
            ("competitor-watch", "Competitor Monitor", ["research", "monitoring"], "intelligence", 6),
            ("bma-expert", "BMA Expertise Agent", ["product_design", "support"], "niche", 10),
            ("code-builder", "Code Generation Agent", ["code_generation", "automation"], "engineering", 7),
            ("workflow-bot", "n8n Workflow Agent", ["automation", "code_generation"], "engineering", 7),
            ("quality-gate", "QA & Review Agent", ["monitoring", "data_analysis"], "engineering", 6),
            ("crm-agent", "CRM Management Agent", ["data_analysis", "sales"], "sales", 7),
            ("ollama-router", "Model Router Agent", ["automation", "monitoring"], "infrastructure", 8),
            ("brain-thinker", "Empire Brain Think Agent", ["data_analysis", "research"], "command", 10),
        ]

        for agent_id, name, caps, squad, priority in defaults:
            self.register(
                agent_id=agent_id,
                name=name,
                capabilities=caps,
                squad=squad,
                priority=priority,
            )

        print(f"    {len(defaults)} Standard-Agents registriert!")

    # ── Reports ──────────────────────────────────────────────

    def show_status(self):
        """Zeigt Registry Status."""
        health = self.health_check()

        # Squads zaehlen
        squads = {}
        for a in self.agents.values():
            squads[a.squad] = squads.get(a.squad, 0) + 1

        print(f"""
{'='*60}
  AGENT REGISTRY - {len(self.agents)} Agents
{'='*60}

  HEALTH: {health['health_pct']}%
    Idle:     {health['idle']}
    Busy:     {health['busy']}
    Offline:  {health['offline']}
    Error:    {health['error']}

  SQUADS:""")
        for squad, count in sorted(squads.items(), key=lambda x: x[1], reverse=True):
            print(f"    {squad:<15s}: {count} agents")

        print(f"""
  CAPABILITIES:""")
        cap_count = {}
        for a in self.agents.values():
            for cap in a.capabilities:
                cap_count[cap] = cap_count.get(cap, 0) + 1
        for cap, count in sorted(cap_count.items(), key=lambda x: x[1], reverse=True):
            desc = CAPABILITIES.get(cap, "")
            print(f"    {cap:<25s}: {count} agents  ({desc[:40]})")

        if self.agents:
            print(f"\n  TOP PERFORMERS:")
            top = sorted(
                self.agents.values(),
                key=lambda a: a.stats["tasks_completed"],
                reverse=True,
            )[:5]
            for i, a in enumerate(top, 1):
                print(f"    {i}. [{a.squad}] {a.name} - "
                      f"{a.stats['tasks_completed']} tasks, "
                      f"EUR {a.stats['total_revenue']:.2f}")

        print(f"""
  COMMANDS:
    python agent_registry.py --seed         # Standard-Agents laden
    python agent_registry.py --find content # Agent suchen
    python agent_registry.py --health       # Health Check
    python agent_registry.py --report       # Performance Report
{'='*60}""")

    def performance_report(self):
        """Detaillierter Performance Report."""
        print(f"\n{'='*60}")
        print(f"  AGENT PERFORMANCE REPORT")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")

        sorted_agents = sorted(
            self.agents.values(),
            key=lambda a: (a.stats["total_revenue"], a.stats["tasks_completed"]),
            reverse=True,
        )

        print(f"\n  {'ID':<18s} {'Squad':<13s} {'Tasks':>6s} {'Failed':>7s} {'Revenue':>10s} {'Avg ms':>8s} {'Status':<8s}")
        print(f"  {'─'*75}")

        total_revenue = 0
        total_tasks = 0
        for a in sorted_agents:
            total = a.stats["tasks_completed"] + a.stats["tasks_failed"]
            total_tasks += total
            total_revenue += a.stats["total_revenue"]
            print(f"  {a.agent_id:<18s} {a.squad:<13s} "
                  f"{a.stats['tasks_completed']:>6d} "
                  f"{a.stats['tasks_failed']:>7d} "
                  f"{a.stats['total_revenue']:>9.2f}€ "
                  f"{a.stats['avg_duration_ms']:>7.0f} "
                  f"{a.status:<8s}")

        print(f"  {'─'*75}")
        print(f"  {'TOTAL':<18s} {'':<13s} {total_tasks:>6d} {'':>7s} {total_revenue:>9.2f}€")
        print(f"{'='*60}")


async def main():
    parser = argparse.ArgumentParser(description="Agent Registry")
    parser.add_argument("--seed", action="store_true", help="Standard-Agents laden")
    parser.add_argument("--find", type=str, metavar="CAP", help="Agent nach Capability suchen")
    parser.add_argument("--health", action="store_true", help="Health Check")
    parser.add_argument("--report", action="store_true", help="Performance Report")
    args = parser.parse_args()

    registry = AgentRegistry()

    if args.seed:
        registry.seed_defaults()
        registry.show_status()
    elif args.find:
        results = registry.find_by_capability(args.find)
        if results:
            print(f"\n  Agents fuer '{args.find}':")
            for a in results:
                print(f"    [{a.priority}] {a.agent_id}: {a.name} ({a.squad}) - {a.status}")
        else:
            print(f"    Keine Agents fuer '{args.find}' gefunden")
    elif args.health:
        health = registry.health_check()
        print(f"\n  Health: {health['health_pct']}% ({health['idle']} idle, {health['busy']} busy)")
    elif args.report:
        registry.performance_report()
    else:
        registry.show_status()


if __name__ == "__main__":
    asyncio.run(main())
