"""
Dual Brain - Gegenseitige Verstaerkungs-Schleife

Architektur:
  Main Brain (Mac/Kimi)  <--Amplification Loop-->  Mirror Brain (Gemini)

Beide Systeme:
1. Teilen ihre besten Insights
2. Challengen gegenseitig ihre Ergebnisse
3. Generieren Cross-Improvements
4. Fuehren kompetitive Analysen durch
5. Entdecken Muster die einzeln unsichtbar waeren
6. Verdoppeln ihre Effektivitaet durch Zusammenarbeit

Der Amplification Loop:
  Main produziert → Mirror reviewed + verbessert →
  Mirror produziert → Main reviewed + verbessert →
  Beide lernen → Patterns werden geteilt → Repeat
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

MIRROR_DIR = Path(__file__).parent
sys.path.insert(0, str(MIRROR_DIR))

from config import (
    DUAL_BRAIN_STATE_FILE,
    DUAL_BRAIN_CONFIG,
    PROJECT_ROOT,
    STATE_DIR,
    OUTPUT_DIR,
)
from gemini_client import GeminiClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DUAL-BRAIN] %(levelname)s %(message)s",
)
logger = logging.getLogger("dual-brain")


# === Prompts ===

REVIEW_PROMPT = """Du bist das Gemini-Gehirn im AIEmpire Dual-Brain System.
Du reviewst Ergebnisse des Main-Systems (Kimi/Ollama-basiert).

DEINE ROLLE: Kritischer Partner, nicht Ja-Sager.
- Finde Schwaechen und blinde Flecken
- Schlage Verbesserungen vor
- Identifiziere verpasste Chancen
- Bewerte Qualitaet objektiv

MAIN-SYSTEM ERGEBNIS:
{main_result}

KONTEXT:
Vision: {vision_context}
Zyklus: {cycle}
Bisherige Cross-Insights: {cross_insights}

Antworte NUR als JSON:
{{
  "review_score": 1-10,
  "strengths": ["Was gut ist"],
  "weaknesses": ["Was schwach ist"],
  "blind_spots": ["Was uebersehen wurde"],
  "improvements": [
    {{
      "area": "Bereich",
      "current": "Aktueller Zustand",
      "suggested": "Verbesserungsvorschlag",
      "impact": "high/medium/low",
      "effort": "minutes_estimated"
    }}
  ],
  "missed_opportunities": ["Verpasste Chancen"],
  "competitive_edge": "Was wuerde Mirror anders/besser machen",
  "synthesis": "Kombinierte Staerke beider Systeme",
  "next_action": "Konkrete naechste Aktion"
}}"""


AMPLIFY_PROMPT = """Du bist das Gemini-Verstaerkungs-Gehirn im AIEmpire System.
Du nimmst Erkenntnisse von BEIDEN Systemen und multiplizierst ihren Wert.

MAIN INSIGHTS:
{main_insights}

MIRROR INSIGHTS:
{mirror_insights}

CROSS-PATTERNS (bisherige):
{cross_patterns}

VISION:
{vision_context}

Deine Aufgabe: VERDOPPLE den Wert durch Kombination.
1. Finde Synergien die einzeln unsichtbar sind
2. Generiere neue Insights aus der Kombination
3. Identifiziere Hebelpunkte wo kleine Aenderungen grossen Impact haben
4. Schlage konkrete Aktionen vor die BEIDE Systeme staerker machen

Antworte NUR als JSON:
{{
  "amplified_insights": [
    {{
      "insight": "Beschreibung",
      "derived_from": "main|mirror|synthesis",
      "impact_multiplier": "2x-10x Beschreibung",
      "action": "Konkrete Aktion",
      "assignee": "main|mirror|both"
    }}
  ],
  "synergy_score": 1-10,
  "new_patterns": [
    {{
      "name": "Muster-Name",
      "description": "Beschreibung",
      "applies_to": "main|mirror|both"
    }}
  ],
  "leverage_points": [
    {{
      "point": "Hebelpunkt",
      "small_change": "Was sich aendert",
      "big_impact": "Was das bewirkt"
    }}
  ],
  "system_upgrade_suggestions": {{
    "main": ["Verbesserung fuer Main"],
    "mirror": ["Verbesserung fuer Mirror"],
    "shared": ["Verbesserung fuer beide"]
  }},
  "next_amplification_focus": "Worauf beim naechsten Mal fokussieren"
}}"""


COMPETITIVE_PROMPT = """Du bist der Wettbewerbs-Analyst im AIEmpire Dual-Brain System.
Vergleiche die Performance beider Gehirne objektiv.

