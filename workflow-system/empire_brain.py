#!/usr/bin/env python3
"""
EMPIRE BRAIN - Das zentrale Gehirn.
Verbindet ALLES: Ollama + Kimi + Agents + Revenue + Knowledge.

Dirk Kreuter Prinzip: Vertrieb ist ALLES. Jeder Agent, jeder Task,
jede Entscheidung dient dem Revenue.

Architecture:
    EmpireBrain
    ├── OllamaEngine     (lokales LLM, $0)
    ├── AgentManager     (Revenue-Ranking)
    ├── KnowledgeHarvester (Wissens-Basis)
    ├── ResourceGuard    (System-Schutz)
    └── KimiSwarmBridge  (50K-500K Agents)

Usage:
    python empire_brain.py                # Status + Analyse
    python empire_brain.py --think        # Ein Denk-Zyklus
    python empire_brain.py --revenue      # Revenue-Fokus Analyse
    python empire_brain.py --connect      # Alle Systeme verbinden
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

from ollama_engine import OllamaEngine, LLMResponse
from agent_manager import AgentManager
from knowledge_harvester import KnowledgeHarvester
from resource_guard import ResourceGuard

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = Path(__file__).parent / "state"
BRAIN_STATE_FILE = STATE_DIR / "brain_state.json"

# Kimi API fuer Swarm Power
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")


class EmpireBrain:
    """Das zentrale Gehirn - verbindet alle Systeme zu einer Geldmaschine."""

    def __init__(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.ollama = OllamaEngine()
        self.agents = AgentManager()
        self.knowledge = KnowledgeHarvester()
        self.guard = ResourceGuard()
        self.state = self._load_state()

    def _load_state(self) -> dict:
        if BRAIN_STATE_FILE.exists():
            try:
                return json.loads(BRAIN_STATE_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "think_cycles": 0,
            "decisions": [],
            "revenue_total": 0.0,
            "created": datetime.now().isoformat(),
        }

    def _save_state(self):
        self.state["updated"] = datetime.now().isoformat()
        BRAIN_STATE_FILE.write_text(json.dumps(self.state, indent=2, ensure_ascii=False))

    # ── System Check ────────────────────────────────────────

    async def check_all_systems(self) -> dict:
        """Prueft alle verbundenen Systeme."""
        results = {}

        # 1. Ollama
        ollama_ok = await self.ollama.health_check()
        models = await self.ollama.list_models() if ollama_ok else []
        results["ollama"] = {
            "status": "online" if ollama_ok else "offline",
            "models": models,
            "stats": self.ollama.get_stats(),
        }

        # 2. Agent Manager
        summary = self.agents.get_summary()
        results["agents"] = {
            "status": "active",
            "total": summary["total_agents"],
            "revenue": summary["total_revenue"],
            "top_agent": summary["top_agent"],
        }

        # 3. Knowledge Base
        topics = self.knowledge.list_topics()
        results["knowledge"] = {
            "status": "active",
            "topics": len(topics),
            "nuggets": len(self.knowledge.knowledge_base.get("gold_nuggets", [])),
        }

        # 4. Resource Guard
        guard_status = self.guard.get_status()
        results["resources"] = {
            "status": guard_status.get("level", "unknown"),
            "cpu": guard_status.get("cpu_percent", 0),
            "ram": guard_status.get("ram_percent", 0),
        }

        # 5. Kimi Swarm
        results["kimi_swarm"] = {
            "status": "available" if MOONSHOT_API_KEY else "no_api_key",
            "api_key_set": bool(MOONSHOT_API_KEY),
        }

        # 6. Key Directories
        dirs_check = {}
        for d in ["kimi-swarm", "atomic-reactor", "x-lead-machine", "crm", "openclaw-config"]:
            path = PROJECT_ROOT / d
            dirs_check[d] = "exists" if path.exists() else "missing"
        results["directories"] = dirs_check

        return results

    # ── Think Cycle ─────────────────────────────────────────

    async def think(self, focus: str = "revenue") -> dict:
        """Ein Denk-Zyklus: Analyse → Entscheidung → Aktion.

        Dirk Kreuter: "Verkaufen ist die Koenigsklasse der Kommunikation."
        Jeder Denk-Zyklus endet mit einer konkreten Revenue-Aktion.
        """
        start = time.time()

        print(f"\n{'='*60}")
        print(f"  EMPIRE BRAIN - Think Cycle #{self.state['think_cycles'] + 1}")
        print(f"  Focus: {focus.upper()}")
        print(f"  Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        # Phase 1: Observe - Was wissen wir?
        print("\n  Phase 1: OBSERVE")
        systems = await self.check_all_systems()
        await self.knowledge.scan_codebase()

        # Phase 2: Analyse - Was bedeutet das?
        print("  Phase 2: ANALYSE")
        analysis_prompt = self._build_analysis_prompt(systems, focus)

        # Versuche Ollama, sonst statische Analyse
        response = await self.ollama.chat([
            {"role": "system", "content": self._brain_system_prompt()},
            {"role": "user", "content": analysis_prompt},
        ])

        if response.success:
            analysis = response.content
            print(f"    LLM Analyse: {len(analysis)} chars ({response.duration_ms:.0f}ms)")
        else:
            analysis = self._static_analysis(systems, focus)
            print(f"    Static Analyse (Ollama offline): {len(analysis)} chars")

        # Phase 3: Decide - Was tun wir als naechstes?
        print("  Phase 3: DECIDE")
        decisions = self._extract_decisions(analysis, focus)

        # Phase 4: Record
        self.state["think_cycles"] += 1
        self.state["decisions"].append({
            "cycle": self.state["think_cycles"],
            "focus": focus,
            "decisions": decisions,
            "timestamp": datetime.now().isoformat(),
        })
        # Halte letzte 100 Decisions
        if len(self.state["decisions"]) > 100:
            self.state["decisions"] = self.state["decisions"][-100:]
        self._save_state()

        elapsed = time.time() - start

        print(f"\n  DECISIONS:")
        for i, d in enumerate(decisions, 1):
            print(f"    {i}. {d}")

        print(f"\n  Duration: {elapsed:.1f}s")
        print(f"  Total Think Cycles: {self.state['think_cycles']}")
        print(f"{'='*60}")

        return {
            "cycle": self.state["think_cycles"],
            "focus": focus,
            "analysis_length": len(analysis),
            "decisions": decisions,
            "duration_sec": elapsed,
            "systems": systems,
        }

    def _brain_system_prompt(self) -> str:
        return """Du bist das EMPIRE BRAIN - das zentrale Gehirn von Maurice's AI Empire.

