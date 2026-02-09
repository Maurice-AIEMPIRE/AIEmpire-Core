#!/usr/bin/env python3
"""
KNOWLEDGE HARVESTER - Wissen sammeln, speichern, nutzen.
Scannt Codebase, externe Quellen und eigene Outputs.

Usage:
    python knowledge_harvester.py              # Voller Harvest
    python knowledge_harvester.py --status     # Zeige Knowledge Base
"""

import os
import json
import logging
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STATE_DIR = Path(__file__).parent / "state"
KNOWLEDGE_FILE = STATE_DIR / "knowledge_context.json"
PROJECT_ROOT = Path(__file__).parent.parent


class KnowledgeHarvester:
    """Sammelt und strukturiert Wissen aus allen Quellen."""

    def __init__(self, knowledge_file: Optional[Path] = None):
        self.knowledge_file = knowledge_file or KNOWLEDGE_FILE
        self.knowledge_file.parent.mkdir(parents=True, exist_ok=True)
        self.knowledge_base = self._load()

    def _load(self) -> dict:
        """Laedt Knowledge Base."""
        if self.knowledge_file.exists():
            try:
                return json.loads(self.knowledge_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return self._default_knowledge()

    def _default_knowledge(self) -> dict:
        return {
            "topics": {
                "OpenClaw": {
                    "summary": "Open Source AI Agent auf GitHub (100K+ Stars)",
                    "details": "",
                    "urls": ["https://github.com/openclaw/openclaw"],
                    "last_updated": "",
                },
                "AI_Trends": {
                    "summary": "Aktuelle AI Trends und Opportunities",
                    "details": "",
                    "urls": [],
                    "last_updated": "",
                },
                "BMA_Expertise": {
                    "summary": "Brandmeldeanlagen - 16 Jahre Expertise (Esser, Hekatron)",
                    "details": "Maurice Pfeifer, 33, Elektrotechnikmeister. Einziger mit BMA+AI Kombination.",
                    "urls": [],
                    "last_updated": "",
                },
                "Revenue_Channels": {
                    "summary": "Gumroad, Fiverr, Consulting, TikTok, X/Twitter",
                    "details": "",
                    "urls": [],
                    "last_updated": "",
                },
                "System_Architecture": {
                    "summary": "Ollama + Kimi + Claude, OpenClaw, Atomic Reactor",
                    "details": "",
                    "urls": [],
                    "last_updated": "",
                },
            },
            "codebase_scan": {},
            "gold_nuggets": [],
            "meta": {
                "version": 2.0,
                "created": datetime.now().isoformat(),
            },
        }

    def save(self):
        """Speichert Knowledge Base."""
        self.knowledge_base["meta"]["updated"] = datetime.now().isoformat()
        self.knowledge_file.write_text(
            json.dumps(self.knowledge_base, indent=2, ensure_ascii=False)
        )
        logger.info(f"Knowledge saved to {self.knowledge_file}")

    # ── Topic Management ────────────────────────────────────

    def update_topic(self, topic: str, content: str, source_url: str = ""):
        """Aktualisiert ein Topic."""
        topics = self.knowledge_base["topics"]
        if topic not in topics:
            topics[topic] = {"summary": "", "details": "", "urls": [], "last_updated": ""}

        topics[topic]["summary"] = content[:500]
        if len(content) > 500:
            topics[topic]["details"] = content
        if source_url and source_url not in topics[topic]["urls"]:
            topics[topic]["urls"].append(source_url)
        topics[topic]["last_updated"] = datetime.now().isoformat()
        self.save()

    def get_topic(self, topic: str) -> Optional[dict]:
        """Holt Topic-Infos."""
        return self.knowledge_base["topics"].get(topic)

    def list_topics(self) -> List[str]:
        """Alle Topics."""
        return list(self.knowledge_base["topics"].keys())

    # ── Codebase Scan ───────────────────────────────────────

    async def scan_codebase(self):
        """Scannt die Projektstruktur und erfasst Capabilities."""
        logger.info("Scanning codebase...")

        scan = {
            "scanned_at": datetime.now().isoformat(),
            "directories": {},
            "capabilities": [],
            "file_count": 0,
            "python_files": 0,
            "md_files": 0,
        }

        key_dirs = [
            "workflow-system",
            "kimi-swarm",
            "atomic-reactor",
            "x-lead-machine",
            "crm",
            "openclaw-config",
            "gold-nuggets",
            "docs",
            "systems",
        ]

        for dir_name in key_dirs:
            dir_path = PROJECT_ROOT / dir_name
            if dir_path.exists():
                files = list(dir_path.rglob("*"))
                file_list = [str(f.relative_to(PROJECT_ROOT)) for f in files if f.is_file()]
                py_count = sum(1 for f in file_list if f.endswith(".py"))
                md_count = sum(1 for f in file_list if f.endswith(".md"))

                scan["directories"][dir_name] = {
                    "files": len(file_list),
                    "python": py_count,
                    "markdown": md_count,
                }
                scan["file_count"] += len(file_list)
                scan["python_files"] += py_count
                scan["md_files"] += md_count

        # Capabilities aus vorhandenen Dateien ableiten
        capability_map = {
            "workflow-system/orchestrator.py": "5-Step Compound Workflow (AUDIT-ARCHITECT-ANALYST-REFINERY-COMPOUNDER)",
            "workflow-system/cowork.py": "Autonomous Cowork Engine (Observe-Plan-Act-Reflect)",
            "workflow-system/ollama_engine.py": "Local LLM Engine (Ollama, $0 cost)",
            "workflow-system/agent_manager.py": "Revenue-Based Agent Ranking",
            "workflow-system/resource_guard.py": "CPU/RAM/Disk Auto-Throttling",
            "workflow-system/empire.py": "Unified Empire Control Center",
            "kimi-swarm/swarm_500k.py": "500K Kimi Agent Swarm",
            "kimi-swarm/swarm_100k.py": "100K Kimi Agent Swarm",
            "x-lead-machine/post_generator.py": "X/Twitter Content Generator",
            "x-lead-machine/viral_reply_generator.py": "Viral Reply Engine",
            "atomic-reactor/task_runner.py": "YAML-Based Task Runner",
            "crm/server.js": "Express.js CRM with BANT Scoring",
        }

        for filepath, capability in capability_map.items():
            if (PROJECT_ROOT / filepath).exists():
                scan["capabilities"].append(capability)

        self.knowledge_base["codebase_scan"] = scan
        self.save()

        logger.info(f"Scan complete: {scan['file_count']} files, {len(scan['capabilities'])} capabilities")
        return scan

    # ── Gold Nugget Harvesting ──────────────────────────────

    async def harvest_gold_nuggets(self):
        """Scannt gold-nuggets/ Verzeichnis und extrahiert Erkenntnisse."""
        logger.info("Harvesting gold nuggets...")

        nuggets_dir = PROJECT_ROOT / "gold-nuggets"
        if not nuggets_dir.exists():
            logger.info("Keine gold-nuggets/ gefunden.")
            return

        nuggets = []
        for md_file in sorted(nuggets_dir.glob("*.md")):
            content = md_file.read_text(errors="replace")
            title = content.split("\n")[0].replace("#", "").strip() if content else md_file.stem

            nuggets.append({
                "file": md_file.name,
                "title": title,
                "size": len(content),
                "extracted_at": datetime.now().isoformat(),
            })

        self.knowledge_base["gold_nuggets"] = nuggets
        self.save()

        logger.info(f"Harvested {len(nuggets)} gold nuggets")
        return nuggets

    # ── System Reflection ───────────────────────────────────

    async def reflect_on_system(self):
        """Analysiert das eigene System und fasst zusammen."""
        logger.info("System self-reflection...")

        scan = self.knowledge_base.get("codebase_scan", {})
        capabilities = scan.get("capabilities", [])
        topics = self.knowledge_base.get("topics", {})
        nuggets = self.knowledge_base.get("gold_nuggets", [])

        reflection = {
            "timestamp": datetime.now().isoformat(),
            "total_capabilities": len(capabilities),
            "total_topics": len(topics),
            "total_nuggets": len(nuggets),
            "total_files": scan.get("file_count", 0),
            "strengths": [],
            "gaps": [],
        }

        # Staerken erkennen
        if any("Ollama" in c for c in capabilities):
            reflection["strengths"].append("Lokale LLM Power (kostenlos)")
        if any("Swarm" in c for c in capabilities):
            reflection["strengths"].append("Massive Agent Swarm Kapazitaet")
        if any("Workflow" in c for c in capabilities):
            reflection["strengths"].append("Strukturierter 5-Step Workflow")
        if any("CRM" in c for c in capabilities):
            reflection["strengths"].append("Lead Management mit BANT Scoring")
        if any("Revenue" in c for c in capabilities):
            reflection["strengths"].append("Revenue-basiertes Agent Ranking")

        # Luecken erkennen
        if not any("TikTok" in c for c in capabilities):
            reflection["gaps"].append("TikTok Content Pipeline fehlt")
        if not any("Digistore" in c for c in capabilities):
            reflection["gaps"].append("Digistore24 Integration fehlt")
        if not any("Email" in c for c in capabilities):
            reflection["gaps"].append("Email Automation fehlt")

        self.update_topic(
            "System_Self_Reflection",
            f"Capabilities: {len(capabilities)} | Topics: {len(topics)} | "
            f"Nuggets: {len(nuggets)} | Strengths: {len(reflection['strengths'])} | "
            f"Gaps: {len(reflection['gaps'])}",
        )

        return reflection

    # ── Full Harvest ────────────────────────────────────────

    async def run_full_harvest(self):
        """Kompletter Harvest-Zyklus."""
        logger.info("Starting full knowledge harvest...")

        await self.scan_codebase()
        await self.harvest_gold_nuggets()
        reflection = await self.reflect_on_system()

        # OpenClaw Info (Bootstrap)
        self.update_topic(
            "OpenClaw",
            "OpenClaw ist ein Open-Source AI Agent (100K+ GitHub Stars). "
            "Laeuft lokal, integriert mit WhatsApp/Telegram/Discord. "
            "Fokus auf Privacy und lokale Ausfuehrung. "
            "Maurice's Empire nutzt OpenClaw als Agent-Framework mit 9 Cron Jobs.",
            "https://github.com/openclaw/openclaw",
        )

        logger.info("Full harvest complete!")
        return reflection

    # ── Display ─────────────────────────────────────────────

    def show_status(self):
        """Zeigt Knowledge Base Status."""
        topics = self.knowledge_base.get("topics", {})
        scan = self.knowledge_base.get("codebase_scan", {})
        nuggets = self.knowledge_base.get("gold_nuggets", [])
        meta = self.knowledge_base.get("meta", {})

        print(f"""
{'='*60}
  KNOWLEDGE HARVESTER - Status
{'='*60}
  Topics:       {len(topics)}
  Gold Nuggets: {len(nuggets)}
  Files Scanned:{scan.get('file_count', 0)}
  Capabilities: {len(scan.get('capabilities', []))}
  Updated:      {meta.get('updated', 'never')}

  TOPICS:""")

        for name, data in topics.items():
            updated = data.get("last_updated", "never")[:10]
            print(f"    {name:<28s} [{updated}] {data.get('summary', '')[:40]}")

        if scan.get("capabilities"):
            print(f"\n  CAPABILITIES:")
            for cap in scan["capabilities"]:
                print(f"    - {cap}")

        if nuggets:
            print(f"\n  GOLD NUGGETS:")
            for nugget in nuggets[:5]:
                print(f"    - {nugget['title'][:50]}")

        print(f"{'='*60}")


async def main():
    parser = argparse.ArgumentParser(description="Knowledge Harvester")
    parser.add_argument("--status", action="store_true", help="Zeige Knowledge Base Status")
    args = parser.parse_args()

    harvester = KnowledgeHarvester()

    if args.status:
        harvester.show_status()
    else:
        reflection = await harvester.run_full_harvest()
        harvester.show_status()


if __name__ == "__main__":
    asyncio.run(main())
