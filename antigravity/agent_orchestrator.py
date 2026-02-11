#!/usr/bin/env python3
"""
Agent Orchestrator — Autonomous Multi-Agent System
====================================================
Manages all AI agents with automatic task routing,
cross-verification, and persistent learning.

100% Freeware: Runs entirely on Ollama (local, free).
Cloud providers (Kimi, Gemini) are optional upgrades.

Agents:
  - Scanner: News, trends, opportunities
  - Producer: Content creation (X, LinkedIn, YouTube)
  - Architect: Code architecture & planning
  - Fixer: Bug detection & repair
  - QA: Quality assurance & verification

Usage:
    from antigravity.agent_orchestrator import Orchestrator
    orch = Orchestrator()

    # Run a single agent task
    result = await orch.run("scanner", "Finde AI Trends Februar 2026")

    # Run full autonomous cycle
    results = await orch.auto_cycle()

    # Cross-verified execution (2 agents verify each other)
    result = await orch.verified_run("architect", "Review empire_boot.py")
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


# ─── Agent Definitions ──────────────────────────────────────────

AGENTS = {
    "scanner": {
        "name": "Scanner",
        "model": "qwen2.5-coder:7b",
        "system": """Du bist der SCANNER Agent im AI Empire System.
Deine Aufgabe: Analysiere Trends, News und Opportunities.
Output IMMER als JSON: {"trends": [...], "opportunities": [...], "summary": "..."}
Sprache: Deutsch. Fokus: AI, Automation, BMA (Brandmeldeanlagen).""",
    },
    "producer": {
        "name": "Producer",
        "model": "qwen2.5-coder:7b",
        "system": """Du bist der PRODUCER Agent im AI Empire System.
Deine Aufgabe: Erstelle viralen Content fuer X/Twitter, LinkedIn, YouTube.
Output IMMER als JSON: {"posts": [{"platform": "x", "content": "...", "hook": "..."}]}
Schreibe auf Deutsch. Maximal 280 Zeichen fuer X. Hook muss Scroll stoppen.""",
    },
    "architect": {
        "name": "Architect",
        "model": "qwen2.5-coder:7b",
        "system": """Du bist der ARCHITECT Agent im AI Empire System.
Deine Aufgabe: Analysiere und optimiere Code-Architektur.
Output als JSON: {"analysis": "...", "issues": [...], "recommendations": [...]}
Minimal-invasive Vorschlaege. Begruende jede Aenderung.""",
    },
    "fixer": {
        "name": "Fixer",
        "model": "qwen2.5-coder:7b",
        "system": """Du bist der FIXER Agent im AI Empire System.
Deine Aufgabe: Finde und fixe Bugs. Minimal-invasiv.
Output als JSON: {"bug": "...", "fix": "...", "file": "...", "test": "..."}
NIEMALS Features hinzufuegen, NUR Bugs fixen.""",
    },
    "qa": {
        "name": "QA Reviewer",
        "model": "qwen2.5-coder:7b",
        "system": """Du bist der QA Agent im AI Empire System.
Deine Aufgabe: Review Code, teste Aenderungen, pruefe Qualitaet.
Output als JSON: {"approved": true/false, "issues": [...], "score": 0-10}
Sei streng aber fair. Jedes Issue muss begruendet sein.""",
    },
}


class Orchestrator:
    """Autonomous multi-agent orchestrator."""

    def __init__(self, prefer_provider: str = "auto"):
        self.prefer = prefer_provider
        self._chain = None
        self.results_dir = ROOT / "empire_data" / "agent_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    @property
    def chain(self):
        """Lazy-load provider chain."""
        if self._chain is None:
            from antigravity.provider_chain import ProviderChain
            self._chain = ProviderChain()
        return self._chain

    async def run(self, agent_key: str, task: str,
                  context: str = "", prefer: str = "") -> dict:
        """Run a single agent task."""
        agent = AGENTS.get(agent_key)
        if not agent:
            return {"success": False, "error": f"Unknown agent: {agent_key}"}

        prompt = task
        if context:
            prompt = f"KONTEXT:\n{context}\n\nAUFGABE:\n{task}"

        result = await self.chain.query(
            prompt=prompt,
            system=agent["system"],
            prefer=prefer or self.prefer,
        )

        # Save result
        result["agent"] = agent_key
        result["task"] = task[:200]
        result["timestamp"] = datetime.now().isoformat()

        self._save_result(agent_key, result)
        return result

    async def verified_run(self, agent_key: str, task: str,
                           context: str = "") -> dict:
        """Run with cross-verification (2nd agent reviews output)."""
        # Step 1: Primary agent executes
        primary = await self.run(agent_key, task, context)
        if not primary.get("success"):
            return primary

        # Step 2: QA agent reviews (never self-review)
        review_agent = "qa" if agent_key != "qa" else "architect"
        review_task = f"""Review diese Agent-Ausgabe auf Korrektheit:

ORIGINAL TASK: {task}
AGENT OUTPUT: {primary.get('content', '')[:2000]}

Bewerte: Ist die Ausgabe korrekt und vollstaendig?"""

        review = await self.run(review_agent, review_task)

        return {
            "primary": primary,
            "review": review,
            "verified": True,
            "success": primary.get("success", False),
        }

    async def auto_cycle(self) -> dict:
        """Run full autonomous cycle: Scan → Produce → Review."""
        print("\n=== AUTONOMOUS CYCLE ===\n")
        results = {}

        # Step 1: Scan
        print("Step 1/3: Scanning trends...")
        results["scan"] = await self.run(
            "scanner",
            "Scanne aktuelle AI und Automation Trends. Was ist viral? Was sind Opportunities?"
        )
        print(f"  → {results['scan'].get('provider', '?')} ({results['scan'].get('model', '?')})")

        # Step 2: Produce content based on scan
        print("Step 2/3: Producing content...")
        scan_content = results["scan"].get("content", "AI Automation Trends")
        results["produce"] = await self.run(
            "producer",
            f"Erstelle 3 virale X-Posts basierend auf: {scan_content[:500]}"
        )
        print(f"  → {results['produce'].get('provider', '?')}")

        # Step 3: QA review
        print("Step 3/3: Quality review...")
        results["qa"] = await self.run(
            "qa",
            f"Review diesen Content auf Qualitaet:\n{results['produce'].get('content', '')[:1000]}"
        )
        print(f"  → {results['qa'].get('provider', '?')}")

        results["timestamp"] = datetime.now().isoformat()
        results["success"] = all(r.get("success") for r in [results["scan"], results["produce"], results["qa"]])

        print(f"\n=== CYCLE {'COMPLETE' if results['success'] else 'FAILED'} ===\n")
        return results

    def _save_result(self, agent_key: str, result: dict):
        """Save agent result to disk."""
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.results_dir / f"{agent_key}_{ts}.json"
            path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        except Exception:
            pass


# ─── CLI ──────────────────────────────────────────────────────

async def _main():
    import argparse
    parser = argparse.ArgumentParser(description="Agent Orchestrator")
    parser.add_argument("command", nargs="?", default="status",
                        choices=["status", "auto", "scan", "produce", "review", "ask"])
    parser.add_argument("task", nargs="*", default=[])
    parser.add_argument("--provider", "-p", default="auto")
    args = parser.parse_args()

    orch = Orchestrator(prefer_provider=args.provider)

    if args.command == "status":
        print("Agent Orchestrator - Available Agents:")
        for key, agent in AGENTS.items():
            print(f"  • {agent['name']} ({key}) - Model: {agent['model']}")
        print(f"\nProvider: {args.provider}")
        health = await orch.chain.health_check()
        for name, info in health.items():
            status = "✓" if info["available"] else "✗"
            print(f"  {status} {name}")

    elif args.command == "auto":
        await orch.auto_cycle()

    elif args.command == "scan":
        result = await orch.run("scanner", " ".join(args.task) or "AI Trends scannen")
        print(result.get("content", "No result"))

    elif args.command == "produce":
        result = await orch.run("producer", " ".join(args.task) or "3 virale Posts erstellen")
        print(result.get("content", "No result"))

    elif args.command == "review":
        result = await orch.run("qa", " ".join(args.task) or "System-Review durchfuehren")
        print(result.get("content", "No result"))

    elif args.command == "ask":
        task = " ".join(args.task) or "Was ist der aktuelle Status?"
        result = await orch.chain.query(task)
        print(f"[{result.get('provider')}] {result.get('content', 'No result')}")


if __name__ == "__main__":
    asyncio.run(_main())