DEIN ZIEL: Maximale Revenue generieren. Jede Entscheidung muss auf Geld einzahlen.

DIRK KREUTER PRINZIPIEN:
1. Vertrieb ist ALLES - ohne Verkauf kein Business
2. Aktivitaet schlaegt Perfektion - lieber 80% und MACHEN
3. Follow-up ist King - 80% der Abschluesse nach dem 5. Kontakt
4. Kenne deinen Kunden besser als er sich selbst
5. Einwandbehandlung ist eine Chance, kein Problem

KONTEXT:
- Maurice Pfeifer, 33, Elektrotechnikmeister, 16 Jahre BMA-Expertise
- Unique: BMA + AI = unbesetzter Markt
- Budget: max 100 EUR/Monat
- Hardware: Mac Mini M4 mit Ollama
- Revenue-Ziel: 500-1000 EUR Monat 1

Antworte IMMER mit konkreten, sofort umsetzbaren Aktionen.
Format: Nummerierte Liste mit klaren naechsten Schritten."""

    def _build_analysis_prompt(self, systems: dict, focus: str) -> str:
        ollama_status = systems.get("ollama", {}).get("status", "unknown")
        agent_count = systems.get("agents", {}).get("total", 0)
        revenue = systems.get("agents", {}).get("revenue", 0)
        topics = systems.get("knowledge", {}).get("topics", 0)
        kimi_ok = systems.get("kimi_swarm", {}).get("api_key_set", False)

        return f"""SYSTEM STATUS:
- Ollama: {ollama_status} | Models: {', '.join(systems.get('ollama', {}).get('models', []))}
- Agents: {agent_count} registriert | Revenue: EUR {revenue:.2f}
- Knowledge: {topics} Topics
- Kimi Swarm: {'verfuegbar' if kimi_ok else 'kein API Key'}
- Ressourcen: CPU {systems.get('resources', {}).get('cpu', 0)}% | RAM {systems.get('resources', {}).get('ram', 0)}%

FOKUS: {focus.upper()}

FRAGE: Was sind die 5 wichtigsten Aktionen die JETZT passieren muessen
um in den naechsten 7 Tagen maximalen Revenue zu generieren?