MAIN BRAIN (Kimi/Ollama):
Zyklen: {main_cycles}
Patterns gefunden: {main_patterns_count}
Letzte Aktionen: {main_actions}

MIRROR BRAIN (Gemini):
Zyklen: {mirror_cycles}
Patterns gefunden: {mirror_patterns_count}
Letzte Aktionen: {mirror_actions}

Bewerte OBJEKTIV:
1. Welches System liefert bessere Insights?
2. Welches ist schneller?
3. Welches kosteneffizienter?
4. Wo ergaenzen sie sich perfekt?

Antworte NUR als JSON:
{{
  "comparison": {{
    "insight_quality": {{"winner": "main|mirror|tie", "score_main": 1-10, "score_mirror": 1-10, "reason": "..."}},
    "speed": {{"winner": "main|mirror|tie", "reason": "..."}},
    "cost_efficiency": {{"winner": "main|mirror|tie", "reason": "..."}},
    "creativity": {{"winner": "main|mirror|tie", "reason": "..."}},
    "reliability": {{"winner": "main|mirror|tie", "reason": "..."}}
  }},
  "complementary_areas": ["Wo sie sich ergaenzen"],
  "recommended_task_distribution": {{
    "main_should_handle": ["Tasks fuer Main"],
    "mirror_should_handle": ["Tasks fuer Mirror"],
    "both_together": ["Tasks fuer beide"]
  }},
  "overall_synergy_score": 1-10,
  "optimization_suggestions": ["Wie beide besser werden"]
}}"""


class DualBrain:
    """Verstaerkungs-Schleife zwischen Main und Mirror System."""

    def __init__(self):
        self.client = GeminiClient()
        self.state = self._load_state()
        self.config = DUAL_BRAIN_CONFIG

    def _load_state(self) -> Dict:
        if DUAL_BRAIN_STATE_FILE.exists():
            try:
                return json.loads(DUAL_BRAIN_STATE_FILE.read_text())
            except json.JSONDecodeError:
                pass
        default = {
            "created": datetime.now().isoformat(),
            "total_cycles": 0,
            "reviews_done": 0,
            "amplifications": 0,
            "competitive_analyses": 0,
            "cross_insights": [],
            "improvement_queue": [],
            "synergy_history": [],
        }
        self._save_state(default)
        return default

    def _save_state(self, state: Dict = None):
        if state is None:
            state = self.state
        state["updated"] = datetime.now().isoformat()
        DUAL_BRAIN_STATE_FILE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False)
        )

    # === Core: Review Loop ===

    async def review_main_output(self) -> Dict:
        """Mirror reviewed die neuesten Main-System Ergebnisse."""
        logger.info("=== REVIEW: Main-System Output ===")

        # Main-Output laden
        main_output_dir = PROJECT_ROOT / "workflow_system" / "output"
        main_result = self._load_latest_output(main_output_dir)

        if not main_result:
            logger.info("Kein Main-Output zum Reviewen")
            return {"status": "no_output"}

        # Vision-Kontext laden
        vision_context = self._load_vision_context()
        cross_insights = self.state.get("cross_insights", [])[-10:]

        prompt = REVIEW_PROMPT.format(
            main_result=json.dumps(main_result, ensure_ascii=False)[:3000],
            vision_context=vision_context[:500],
            cycle=self.state.get("total_cycles", 0),
            cross_insights=json.dumps(cross_insights, ensure_ascii=False)[:1000],
        )

        result = await self.client.chat_json(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Fuehre ein gruendliches Review durch."},
            ],
            model="pro",
            temperature=0.6,
        )

        review = result.get("parsed", {})

        # Improvements zur Queue hinzufuegen
        improvements = review.get("improvements", [])
        for imp in improvements:
            imp["source"] = "mirror_review"
            imp["timestamp"] = datetime.now().isoformat()
            self.state["improvement_queue"].append(imp)

        self.state["reviews_done"] = self.state.get("reviews_done", 0) + 1
        self._save_state()

        # Review-Ergebnis speichern
        review_file = OUTPUT_DIR / f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        review_file.write_text(json.dumps(review, indent=2, ensure_ascii=False))

        logger.info(f"✓ Review Score: {review.get('review_score', '?')}/10")
        logger.info(f"  Staerken: {len(review.get('strengths', []))}")
        logger.info(f"  Schwaechen: {len(review.get('weaknesses', []))}")
        logger.info(f"  Improvements: {len(improvements)}")

        return review

    # === Core: Amplification Loop ===

    async def amplify(self) -> Dict:
        """Verstaerkt Insights beider Systeme."""
        logger.info("=== AMPLIFICATION LOOP ===")

        main_insights = self._gather_main_insights()
        mirror_insights = self._gather_mirror_insights()
        cross_patterns = self._load_cross_patterns()
        vision_context = self._load_vision_context()

        prompt = AMPLIFY_PROMPT.format(
            main_insights=json.dumps(main_insights, ensure_ascii=False)[:2000],
            mirror_insights=json.dumps(mirror_insights, ensure_ascii=False)[:2000],
            cross_patterns=json.dumps(cross_patterns, ensure_ascii=False)[:1000],
            vision_context=vision_context[:500],
        )

        result = await self.client.chat_json(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Verstaerke und kombiniere alle Insights."},
            ],
            model="pro",
            temperature=0.7,
        )

        amplified = result.get("parsed", {})

        # Cross-Insights speichern
        new_insights = amplified.get("amplified_insights", [])
        for insight in new_insights:
            insight["amplification_cycle"] = self.state.get("amplifications", 0) + 1
            insight["timestamp"] = datetime.now().isoformat()
        self.state["cross_insights"].extend(new_insights)
        self.state["cross_insights"] = self.state["cross_insights"][-100:]

        # Neue Patterns speichern
        new_patterns = amplified.get("new_patterns", [])
        self._save_cross_patterns(new_patterns)

        # Synergy Score tracken
        synergy_score = amplified.get("synergy_score", 5)
        self.state["synergy_history"].append({
            "timestamp": datetime.now().isoformat(),
            "score": synergy_score,
            "insights_generated": len(new_insights),
            "patterns_found": len(new_patterns),
        })
        self.state["synergy_history"] = self.state["synergy_history"][-50:]

        self.state["amplifications"] = self.state.get("amplifications", 0) + 1
        self._save_state()

        # Output speichern
        amp_file = OUTPUT_DIR / f"amplification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        amp_file.write_text(json.dumps(amplified, indent=2, ensure_ascii=False))

        logger.info(f"✓ Synergy Score: {synergy_score}/10")
        logger.info(f"  Neue Insights: {len(new_insights)}")
        logger.info(f"  Neue Patterns: {len(new_patterns)}")
        logger.info(f"  Leverage Points: {len(amplified.get('leverage_points', []))}")

        return amplified

    # === Core: Competitive Analysis ===

    async def competitive_analysis(self) -> Dict:
        """Vergleicht Main vs Mirror Performance."""
        logger.info("=== COMPETITIVE ANALYSIS ===")

        # Main Stats
        main_state = self._load_main_state()
        main_cowork = self._load_main_cowork()

        # Mirror Stats
        mirror_state_file = STATE_DIR / "mirror_state.json"
        mirror_state = {}
        if mirror_state_file.exists():
            try:
                mirror_state = json.loads(mirror_state_file.read_text())
            except json.JSONDecodeError:
                pass

        prompt = COMPETITIVE_PROMPT.format(
            main_cycles=main_state.get("cycle", 0),
            main_patterns_count=len(main_state.get("patterns", [])),
            main_actions=json.dumps(main_cowork.get("actions_taken", [])[-5:], ensure_ascii=False)[:1000],
            mirror_cycles=mirror_state.get("cycle", 0),
            mirror_patterns_count=len(mirror_state.get("patterns", [])),
            mirror_actions=json.dumps(self.state.get("cross_insights", [])[-5:], ensure_ascii=False)[:1000],
        )

        result = await self.client.chat_json(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Fuehre eine objektive Wettbewerbsanalyse durch."},
            ],
            model="pro",
            temperature=0.4,
        )

        analysis = result.get("parsed", {})
        self.state["competitive_analyses"] = self.state.get("competitive_analyses", 0) + 1
        self._save_state()

        # Output
        comp_file = OUTPUT_DIR / f"competitive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        comp_file.write_text(json.dumps(analysis, indent=2, ensure_ascii=False))

        logger.info(f"✓ Synergy Score: {analysis.get('overall_synergy_score', '?')}/10")

        return analysis

    # === Full Dual-Brain Cycle ===

    async def full_cycle(self) -> Dict:
        """Fuehrt einen kompletten Dual-Brain Zyklus durch."""
        logger.info("╔══════════════════════════════════════════╗")
        logger.info("║    DUAL-BRAIN AMPLIFICATION CYCLE        ║")
        logger.info("╚══════════════════════════════════════════╝")

        results = {
            "timestamp": datetime.now().isoformat(),
            "cycle": self.state.get("total_cycles", 0) + 1,
        }

        # Phase 1: Review Main Output
        results["review"] = await self.review_main_output()

        # Phase 2: Amplification
        results["amplification"] = await self.amplify()

        # Phase 3: Competitive Analysis (alle 5 Zyklen)
        if results["cycle"] % 5 == 0 or results["cycle"] == 1:
            results["competitive"] = await self.competitive_analysis()

        self.state["total_cycles"] = results["cycle"]
        self._save_state()

        # Kosten-Report
        stats = self.client.get_cost_stats()
        results["cost"] = stats

        logger.info(f"\n=== DUAL-BRAIN ZYKLUS {results['cycle']} ABGESCHLOSSEN ===")
        logger.info(f"Kosten: ${stats['today_cost_usd']:.4f}")

        return results

    # === Data Loading Helpers ===

    def _load_latest_output(self, output_dir: Path) -> Optional[Dict]:
        """Laedt den neuesten Output aus einem Verzeichnis."""
        if not output_dir.exists():
            return None
        files = sorted(output_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not files:
            return None
        try:
            return json.loads(files[0].read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def _load_main_state(self) -> Dict:
        main_file = PROJECT_ROOT / "workflow_system" / "state" / "current_state.json"
        if main_file.exists():
            try:
                return json.loads(main_file.read_text())
            except json.JSONDecodeError:
                pass
        return {}

    def _load_main_cowork(self) -> Dict:
        cowork_file = PROJECT_ROOT / "workflow_system" / "state" / "cowork_state.json"
        if cowork_file.exists():
            try:
                return json.loads(cowork_file.read_text())
            except json.JSONDecodeError:
                pass
        return {}

    def _load_vision_context(self) -> str:
        from config import VISION_MEMORY_FILE
        if VISION_MEMORY_FILE.exists():
            try:
                data = json.loads(VISION_MEMORY_FILE.read_text())
                summary = data.get("summary", {})
                if summary:
                    return json.dumps(summary, ensure_ascii=False)
                entries = data.get("entries", [])[-5:]
                return json.dumps(entries, ensure_ascii=False)
            except json.JSONDecodeError:
                pass
        return "Vision noch nicht erfasst - Vision Interrogator starten!"

    def _gather_main_insights(self) -> List[Dict]:
        """Sammelt Insights vom Main-System."""
        insights = []
        main_output_dir = PROJECT_ROOT / "workflow_system" / "output"
        if main_output_dir.exists():
            for f in sorted(main_output_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                try:
                    data = json.loads(f.read_text())
                    insights.append({
                        "source": "main",
                        "step": data.get("step", f.stem),
                        "data": json.dumps(data)[:500],
                    })
                except (json.JSONDecodeError, OSError):
                    continue
        return insights

    def _gather_mirror_insights(self) -> List[Dict]:
        """Sammelt Insights vom Mirror-System."""
        insights = []
        for f in sorted(OUTPUT_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
            try:
                data = json.loads(f.read_text())
                insights.append({
                    "source": "mirror",
                    "step": data.get("step", f.stem),
                    "data": json.dumps(data)[:500],
                })
            except (json.JSONDecodeError, OSError):
                continue
        return insights

    def _load_cross_patterns(self) -> List[Dict]:
        from config import PATTERN_CROSS_FILE
        if PATTERN_CROSS_FILE.exists():
            try:
                data = json.loads(PATTERN_CROSS_FILE.read_text())
                if isinstance(data, list):
                    return data
                return data.get("patterns", [])
            except json.JSONDecodeError:
                pass
        return []

    def _save_cross_patterns(self, new_patterns: List[Dict]):
        from config import PATTERN_CROSS_FILE
        existing = self._load_cross_patterns()
        existing_names = {p.get("name", "") for p in existing}
        for p in new_patterns:
            if p.get("name", "") not in existing_names:
                p["discovered"] = datetime.now().isoformat()
                existing.append(p)
        PATTERN_CROSS_FILE.write_text(
            json.dumps(existing[-200:], indent=2, ensure_ascii=False)
        )

    # === Status ===

    def show_status(self):
        """Zeigt Dual-Brain Status an."""
        print("\n╔══════════════════════════════════════════╗")
        print("║       DUAL-BRAIN - STATUS                ║")
        print("╚══════════════════════════════════════════╝")
        print(f"  Zyklen:                {self.state.get('total_cycles', 0)}")
        print(f"  Reviews:               {self.state.get('reviews_done', 0)}")
        print(f"  Amplifications:        {self.state.get('amplifications', 0)}")
        print(f"  Competitive Analyses:  {self.state.get('competitive_analyses', 0)}")
        print(f"  Cross-Insights:        {len(self.state.get('cross_insights', []))}")
        print(f"  Improvement Queue:     {len(self.state.get('improvement_queue', []))}")

        history = self.state.get("synergy_history", [])
        if history:
            avg_synergy = sum(h["score"] for h in history[-10:]) / min(len(history), 10)
            print(f"  Avg Synergy (last 10): {avg_synergy:.1f}/10")

        print()


# === Daemon ===

async def run_dual_brain_daemon(interval: int = None):
    """Dual-Brain Daemon der regelmaessig Amplification-Zyklen faehrt."""
    if interval is None:
        interval = DUAL_BRAIN_CONFIG["amplification_interval"]

    brain = DualBrain()
    logger.info(f"Dual-Brain Daemon gestartet (Intervall: {interval}s)")

    try:
        while True:
            try:
                await brain.full_cycle()
            except Exception as e:
                logger.error(f"Cycle-Fehler: {e}")
            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Dual-Brain Daemon gestoppt.")


# === CLI ===

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dual Brain Amplification")
    parser.add_argument("--cycle", action="store_true", help="Voller Zyklus")
    parser.add_argument("--review", action="store_true", help="Main-Output reviewen")
    parser.add_argument("--amplify", action="store_true", help="Insights verstaerken")
    parser.add_argument("--compete", action="store_true", help="Competitive Analysis")
    parser.add_argument("--daemon", action="store_true", help="Daemon-Modus")
    parser.add_argument("--interval", type=int, default=3600, help="Intervall in Sekunden")
    parser.add_argument("--status", action="store_true", help="Status anzeigen")
    args = parser.parse_args()

    brain = DualBrain()

    if args.status:
        brain.show_status()
    elif args.daemon:
        asyncio.run(run_dual_brain_daemon(args.interval))
    elif args.review:
        asyncio.run(brain.review_main_output())
    elif args.amplify:
        asyncio.run(brain.amplify())
    elif args.compete:
        asyncio.run(brain.competitive_analysis())
    else:
        asyncio.run(brain.full_cycle())
