"""
Cross-System Evolution Protocol.

Both systems (Claude on Mac + Gemini in Cloud) evolve each other through:

1. Code Review Exchange - Each reviews the other's improvements
2. Strategy Challenge - Each challenges the other's strategies
3. Blind Spot Detection - Find what the other system missed
4. Capability Expansion - Teach each other new tricks
5. Performance Benchmark - Compare outputs, keep the best

The result: exponential improvement. 1+1 = 3.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from gemini_client import GeminiClient
from digital_memory import DigitalMemory
from mirror_sync import MirrorSyncEngine, SyncArtifact


STATE_DIR = Path(__file__).parent / "state"
EVOLUTION_LOG = STATE_DIR / "evolution_log.json"
BENCHMARK_LOG = STATE_DIR / "benchmark_log.json"


class EvolutionProtocol:
    """
    Cross-system evolution: both systems make each other stronger.
    """

    def __init__(
        self,
        gemini: GeminiClient,
        memory: DigitalMemory,
        sync: MirrorSyncEngine,
    ):
        self.gemini = gemini
        self.memory = memory
        self.sync = sync
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    async def run_daily_evolution(self) -> dict:
        """Run all daily evolution strategies."""
        results = {}

        # Run strategies concurrently
        tasks = [
            self._code_improvement_review(),
            self._strategy_challenge(),
            self._blind_spot_detection(),
        ]

        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        results["code_improvement"] = outcomes[0] if not isinstance(outcomes[0], Exception) else str(outcomes[0])
        results["strategy_challenge"] = outcomes[1] if not isinstance(outcomes[1], Exception) else str(outcomes[1])
        results["blind_spot"] = outcomes[2] if not isinstance(outcomes[2], Exception) else str(outcomes[2])

        # Log evolution
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "daily_evolution",
            "results": results,
        }
        self._append_log(EVOLUTION_LOG, entry)

        return results

    async def run_weekly_evolution(self) -> dict:
        """Run weekly deeper evolution strategies."""
        results = {}

        tasks = [
            self._capability_expansion(),
            self._performance_benchmark(),
            self._meta_evolution(),
        ]

        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        results["capability_expansion"] = outcomes[0] if not isinstance(outcomes[0], Exception) else str(outcomes[0])
        results["performance_benchmark"] = outcomes[1] if not isinstance(outcomes[1], Exception) else str(outcomes[1])
        results["meta_evolution"] = outcomes[2] if not isinstance(outcomes[2], Exception) else str(outcomes[2])

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "weekly_evolution",
            "results": results,
        }
        self._append_log(EVOLUTION_LOG, entry)

        return results

    # -- Daily Strategies --

    async def _code_improvement_review(self) -> dict:
        """Gemini reviews recent Claude improvements and suggests enhancements."""
        # Get recent sync artifacts that are code-related
        sync_status = self.sync.status()
        memory_export = self.memory.export_for_system("gemini")

        prompt = f"""Du bist der Evolution-Agent des AIEmpire Dual-Systems (Gemini-Seite).
Deine Aufgabe: Das Claude-System (auf Mac) verbessern.

Aktueller Systemstand:
- Sync Status: {json.dumps(sync_status, ensure_ascii=False)}
- Bekanntes Wissen: {json.dumps(memory_export.get('high_confidence_facts', [])[:10], ensure_ascii=False)[:2000]}

Analysiere das AIEmpire-Core System und schlage konkrete Code-Verbesserungen vor:

1. Welche Systeme koennten effizienter sein?
2. Welche fehlenden Integrationen wuerden den groessten Impact haben?
3. Welche Automatisierungen fehlen?
4. Welche Sicherheitsluecken oder Schwachstellen gibt es?
5. Welche Quick Wins koennten sofort umgesetzt werden?

Fokus auf REVENUE-IMPACT. Maurice will 100M EUR.

Antworte als JSON:
{{
  "improvements": [
    {{
      "area": "system_area",
      "current_state": "...",
      "improvement": "...",
      "revenue_impact": "low/medium/high",
      "effort": "low/medium/high",
      "priority": 1-10
    }}
  ],
  "quick_wins": ["..."],
  "critical_gaps": ["..."]
}}"""

        result = await self.gemini.chat_json(prompt, tier="pro")
        parsed = result.get("parsed") or {}

        # Push improvements as sync artifacts
        if parsed.get("improvements"):
            for imp in parsed["improvements"][:5]:  # Top 5
                self.sync.push_artifact(
                    artifact_type="improvement",
                    content=imp,
                    source="gemini",
                    priority=imp.get("priority", 5),
                )

        return parsed

    async def _strategy_challenge(self) -> dict:
        """Gemini challenges the current empire strategy."""
        vision = self.memory.get_vision_summary()

        prompt = f"""Du bist der Strategie-Challenger des AIEmpire Systems.