Beruecksichtige:
- BMA + AI ist eine unbesetzte Nische
- Fiverr/Gumroad sind sofort aktivierbar
- TikTok/X Content kann sofort gestartet werden
- Ollama laeuft lokal und kostet nichts
- Es gibt 50K-500K Kimi Agents bei Bedarf"""

    def _static_analysis(self, systems: dict, focus: str) -> str:
        """Fallback wenn Ollama offline ist."""
        actions = []

        if focus == "revenue":
            actions = [
                "Fiverr: 3 AI-Automation Gigs erstellen (30-500 EUR)",
                "Gumroad: BMA Checklisten-Pack hochladen (27 EUR)",
                "X/Twitter: 3 Posts mit CTA vorbereiten",
                "BMA-Netzwerk: 5 ehemalige Kollegen kontaktieren fuer Consulting",
                "TikTok: Ersten Account + 3 Testvideos erstellen",
            ]
        elif focus == "content":
            actions = [
                "X/Twitter: Wochen-Content aus READY_TO_POST.md posten",
                "TikTok: 3 BMA-Tipps als Kurzvideos scripten",
                "LinkedIn: Profil auf AI+BMA Consulting optimieren",
                "Blog: Ersten Artikel 'BMA + AI' schreiben",
                "Newsletter: Landing Page aufsetzen",
            ]
        elif focus == "automation":
            actions = [
                "Ollama Pipeline testen und optimieren",
                "Kimi Swarm: 1000er Test-Run starten",
                "n8n: Content-Pipeline Workflow aufsetzen",
                "CRM: BANT-Scoring fuer Leads aktivieren",
                "Cron Jobs: Alle 9 OpenClaw Jobs verifizieren",
            ]
        else:
            actions = [
                "Revenue-Kanaele aktivieren (Fiverr, Gumroad)",
                "Content-Pipeline starten (X, TikTok)",
                "Systeme testen (Ollama, Kimi, CRM)",
                "Knowledge Base aktualisieren",
                "Agent-Rankings reviewen",
            ]

        return "\n".join(f"{i+1}. {a}" for i, a in enumerate(actions))

    def _extract_decisions(self, analysis: str, focus: str) -> List[str]:
        """Extrahiert konkrete Entscheidungen aus der Analyse."""
        decisions = []
        for line in analysis.strip().split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                clean = line.lstrip("0123456789.-) ").strip()
                if clean and len(clean) > 10:
                    decisions.append(clean)
        return decisions[:7] if decisions else [
            "Revenue-Kanaele sofort aktivieren",
            "Ersten Content posten",
            "System-Tests durchfuehren",
        ]

    # ── Connect All ─────────────────────────────────────────

    async def connect_all(self):
        """Verbindet alle Systeme und zeigt den Status."""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗███╗   ███╗██████╗ ██╗██████╗ ███████╗            ║
║   ██╔════╝████╗ ████║██╔══██╗██║██╔══██╗██╔════╝            ║
║   █████╗  ██╔████╔██║██████╔╝██║██████╔╝█████╗              ║
║   ██╔══╝  ██║╚██╔╝██║██╔═══╝ ██║██╔══██╗██╔══╝              ║
║   ███████╗██║ ╚═╝ ██║██║     ██║██║  ██║███████╗            ║
║   ╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝            ║
║                                                              ║
║           B R A I N  -  Connected Systems                    ║
║           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                              ║
╚══════════════════════════════════════════════════════════════╝
        """)

        systems = await self.check_all_systems()

        # Ollama
        o = systems["ollama"]
        status_icon = "ON " if o["status"] == "online" else "OFF"
        models_str = ", ".join(o["models"][:3]) if o["models"] else "none"
        print(f"  [{status_icon}] OLLAMA ENGINE")
        print(f"        Models: {models_str}")
        print(f"        Stats: {self.ollama.format_stats()}")
        print()

        # Agent Manager
        a = systems["agents"]
        print(f"  [ON ] AGENT MANAGER")
        print(f"        Agents: {a['total']} | Revenue: EUR {a['revenue']:.2f} | Top: {a['top_agent']}")
        if a["total"] > 0:
            print(f"\n{self.agents.format_leaderboard(5)}")
        print()

        # Knowledge
        k = systems["knowledge"]
        print(f"  [ON ] KNOWLEDGE HARVESTER")
        print(f"        Topics: {k['topics']} | Nuggets: {k['nuggets']}")
        print()

        # Resources
        r = systems["resources"]
        print(f"  [ON ] RESOURCE GUARD")
        print(f"        Level: {r['status']} | CPU: {r['cpu']}% | RAM: {r['ram']}%")
        print()

        # Kimi Swarm
        ks = systems["kimi_swarm"]
        kimi_icon = "ON " if ks["api_key_set"] else "OFF"
        print(f"  [{kimi_icon}] KIMI SWARM BRIDGE")
        print(f"        API Key: {'Set' if ks['api_key_set'] else 'NOT SET (set MOONSHOT_API_KEY)'}")
        print()

        # Directories
        d = systems["directories"]
        print(f"  [---] SUBSYSTEMS")
        for name, status in d.items():
            icon = "OK" if status == "exists" else "!!"
            print(f"        [{icon}] {name}")
        print()

        # Brain State
        print(f"  [ON ] EMPIRE BRAIN")
        print(f"        Think Cycles: {self.state['think_cycles']}")
        print(f"        Decisions: {len(self.state['decisions'])}")
        print(f"        Revenue Tracked: EUR {self.state.get('revenue_total', 0):.2f}")
        print()

        print("  COMMANDS:")
        print("    python empire_brain.py --think          # Ein Denk-Zyklus")
        print("    python empire_brain.py --think --focus revenue")
        print("    python empire_brain.py --connect        # System-Check")
        print("    python empire.py status                 # Empire CLI")
        print()

        return systems

    # ── Revenue Analyse ─────────────────────────────────────

    async def revenue_analysis(self) -> dict:
        """Fokussierte Revenue-Analyse nach Dirk Kreuter."""
        print(f"\n{'='*60}")
        print(f"  REVENUE ANALYSE - Dirk Kreuter Modus")
        print(f"{'='*60}")

        # Agent Leaderboard
        print(f"\n  TOP PERFORMER:")
        print(self.agents.format_leaderboard(5))

        # Squad Revenue
        print(f"\n  SQUAD PERFORMANCE:")
        squads = self.agents.get_squad_stats()
        for squad, stats in sorted(squads.items(), key=lambda x: x[1]["revenue"], reverse=True):
            print(f"    {squad:<12s}: EUR {stats['revenue']:>8.2f} | {stats['agents']} Agents | {stats['tasks']} Tasks")

        # Revenue Channels Status
        print(f"\n  REVENUE CHANNELS:")
        channels = {
            "Fiverr/Upwork": "NOT ACTIVE - Gigs erstellen!",
            "Gumroad": "NOT ACTIVE - Produkte hochladen!",
            "BMA Consulting": "NOT ACTIVE - Netzwerk kontaktieren!",
            "TikTok": "NOT ACTIVE - Account erstellen!",
            "X/Twitter": "READY - Content in READY_TO_POST.md",
        }
        for channel, status in channels.items():
            icon = "!!" if "NOT" in status else "OK"
            print(f"    [{icon}] {channel:<20s}: {status}")

        # Think with revenue focus
        result = await self.think(focus="revenue")

        print(f"\n  DIRK KREUTER REMINDER:")
        print(f"    'Wer nicht verkauft, hat keinen Umsatz.'")
        print(f"    'Aktivitaet schlaegt Perfektion.'")
        print(f"    'Jeder Tag ohne Angebot ist ein verlorener Tag.'")
        print(f"{'='*60}")

        return result


async def main():
    parser = argparse.ArgumentParser(description="Empire Brain - Zentrales Gehirn")
    parser.add_argument("--think", action="store_true", help="Ein Denk-Zyklus ausfuehren")
    parser.add_argument("--revenue", action="store_true", help="Revenue-Fokus Analyse")
    parser.add_argument("--connect", action="store_true", help="Alle Systeme verbinden + Status")
    parser.add_argument("--focus", default="revenue",
                       choices=["revenue", "content", "automation", "product"],
                       help="Fokus-Bereich fuer Think-Zyklus")
    args = parser.parse_args()

    brain = EmpireBrain()

    if args.think:
        await brain.think(focus=args.focus)
    elif args.revenue:
        await brain.revenue_analysis()
    elif args.connect:
        await brain.connect_all()
    else:
        await brain.connect_all()


if __name__ == "__main__":
    asyncio.run(main())
