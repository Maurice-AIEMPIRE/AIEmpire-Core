"""
Mirror Cowork - Autonomer Hintergrund-Agent mit Gemini
Spiegelt workflow-system/cowork.py mit Gemini statt Kimi.

4-Phasen Zyklus (wie Original):
1. OBSERVE  - System scannen, Zustand erfassen
2. PLAN     - Naechste Aktion planen (mit Vision-Kontext)
3. ACT      - Aktion ausfuehren (Code/Content/Analysis)
4. REFLECT  - Lernen, Muster erkennen, verbessern

Unterschiede zum Original:
- Nutzt Gemini Pro/Flash statt Kimi
- Integriert Vision-Interrogator Kontext
- Cross-referenziert mit Main-Cowork Ergebnissen
- Teilt Patterns ueber Dual-Brain
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

MIRROR_DIR = Path(__file__).parent
sys.path.insert(0, str(MIRROR_DIR))

from config import (
    STATE_DIR,
    OUTPUT_DIR,
    MEMORY_DIR,
    PROJECT_ROOT,
    MODEL_ROUTING,
    VISION_MEMORY_FILE,
)
from gemini_client import GeminiClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MIRROR-COWORK] %(levelname)s %(message)s",
)
logger = logging.getLogger("mirror-cowork")

COWORK_STATE_FILE = STATE_DIR / "mirror_cowork_state.json"

FOCUS_AREAS = {
    "revenue": {
        "description": "Einnahmen generieren und monetarisieren",
        "priority_keywords": ["revenue", "gumroad", "fiverr", "consulting", "money"],
        "scan_dirs": ["gold-nuggets", "x-lead-machine"],
    },
    "content": {
        "description": "Content erstellen und verbreiten",
        "priority_keywords": ["content", "twitter", "post", "thread", "viral"],
        "scan_dirs": ["x-lead-machine"],
    },
    "automation": {
        "description": "Mehr automatisieren, weniger manuell",
        "priority_keywords": ["automate", "cron", "workflow", "pipeline"],
        "scan_dirs": ["workflow-system", "atomic-reactor", "openclaw-config"],
    },
    "product": {
        "description": "Produkte entwickeln und verbessern",
        "priority_keywords": ["product", "feature", "release", "gumroad"],
        "scan_dirs": ["atomic-reactor"],
    },
    "mirror": {
        "description": "Gemini-Mirror System verbessern",
        "priority_keywords": ["gemini", "mirror", "sync", "dual-brain"],
        "scan_dirs": ["gemini-mirror"],
    },
}


# === Prompts ===

PLAN_PROMPT = """Du bist der Mirror-Cowork Agent im AIEmpire Gemini System.
Du planst die naechste autonome Aktion.

SYSTEM-BEOBACHTUNGEN:
{observations}

AKTIVER FOKUS: {focus} - {focus_description}

BISHERIGE AKTIONEN ({action_count}):
{recent_actions}

BLOCKER:
{blockers}

VISION-KONTEXT:
{vision_context}

MAIN-SYSTEM STATUS:
{main_status}

Plane die EINE wichtigste Aktion die jetzt ausgefuehrt werden sollte.

Antworte NUR als JSON:
{{
  "priority_action": {{
    "title": "Aktions-Titel",
    "why": "Warum gerade jetzt",
    "how": ["Schritt 1", "Schritt 2"],
    "expected_impact": "Was sich verbessert",
    "effort_minutes": 0,
    "category": "revenue|content|automation|product|mirror",
    "dependencies": [],
    "success_criteria": "Woran erkennt man Erfolg",
    "dual_brain_relevance": "Wie nutzt das dem anderen System"
  }},
  "secondary_actions": [
    {{"title": "...", "why": "...", "effort_minutes": 0}}
  ],
  "situation_assessment": "Kurze Lage-Einschaetzung",
  "risk_alert": null
}}"""

ACT_PROMPT = """Du bist der Mirror-Cowork Executor im AIEmpire Gemini System.
Fuehre die geplante Aktion aus und erstelle ein konkretes Deliverable.

GEPLANTE AKTION:
{action}

