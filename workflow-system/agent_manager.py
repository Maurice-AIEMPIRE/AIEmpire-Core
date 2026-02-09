#!/usr/bin/env python3
"""
AGENT MANAGER - Revenue-basiertes Ranking System.
Dirk Kreuter Prinzip: Wer Geld bringt, bekommt mehr Ressourcen.

Ranking-Logik:
  Platz 1-3:   3.0x / 2.5x / 2.0x Task-Multiplikator (Top Performer)
  Platz 4-7:   1.0x (Standard)
  Platz 8-10:  0.5x (Underperformer, weniger Tasks)
  Unter Top 10: 0.1x (Fast pausiert)

Usage:
    from agent_manager import AgentManager

    manager = AgentManager()
    manager.record_revenue("content_agent_01", 150.0)
    manager.record_revenue("lead_agent_03", 500.0)
    leaderboard = manager.get_leaderboard()
    multiplier = manager.get_task_multiplier("lead_agent_03")
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


STATE_DIR = Path(__file__).parent / "state"
DEFAULT_RANKINGS_FILE = STATE_DIR / "agent_rankings.json"

# Ranking Multiplikatoren - Dirk Kreuter Style
RANK_MULTIPLIERS = {
    1: 3.0,   # Champion - maximale Power
    2: 2.5,   # Vize-Champion
    3: 2.0,   # Bronze - immer noch stark
    4: 1.0,   # Standard
    5: 1.0,
    6: 1.0,
    7: 1.0,
    8: 0.5,   # Underperformer - weniger Tasks
    9: 0.5,
    10: 0.5,
}
DEFAULT_MULTIPLIER = 0.1  # Unter Top 10: fast pausiert


class AgentManager:
    """Revenue-basiertes Agent Ranking und Task Allocation."""

    def __init__(self, rankings_file: Optional[str] = None):
        self.rankings_file = Path(rankings_file) if rankings_file else DEFAULT_RANKINGS_FILE
        self.rankings_file.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    # ── Persistence ─────────────────────────────────────────

    def _load(self) -> dict:
        """Laedt Rankings aus JSON."""
        if self.rankings_file.exists():
            try:
                return json.loads(self.rankings_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"agents": {}, "history": [], "meta": {"created": datetime.now().isoformat()}}

    def save(self):
        """Speichert Rankings als JSON."""
        self.data["meta"]["updated"] = datetime.now().isoformat()
        self.data["meta"]["total_agents"] = len(self.data["agents"])
        self.data["meta"]["total_revenue"] = sum(
            a.get("revenue", 0) for a in self.data["agents"].values()
        )
        self.rankings_file.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    # ── Agent Operations ────────────────────────────────────

    def register_agent(self, agent_id: str, squad: str = "general", role: str = "worker"):
        """Registriert einen neuen Agent."""
        if agent_id not in self.data["agents"]:
            self.data["agents"][agent_id] = {
                "squad": squad,
                "role": role,
                "revenue": 0.0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "registered": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
            }
            self.save()

    def record_revenue(self, agent_id: str, amount: float, source: str = ""):
        """Erfasst Revenue von einem Agent."""
        if agent_id not in self.data["agents"]:
            self.register_agent(agent_id)

        agent = self.data["agents"][agent_id]
        agent["revenue"] = agent.get("revenue", 0) + amount
        agent["last_active"] = datetime.now().isoformat()

        # History Entry
        self.data["history"].append({
            "agent_id": agent_id,
            "amount": amount,
            "source": source,
            "timestamp": datetime.now().isoformat(),
        })

        # History auf letzte 1000 Eintraege begrenzen
        if len(self.data["history"]) > 1000:
            self.data["history"] = self.data["history"][-1000:]

        self.save()

    def record_task(self, agent_id: str, success: bool = True):
        """Erfasst Task-Completion."""
        if agent_id not in self.data["agents"]:
            self.register_agent(agent_id)

        agent = self.data["agents"][agent_id]
        if success:
            agent["tasks_completed"] = agent.get("tasks_completed", 0) + 1
        else:
            agent["tasks_failed"] = agent.get("tasks_failed", 0) + 1
        agent["last_active"] = datetime.now().isoformat()
        self.save()

    # ── Ranking & Leaderboard ───────────────────────────────

    def get_leaderboard(self, limit: int = 10) -> List[dict]:
        """Top N Agents sortiert nach Revenue."""
        ranked = []
        for agent_id, agent_data in self.data["agents"].items():
            ranked.append({
                "agent_id": agent_id,
                "revenue": agent_data.get("revenue", 0),
                "tasks_completed": agent_data.get("tasks_completed", 0),
                "tasks_failed": agent_data.get("tasks_failed", 0),
                "squad": agent_data.get("squad", "general"),
                "role": agent_data.get("role", "worker"),
                "last_active": agent_data.get("last_active", ""),
            })

        ranked.sort(key=lambda x: x["revenue"], reverse=True)

        for i, agent in enumerate(ranked):
            agent["rank"] = i + 1
            agent["multiplier"] = self._multiplier_for_rank(i + 1)

        return ranked[:limit]

    def get_rank(self, agent_id: str) -> int:
        """Gibt den Rang eines Agents zurueck (1-based, 0 = nicht gefunden)."""
        leaderboard = self.get_leaderboard(limit=999)
        for entry in leaderboard:
            if entry["agent_id"] == agent_id:
                return entry["rank"]
        return 0

    def get_task_multiplier(self, agent_id: str) -> float:
        """Task-Multiplikator basierend auf Revenue-Ranking."""
        rank = self.get_rank(agent_id)
        if rank == 0:
            return DEFAULT_MULTIPLIER
        return self._multiplier_for_rank(rank)

    def allocate_tasks(self, agent_id: str, base_count: int) -> int:
        """Berechnet Task-Zuweisung basierend auf Ranking."""
        multiplier = self.get_task_multiplier(agent_id)
        return max(1, int(base_count * multiplier))

    def _multiplier_for_rank(self, rank: int) -> float:
        """Multiplikator fuer einen Rang."""
        return RANK_MULTIPLIERS.get(rank, DEFAULT_MULTIPLIER)

    # ── Squad Management ────────────────────────────────────

    def get_squad_stats(self) -> Dict[str, dict]:
        """Revenue pro Squad."""
        squads: Dict[str, dict] = {}
        for agent_id, agent_data in self.data["agents"].items():
            squad = agent_data.get("squad", "general")
            if squad not in squads:
                squads[squad] = {"agents": 0, "revenue": 0.0, "tasks": 0}
            squads[squad]["agents"] += 1
            squads[squad]["revenue"] += agent_data.get("revenue", 0)
            squads[squad]["tasks"] += agent_data.get("tasks_completed", 0)
        return squads

    # ── Display ─────────────────────────────────────────────

    def format_leaderboard(self, limit: int = 10) -> str:
        """Formatiertes Leaderboard fuer Terminal-Ausgabe."""
        board = self.get_leaderboard(limit)
        if not board:
            return "  Keine Agents registriert."

        lines = [
            "  RANK  AGENT                    REVENUE    TASKS  MULTI  SQUAD",
            "  " + "-" * 70,
        ]

        medals = {1: ">>", 2: "> ", 3: "> "}

        for entry in board:
            prefix = medals.get(entry["rank"], "  ")
            lines.append(
                f"  {prefix}{entry['rank']:2d}.  "
                f"{entry['agent_id']:<24s} "
                f"EUR {entry['revenue']:>8.2f}  "
                f"{entry['tasks_completed']:>5d}  "
                f"{entry['multiplier']:>4.1f}x  "
                f"{entry['squad']}"
            )

        total_rev = sum(e["revenue"] for e in board)
        lines.append("  " + "-" * 70)
        lines.append(f"  TOTAL: EUR {total_rev:.2f} | {len(board)} Agents")

        return "\n".join(lines)

    def get_summary(self) -> dict:
        """Kompakte Zusammenfassung fuer Integration."""
        board = self.get_leaderboard(10)
        squads = self.get_squad_stats()
        return {
            "total_agents": len(self.data["agents"]),
            "total_revenue": sum(a.get("revenue", 0) for a in self.data["agents"].values()),
            "top_agent": board[0]["agent_id"] if board else "none",
            "top_revenue": board[0]["revenue"] if board else 0,
            "squads": squads,
            "updated": self.data.get("meta", {}).get("updated", "never"),
        }


# ── Standalone Test ─────────────────────────────────────────

def _demo():
    """Demo mit simulierten Agents."""
    import random

    print("=" * 60)
    print("  AGENT MANAGER - Demo")
    print("=" * 60)

    manager = AgentManager(rankings_file=str(STATE_DIR / "agent_rankings_demo.json"))

    # Agents registrieren
    agents = [
        ("lead_hunter_01", "sales", "lead_gen"),
        ("lead_hunter_02", "sales", "lead_gen"),
        ("content_king_01", "content", "writer"),
        ("content_king_02", "content", "writer"),
        ("viral_reply_01", "content", "engagement"),
        ("bma_expert_01", "consulting", "specialist"),
        ("seo_engine_01", "product", "seo"),
        ("gumroad_agent_01", "product", "sales"),
        ("kimi_swarm_lead", "operations", "orchestrator"),
        ("analytics_01", "operations", "analytics"),
        ("security_guard_01", "security", "monitor"),
        ("trend_scanner_01", "content", "research"),
    ]

    for agent_id, squad, role in agents:
        manager.register_agent(agent_id, squad, role)

    # Revenue simulieren (50 Runden)
    print("\n  Simuliere 50 Revenue-Runden...\n")
    total = 0
    for _ in range(50):
        agent_id = random.choice(agents)[0]
        amount = random.uniform(0, 80)
        manager.record_revenue(agent_id, amount, "simulation")
        manager.record_task(agent_id, success=random.random() > 0.1)
        total += amount

    # Leaderboard
    print(manager.format_leaderboard())

    # Task Allocation Beispiel
    print(f"\n  TASK ALLOCATION (Base: 100 Tasks):")
    for entry in manager.get_leaderboard(5):
        allocated = manager.allocate_tasks(entry["agent_id"], 100)
        print(f"    {entry['agent_id']:<24s} → {allocated} Tasks ({entry['multiplier']}x)")

    # Squad Stats
    print(f"\n  SQUAD STATS:")
    for squad, stats in manager.get_squad_stats().items():
        print(f"    {squad:<12s}: {stats['agents']} Agents | EUR {stats['revenue']:.2f} | {stats['tasks']} Tasks")

    print(f"\n  Total Revenue: EUR {total:.2f}")
    print("=" * 60)

    # Demo-File aufraeumen
    demo_file = STATE_DIR / "agent_rankings_demo.json"
    if demo_file.exists():
        demo_file.unlink()


if __name__ == "__main__":
    _demo()