Deine Rolle: Die aktuelle Strategie KRITISCH hinterfragen.
Nicht zustimmen, sondern HERAUSFORDERN.

Aktuelles Wissen ueber Maurice und sein Empire:
{json.dumps(vision, indent=2, ensure_ascii=False)[:4000]}

Bekannte Fakten:
- Maurice: 37, Elektrotechnikmeister, 16 Jahre BMA
- Ziel: 100M EUR in 1-3 Jahren
- Aktueller Revenue: 0 EUR
- System: Claude + Gemini + Kimi + Ollama
- Revenue Channels: Gumroad, Fiverr, Consulting, X/Twitter

CHALLENGE:
1. Ist das 100M Ziel realistisch in 1-3 Jahren? Was muesste passieren?
2. Was sind die 3 groessten strategischen Fehler gerade?
3. Welche Annahmen sind wahrscheinlich falsch?
4. Was wuerde ein Konkurrent mit gleichen Ressourcen anders machen?
5. Was ist der schnellste Weg von 0 auf ersten Revenue?
6. Welche Ablenkungen muessen eliminiert werden?

Sei EHRLICH und DIREKT. Kein Sugarcoating.

Antworte als JSON:
{{
  "reality_check": "...",
  "strategic_errors": ["..."],
  "false_assumptions": ["..."],
  "competitor_perspective": "...",
  "fastest_to_revenue": "...",
  "distractions_to_kill": ["..."],
  "recommended_pivot": "...",
  "confidence_in_strategy": 0.0-1.0
}}"""

        result = await self.gemini.chat_json(prompt, tier="pro")
        parsed = result.get("parsed") or {}

        # Push challenge as sync artifact
        if parsed:
            self.sync.push_artifact(
                artifact_type="insight",
                content={"type": "strategy_challenge", "challenge": parsed},
                source="gemini",
                priority=8,
            )

        return parsed

    async def _blind_spot_detection(self) -> dict:
        """Find what both systems might be missing."""
        gaps = self.memory.get_gaps()
        vision = self.memory.get_vision_summary()

        prompt = f"""Du bist der Blind-Spot-Detektor des AIEmpire Systems.
Deine Aufgabe: Finde was BEIDE Systeme (Claude + Gemini) uebersehen.

Bekannte Wissensluecken:
{json.dumps(gaps, ensure_ascii=False)}

Aktuelles Wissen:
{json.dumps(vision, indent=2, ensure_ascii=False)[:3000]}

Suche nach:
1. UNGESTELLTE FRAGEN - Was hat noch niemand gefragt?
2. VERGESSENE BEREICHE - Welche Lebensbereiche werden ignoriert?
3. VERSTECKTE RISIKEN - Was koennte das ganze Projekt gefaehrden?
4. MARKT-BLINDHEIT - Was passiert im Markt das wir nicht sehen?
5. PERSOENLICHE BLINDHEIT - Was ueber Maurice wissen wir nicht?
6. TECHNISCHE BLINDHEIT - Welche Tech-Trends werden verpasst?

Antworte als JSON:
{{
  "unasked_questions": ["..."],
  "forgotten_areas": ["..."],
  "hidden_risks": ["..."],
  "market_blind_spots": ["..."],
  "personal_blind_spots": ["..."],
  "tech_blind_spots": ["..."],
  "most_critical_blind_spot": "...",
  "recommended_action": "..."
}}"""

        result = await self.gemini.chat_json(prompt, tier="flash")
        parsed = result.get("parsed") or {}

        if parsed:
            self.sync.push_artifact(
                artifact_type="insight",
                content={"type": "blind_spot_detection", "findings": parsed},
                source="gemini",
                priority=7,
            )

        return parsed

    # -- Weekly Strategies --

    async def _capability_expansion(self) -> dict:
        """Identify new capabilities each system should develop."""
        prompt = f"""Du bist der Capability-Expansion Agent.
Analysiere welche NEUEN Faehigkeiten das AIEmpire System entwickeln sollte.