KONTEXT:
{context}

Erstelle ein KONKRETES Ergebnis. Kein Blabla, sondern:
- Code der funktioniert
- Content der publishbar ist
- Analysen mit Zahlen
- Configs die deploybar sind

Antworte NUR als JSON:
{{
  "action_title": "Was ausgefuehrt wurde",
  "deliverable_type": "code|content|analysis|config|plan",
  "deliverable": "DAS TATSAECHLICHE ERGEBNIS (Code/Content/etc)",
  "files_to_create": [
    {{"path": "relativer/pfad", "content": "Dateiinhalt", "description": "Was die Datei tut"}}
  ],
  "files_to_modify": [
    {{"path": "relativer/pfad", "change": "Was aendern", "description": "Warum"}}
  ],
  "next_manual_step": null,
  "execution_notes": "Was zu beachten ist",
  "quality_score": 1-10,
  "ready_for_main": true
}}"""

REFLECT_PROMPT = """Du bist der Mirror-Cowork Reflektor im AIEmpire Gemini System.
Reflektiere ueber den gerade abgeschlossenen Zyklus.

BEOBACHTUNGEN:
{observations}

PLAN:
{plan}

AKTIONSERGEBNIS:
{action_result}

BISHERIGE PATTERNS:
{patterns}

Reflektiere ehrlich:
1. Was hat funktioniert?
2. Was nicht?
3. Welches Muster ist erkennbar?
4. Was beim naechsten Mal anders?
5. Was kann das Main-System davon lernen?