Aktuelle Faehigkeiten:
- Workflow Orchestration (5-Step Compound Loop)
- Kimi Swarm (100K-500K Agents)
- X/Twitter Lead Machine
- CRM mit BANT Scoring
- Atomic Reactor Task Engine
- Brain System (8 spezialisierte Gehirne)
- Gemini Mirror (Dual-System Evolution)
- Digital Memory (Persistentes Wissen)

Maurice's Ziel: 100M EUR in 1-3 Jahren.

Welche NEUEN Capabilities wuerden den groessten Impact haben?
Denke an:
- Revenue-generierende Faehigkeiten
- Markt-Intelligence
- Automatische Kundengewinnung
- Selbst-Optimierung
- Neue Revenue Streams
- Skalierung

Antworte als JSON:
{{
  "new_capabilities": [
    {{
      "name": "...",
      "description": "...",
      "revenue_impact": "...",
      "implementation_complexity": "low/medium/high",
      "priority": 1-10,
      "which_system": "claude/gemini/both"
    }}
  ],
  "synergy_opportunities": ["..."],
  "moonshot_ideas": ["..."]
}}"""

        result = await self.gemini.chat_json(prompt, tier="pro")
        return result.get("parsed") or {}

    async def _performance_benchmark(self) -> dict:
        """Compare and benchmark both systems' outputs."""
        evolution_log = self._read_log(EVOLUTION_LOG)
        recent = evolution_log[-7:] if len(evolution_log) >= 7 else evolution_log

        prompt = f"""Analysiere die Performance beider Systeme (Claude + Gemini) der letzten Woche.

Evolution Log (letzte Eintraege):
{json.dumps(recent, indent=2, ensure_ascii=False)[:4000]}

Bewerte:
1. Welches System hat mehr wertvolle Insights produziert?
2. Welches System war kreativer?
3. Welches System war praxisnaher?
4. Wo ergaenzen sie sich am besten?
5. Wo gibt es Redundanz die eliminiert werden sollte?

Antworte als JSON:
{{
  "claude_strengths": ["..."],
  "gemini_strengths": ["..."],
  "best_synergies": ["..."],
  "redundancies": ["..."],
  "optimization_suggestions": ["..."],
  "overall_effectiveness": 0.0-1.0
}}"""

        result = await self.gemini.chat_json(prompt, tier="flash")
        parsed = result.get("parsed") or {}

        if parsed:
            self._append_log(BENCHMARK_LOG, {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "benchmark": parsed,
            })

        return parsed

    async def _meta_evolution(self) -> dict:
        """Evolve the evolution process itself."""
        evolution_log = self._read_log(EVOLUTION_LOG)

        prompt = f"""META-EVOLUTION: Verbessere den Evolutionsprozess selbst.

Bisherige Evolution-Ergebnisse:
{json.dumps(evolution_log[-5:], indent=2, ensure_ascii=False)[:3000]}

Analysiere:
1. Welche Evolution-Strategien bringen am meisten?
2. Welche sind Zeitverschwendung?
3. Welche NEUEN Strategien sollten hinzugefuegt werden?
4. Wie kann die Feedback-Schleife beschleunigt werden?
5. Was muss sich aendern damit die Evolution 10x effektiver wird?

Antworte als JSON:
{{
  "effective_strategies": ["..."],
  "ineffective_strategies": ["..."],
  "new_strategies": [
    {{"name": "...", "description": "...", "expected_impact": "..."}}
  ],
  "process_improvements": ["..."],
  "meta_insight": "Die wichtigste Erkenntnis ueber den Evolutionsprozess"
}}"""

        result = await self.gemini.chat_json(prompt, tier="flash")
        return result.get("parsed") or {}

    # -- Utility --

    def status(self) -> dict:
        """Get evolution status."""
        evo_log = self._read_log(EVOLUTION_LOG)
        bench_log = self._read_log(BENCHMARK_LOG)

        return {
            "total_evolutions": len(evo_log),
            "total_benchmarks": len(bench_log),
            "last_evolution": evo_log[-1]["timestamp"] if evo_log else "never",
            "last_benchmark": bench_log[-1]["timestamp"] if bench_log else "never",
        }

    def _read_log(self, path: Path) -> list:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _append_log(self, path: Path, entry: dict):
        log = self._read_log(path)
        log.append(entry)
        # Keep last 500 entries
        if len(log) > 500:
            log = log[-500:]
        path.write_text(json.dumps(log, indent=2, ensure_ascii=False))