Antworte NUR als JSON:
{{
  "cycle_score": 1-10,
  "what_worked": "Was gut lief",
  "what_didnt": null,
  "pattern_discovered": {{
    "name": "Muster-Name",
    "description": "Beschreibung",
    "reusable": true,
    "share_with_main": true
  }},
  "improvement_for_next_cycle": "Konkrete Verbesserung",
  "recommended_focus_shift": "revenue|content|automation|product|mirror|stay",
  "confidence": 1-10,
  "message_to_main": "Nachricht ans Main-System"
}}"""


class MirrorCowork:
    """Autonomer Hintergrund-Agent mit Gemini."""

    def __init__(self, focus: str = "revenue"):
        self.client = GeminiClient()
        self.state = self._load_state()
        self.focus = focus

    def _load_state(self) -> Dict:
        if COWORK_STATE_FILE.exists():
            try:
                return json.loads(COWORK_STATE_FILE.read_text())
            except json.JSONDecodeError:
                pass
        default = {
            "created": datetime.now().isoformat(),
            "total_cycles": 0,
            "active_focus": "revenue",
            "actions_taken": [],
            "patterns_discovered": [],
            "pending_recommendations": [],
            "messages_for_main": [],
        }
        self._save_state(default)
        return default

    def _save_state(self, state: Dict = None):
        if state is None:
            state = self.state
        state["updated"] = datetime.now().isoformat()
        COWORK_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    # === Phase 1: OBSERVE ===

    def observe(self) -> Dict:
        """Scannt das Projekt und erfasst den Zustand."""
        logger.info("Phase 1: OBSERVE")

        observations = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(PROJECT_ROOT),
            "files": {},
            "system_health": {},
            "blockers": [],
        }

        # Scan-Ziele
        scan_targets = {
            "workflow_outputs": PROJECT_ROOT / "workflow-system" / "output",
            "mirror_outputs": OUTPUT_DIR,
            "swarm_outputs": PROJECT_ROOT / "kimi-swarm",
            "lead_machine": PROJECT_ROOT / "x-lead-machine",
            "gold_nuggets": PROJECT_ROOT / "gold-nuggets",
            "mirror_state": STATE_DIR,
            "mirror_memory": MEMORY_DIR,
        }

        for name, path in scan_targets.items():
            if path.exists():
                files = list(path.glob("*.json")) + list(path.glob("*.py"))
                recent = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[:3]
                observations["files"][name] = {
                    "count": len(files),
                    "recent": [f.name for f in recent],
                    "newest_age_hours": self._file_age_hours(recent[0]) if recent else 999,
                }
            else:
                observations["files"][name] = {"count": 0, "recent": [], "newest_age_hours": 999}

        # System Health
        main_state_file = PROJECT_ROOT / "workflow-system" / "state" / "current_state.json"
        if main_state_file.exists():
            try:
                main_state = json.loads(main_state_file.read_text())
                observations["system_health"]["main_cycle"] = main_state.get("cycle", 0)
                observations["system_health"]["main_steps"] = len(main_state.get("steps_completed", []))
                observations["system_health"]["main_patterns"] = len(main_state.get("patterns", []))
            except json.JSONDecodeError:
                observations["blockers"].append("Main-State nicht lesbar")

        mirror_state_file = STATE_DIR / "mirror_state.json"
        if mirror_state_file.exists():
            try:
                mirror_state = json.loads(mirror_state_file.read_text())
                observations["system_health"]["mirror_cycle"] = mirror_state.get("cycle", 0)
                observations["system_health"]["mirror_steps"] = len(mirror_state.get("steps_completed", []))
            except json.JSONDecodeError:
                observations["blockers"].append("Mirror-State nicht lesbar")

        # Blocker erkennen
        for name, info in observations["files"].items():
            if info.get("newest_age_hours", 999) > 24:
                observations["blockers"].append(f"Keine neuen Outputs in {name} seit >24h")

        if not os.getenv("GEMINI_API_KEY"):
            observations["blockers"].append("GEMINI_API_KEY nicht gesetzt!")

        logger.info(f"  Dateien gescannt: {sum(f['count'] for f in observations['files'].values())}")
        logger.info(f"  Blocker: {len(observations['blockers'])}")

        return observations

    # === Phase 2: PLAN ===

    async def plan(self, observations: Dict) -> Dict:
        """Plant die naechste Aktion."""
        logger.info("Phase 2: PLAN")

        focus_config = FOCUS_AREAS.get(self.focus, FOCUS_AREAS["revenue"])
        recent_actions = self.state.get("actions_taken", [])[-5:]
        vision_context = self._load_vision_context()

        # Main Status
        main_cowork_file = PROJECT_ROOT / "workflow-system" / "state" / "cowork_state.json"
        main_status = "{}"
        if main_cowork_file.exists():
            try:
                main_data = json.loads(main_cowork_file.read_text())
                main_status = json.dumps({
                    "focus": main_data.get("active_focus", "unknown"),
                    "cycles": main_data.get("total_cycles", 0),
                    "recent": main_data.get("actions_taken", [])[-3:],
                }, ensure_ascii=False)[:500]
            except json.JSONDecodeError as e:
                print(f"[mirror_cowork] Failed to parse main cowork state: {e}")

        prompt = PLAN_PROMPT.format(
            observations=json.dumps(observations, ensure_ascii=False)[:2000],
            focus=self.focus,
            focus_description=focus_config["description"],
            action_count=len(self.state.get("actions_taken", [])),
            recent_actions=json.dumps(recent_actions, ensure_ascii=False)[:1000],
            blockers="\n".join(f"- {b}" for b in observations.get("blockers", [])),
            vision_context=vision_context[:500],
            main_status=main_status,
        )

        routing = MODEL_ROUTING.get("cowork_plan", {"model": "pro", "temp": 0.7})
        result = await self.client.chat_json(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Plane die naechste Aktion (Fokus: {self.focus})"},
            ],
            model=routing["model"],
            temperature=routing["temp"],
        )

        plan = result.get("parsed", {})
        action = plan.get("priority_action", {})
        logger.info(f"  Geplant: {action.get('title', 'Unbekannt')}")
        logger.info(f"  Aufwand: ~{action.get('effort_minutes', '?')} Min")

        return plan

    # === Phase 3: ACT ===

    async def act(self, plan: Dict, observations: Dict) -> Dict:
        """Fuehrt die geplante Aktion aus."""
        logger.info("Phase 3: ACT")

        action = plan.get("priority_action", {})

        routing = MODEL_ROUTING.get("cowork_act", {"model": "flash", "temp": 0.6})
        result = await self.client.chat_json(
            messages=[
                {"role": "system", "content": ACT_PROMPT.format(
                    action=json.dumps(action, ensure_ascii=False),
                    context=json.dumps({
                        "focus": self.focus,
                        "observations_summary": plan.get("situation_assessment", ""),
                        "vision": self._load_vision_context()[:300],
                    }, ensure_ascii=False),
                )},
                {"role": "user", "content": "Fuehre die Aktion aus und erstelle das Deliverable."},
            ],
            model=routing["model"],
            temperature=routing["temp"],
            max_tokens=6000,
        )

        action_result = result.get("parsed", {})

        # Dateien erstellen (wenn angegeben)
        files_created = []
        for file_spec in action_result.get("files_to_create", []):
            file_path = file_spec.get("path", "")
            content = file_spec.get("content", "")
            if file_path and content:
                full_path = OUTPUT_DIR / "deliverables" / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                files_created.append(str(full_path))
                logger.info(f"  Datei erstellt: {full_path}")

        action_result["files_actually_created"] = files_created

        # Action-Output speichern
        act_file = OUTPUT_DIR / f"cowork_act_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        act_file.write_text(json.dumps(action_result, indent=2, ensure_ascii=False))

        logger.info(f"  Deliverable: {action_result.get('deliverable_type', '?')}")
        logger.info(f"  Qualitaet: {action_result.get('quality_score', '?')}/10")

        return action_result

    # === Phase 4: REFLECT ===

    async def reflect(
        self,
        observations: Dict,
        plan: Dict,
        action_result: Dict,
    ) -> Dict:
        """Reflektiert ueber den Zyklus."""
        logger.info("Phase 4: REFLECT")

        routing = MODEL_ROUTING.get("cowork_reflect", {"model": "thinking", "temp": 0.5})
        result = await self.client.chat_json(
            messages=[
                {"role": "system", "content": REFLECT_PROMPT.format(
                    observations=json.dumps(observations, ensure_ascii=False)[:1000],
                    plan=json.dumps(plan.get("priority_action", {}), ensure_ascii=False)[:500],
                    action_result=json.dumps(action_result, ensure_ascii=False)[:1500],
                    patterns=json.dumps(self.state.get("patterns_discovered", [])[-5:], ensure_ascii=False)[:500],
                )},
                {"role": "user", "content": "Reflektiere ehrlich ueber diesen Zyklus."},
            ],
            model=routing["model"],
            temperature=routing["temp"],
        )

        reflection = result.get("parsed", {})

        # Pattern speichern
        pattern = reflection.get("pattern_discovered")
        if pattern and isinstance(pattern, dict) and pattern.get("name"):
            self.state["patterns_discovered"].append(pattern)
            logger.info(f"  Neues Pattern: {pattern['name']}")

        # Message fuer Main speichern
        msg = reflection.get("message_to_main")
        if msg:
            self.state["messages_for_main"].append({
                "timestamp": datetime.now().isoformat(),
                "message": msg,
                "cycle": self.state.get("total_cycles", 0),
            })

        # Fokus-Shift pruefen
        recommended_shift = reflection.get("recommended_focus_shift", "stay")
        if recommended_shift != "stay" and recommended_shift in FOCUS_AREAS:
            logger.info(f"  Fokus-Shift empfohlen: {self.focus} → {recommended_shift}")
            self.state["active_focus"] = recommended_shift
            self.focus = recommended_shift

        logger.info(f"  Score: {reflection.get('cycle_score', '?')}/10")
        logger.info(f"  Confidence: {reflection.get('confidence', '?')}/10")

        return reflection

    # === Full Cycle ===

    async def run_cycle(self) -> Dict:
        """Fuehrt einen kompletten Observe-Plan-Act-Reflect Zyklus aus."""
        logger.info("╔══════════════════════════════════════════╗")
        logger.info("║   MIRROR COWORK - AUTONOMER ZYKLUS       ║")
        logger.info(f"║   Fokus: {self.focus:<33}║")
        logger.info("╚══════════════════════════════════════════╝")

        # Phase 1: OBSERVE
        observations = self.observe()

        # Phase 2: PLAN
        plan = await self.plan(observations)

        # Phase 3: ACT
        action_result = await self.act(plan, observations)

        # Phase 4: REFLECT
        reflection = await self.reflect(observations, plan, action_result)

        # State aktualisieren
        self.state["total_cycles"] = self.state.get("total_cycles", 0) + 1
        self.state["actions_taken"].append({
            "cycle": self.state["total_cycles"],
            "timestamp": datetime.now().isoformat(),
            "action": plan.get("priority_action", {}).get("title", "Unknown"),
            "score": reflection.get("cycle_score", 0),
            "focus": self.focus,
        })
        self.state["actions_taken"] = self.state["actions_taken"][-50:]
        self._save_state()

        stats = self.client.get_cost_stats()
        logger.info(f"\n=== ZYKLUS {self.state['total_cycles']} ABGESCHLOSSEN ===")
        logger.info(f"Kosten: ${stats['today_cost_usd']:.4f}")

        return {
            "cycle": self.state["total_cycles"],
            "observations": observations,
            "plan": plan,
            "action": action_result,
            "reflection": reflection,
            "cost": stats,
        }

    # === Helpers ===

    def _load_vision_context(self) -> str:
        if VISION_MEMORY_FILE.exists():
            try:
                data = json.loads(VISION_MEMORY_FILE.read_text())
                summary = data.get("summary", {})
                if summary:
                    return json.dumps(summary, ensure_ascii=False)
            except json.JSONDecodeError as e:
                print(f"[mirror_cowork] Failed to parse vision memory file: {e}")
        return "Vision noch nicht erfasst."

    @staticmethod
    def _file_age_hours(path: Path) -> float:
        try:
            age_seconds = (datetime.now().timestamp() - path.stat().st_mtime)
            return round(age_seconds / 3600, 1)
        except OSError:
            return 999.0

    def show_status(self):
        """Zeigt Cowork-Status an."""
        print("\n╔══════════════════════════════════════════╗")
        print("║    MIRROR COWORK - STATUS                ║")
        print("╚══════════════════════════════════════════╝")
        print(f"  Zyklen:          {self.state.get('total_cycles', 0)}")
        print(f"  Aktiver Fokus:   {self.state.get('active_focus', 'revenue')}")
        print(f"  Aktionen:        {len(self.state.get('actions_taken', []))}")
        print(f"  Patterns:        {len(self.state.get('patterns_discovered', []))}")
        print(f"  Main-Messages:   {len(self.state.get('messages_for_main', []))}")

        recent = self.state.get("actions_taken", [])[-5:]
        if recent:
            print("\n  Letzte Aktionen:")
            for a in recent:
                print(f"    [{a.get('score', '?')}/10] {a.get('action', '?')[:60]} ({a.get('focus', '?')})")
        print()


# === Daemon ===

async def run_daemon(interval: int = 1800, focus: Optional[str] = None):
    """Daemon-Modus: Laeuft automatisch alle N Sekunden."""
    cowork = MirrorCowork(focus=focus or "revenue")
    logger.info(f"Daemon gestartet (Intervall: {interval}s, Fokus: {cowork.focus})")

    try:
        while True:
            try:
                await cowork.run_cycle()
            except Exception as e:
                logger.error(f"Zyklus-Fehler: {e}")
            logger.info(f"Naechster Zyklus in {interval}s...")
            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Daemon gestoppt.")


# === CLI ===

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mirror Cowork Agent")
    parser.add_argument("--daemon", action="store_true", help="Daemon-Modus")
    parser.add_argument("--interval", type=int, default=1800, help="Intervall in Sekunden")
    parser.add_argument("--focus", choices=list(FOCUS_AREAS.keys()), default="revenue")
    parser.add_argument("--status", action="store_true", help="Status anzeigen")
    args = parser.parse_args()

    if args.status:
        MirrorCowork(args.focus).show_status()
    elif args.daemon:
        asyncio.run(run_daemon(args.interval, args.focus))
    else:
        asyncio.run(MirrorCowork(args.focus).run_cycle())
