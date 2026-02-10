"""
Mirror Orchestrator - 5-Step Compound Loop auf Gemini
Spiegelt workflow-system/orchestrator.py aber nutzt Gemini statt Kimi.

Schritte:
1. AUDIT    - System-Zustand pruefen, Prioritaeten bewerten
2. ARCHITECT - Loesungsansaetze entwerfen
3. ANALYST  - Engineering-Review und Risiken
4. REFINERY - Konvergenz-Schleife (iterative Verbesserung)
5. COMPOUNDER - Muster extrahieren, naechsten Zyklus planen

Der Mirror-Orchestrator laeuft PARALLEL zum Main-Orchestrator.
Ergebnisse werden ueber den SyncEngine ausgetauscht.
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Pfad-Setup
MIRROR_DIR = Path(__file__).parent
sys.path.insert(0, str(MIRROR_DIR))

from config import (
    MIRROR_STATE_FILE,
    MODEL_ROUTING,
    OUTPUT_DIR,
    HISTORY_DIR,
    STATE_DIR,
    PROJECT_ROOT,
)
from gemini_client import GeminiClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MIRROR-ORCH] %(levelname)s %(message)s",
)
logger = logging.getLogger("mirror-orchestrator")

# === System Prompts (Deutsch, wie im Hauptsystem) ===

STEP_PROMPTS = {
    "audit": {
        "system": """Du bist der AUDIT-Agent im AIEmpire Gemini-Spiegel-System.
Deine Aufgabe: Analysiere den aktuellen Zustand ALLER Systeme.

Bewerte jeden Bereich:
- Revenue-Status (Einnahmen, Pipeline, Blocker)
- Content-Pipeline (X/Twitter, Gumroad, Fiverr)
- Automation-Level (was laeuft automatisch, was manuell)
- System-Gesundheit (Services, Errors, Performance)
- Kimi-Swarm-Status (Jobs, Output-Qualitaet)
- Gemini-Mirror-Status (Sync, Dual-Brain)

Antworte NUR als JSON mit dieser Struktur:
{
  "timestamp": "ISO-Datum",
  "overall_score": 1-10,
  "areas": {
    "revenue": {"score": 1-10, "status": "text", "blockers": [], "opportunities": []},
    "content": {"score": 1-10, "status": "text", "blockers": [], "opportunities": []},
    "automation": {"score": 1-10, "status": "text", "blockers": [], "opportunities": []},
    "system_health": {"score": 1-10, "status": "text", "blockers": [], "opportunities": []},
    "swarm": {"score": 1-10, "status": "text", "blockers": [], "opportunities": []},
    "mirror": {"score": 1-10, "status": "text", "blockers": [], "opportunities": []}
  },
  "top_3_priorities": [{"title": "...", "impact": "high/medium/low", "effort": "hours"}],
  "energy_score": 1-10,
  "recommended_focus": "revenue|content|automation|product"
}""",
        "user_template": """SYSTEM-ZUSTAND ZUM AUDIT:
Zyklus: {cycle}
Vorherige Schritte: {prior_steps}
Main-System Patterns: {main_patterns}
Mirror Patterns: {mirror_patterns}
Letzte Ergebnisse: {last_results}
Vision-Kontext: {vision_context}

Fuehre jetzt einen gruendlichen Audit durch.""",
    },
    "architect": {
        "system": """Du bist der ARCHITECT-Agent im AIEmpire Gemini-Spiegel-System.
Basierend auf dem AUDIT entwirfst du konkrete Loesungsansaetze.

Fuer jede Prioritaet aus dem Audit:
- 2-3 Loesungsansaetze mit Vor/Nachteilen
- Konkreter Implementierungsplan
- Geschaetzte Setup-Zeit
- Benoetigte Ressourcen

Antworte NUR als JSON:
{
  "timestamp": "ISO-Datum",
  "solutions": [
    {
      "priority": "Titel aus Audit",
      "approaches": [
        {
          "name": "Ansatz-Name",
          "description": "Was genau gemacht wird",
          "pros": ["..."],
          "cons": ["..."],
          "setup_hours": 0,
          "implementation_steps": ["Schritt 1", "Schritt 2"],
          "resources_needed": ["..."],
          "expected_roi": "Beschreibung"
        }
      ],
      "recommended": "Name des besten Ansatzes",
      "why": "Begruendung"
    }
  ],
  "cross_system_synergies": ["Wie Main und Mirror zusammen staerker werden"],
  "quick_wins": [{"action": "...", "impact": "...", "effort_minutes": 0}]
}""",
        "user_template": """AUDIT-ERGEBNIS:
{audit_result}

KONTEXT:
Zyklus: {cycle}
Verfuegbare Systeme: Main (Kimi/Ollama), Mirror (Gemini), n8n, Atomic Reactor
Budget-Rahmen: Minimal (Ollama first, dann guenstige APIs)
Vision: {vision_context}

Entwirf jetzt konkrete Loesungen fuer die Top-Prioritaeten.""",
    },
    "analyst": {
        "system": """Du bist der ANALYST-Agent im AIEmpire Gemini-Spiegel-System.
Du fuehrst ein Engineering-Review der Architekten-Vorschlaege durch.

Bewerte:
- Technische Machbarkeit (1-10)
- Risiken und Abhaengigkeiten
- Skalierbarkeit
- Kosten-Effizienz
- Zeitrahmen-Realismus

Antworte NUR als JSON:
{
  "timestamp": "ISO-Datum",
  "reviews": [
    {
      "solution": "Loesungs-Name",
      "feasibility_score": 1-10,
      "risk_assessment": {
        "technical_risks": ["..."],
        "business_risks": ["..."],
        "mitigation": ["..."]
      },
      "scalability": "Bewertung",
      "cost_analysis": "Beschreibung",
      "timeline_realistic": true/false,
      "recommended_changes": ["..."],
      "go_no_go": "GO|CAUTION|NO-GO"
    }
  ],
  "overall_recommendation": "Zusammenfassung",
  "critical_path": ["Schritt 1", "Schritt 2"],
  "dual_brain_advantage": "Wie nutzen wir Main+Mirror optimal"
}""",
        "user_template": """ARCHITEKTEN-VORSCHLAEGE:
{architect_result}

AUDIT-KONTEXT:
{audit_result}

Zyklus: {cycle}
System-Constraints: {constraints}

Fuehre ein gruendliches Engineering-Review durch.""",
    },
    "refinery": {
        "system": """Du bist der REFINERY-Agent im AIEmpire Gemini-Spiegel-System.
Du verbesserst iterativ die Loesung bis zur Konvergenz.

Iteration {iteration} von max {max_iterations}.
Vorheriger Score: {previous_score}/10

Verbessere die Loesung basierend auf dem Analyst-Feedback.
Fokus auf: Praktikabilitaet, Sofort-Umsetzbarkeit, ROI.

Antworte NUR als JSON:
{{
  "timestamp": "ISO-Datum",
  "iteration": {iteration},
  "refined_plan": {{
    "actions": [
      {{
        "title": "Aktion",
        "description": "Was genau",
        "priority": 1-5,
        "estimated_minutes": 0,
        "assignee": "main|mirror|both|manual",
        "dependencies": [],
        "deliverable": "Was kommt raus"
      }}
    ],
    "execution_order": ["Aktion-1", "Aktion-2"],
    "parallel_tracks": [["Track A Aktionen"], ["Track B Aktionen"]]
  }},
  "quality_score": 1-10,
  "improvements_made": ["Was wurde verbessert"],
  "remaining_issues": ["Was ist noch offen"],
  "converged": true/false
}}""",
        "user_template": """ZU VERBESSERN:
{previous_result}

ANALYST-FEEDBACK:
{analyst_result}

ITERATION: {iteration}/{max_iterations}
VORHERIGER SCORE: {previous_score}

Verfeinere und verbessere den Plan.""",
    },
    "compounder": {
        "system": """Du bist der COMPOUNDER-Agent im AIEmpire Gemini-Spiegel-System.
Du extrahierst wiederverwendbare Muster und planst den naechsten Zyklus.

Deine Aufgabe:
1. Muster erkennen (was hat funktioniert, was nicht)
2. Wissen komprimieren fuer zukuenftige Zyklen
3. Naechsten Zyklus planen
4. Cross-System Learnings (Main <-> Mirror)

Antworte NUR als JSON:
{
  "timestamp": "ISO-Datum",
  "cycle_summary": "Zusammenfassung des Zyklus",
  "patterns_discovered": [
    {
      "name": "Muster-Name",
      "description": "Beschreibung",
      "category": "revenue|content|automation|system",
      "reusable": true/false,
      "confidence": 1-10
    }
  ],
  "cross_system_insights": [
    {
      "insight": "Was haben wir gelernt",
      "applies_to": "main|mirror|both",
      "action_required": "Was muss getan werden"
    }
  ],
  "next_cycle_priorities": [
    {"title": "...", "why": "...", "estimated_impact": "..."}
  ],
  "knowledge_compressed": "Komprimiertes Wissen fuer naechsten Zyklus",
  "dual_brain_effectiveness": 1-10,
  "recommended_model_adjustments": {
    "main": "Empfehlungen fuer Main-System",
    "mirror": "Empfehlungen fuer Mirror-System"
  }
}""",
        "user_template": """ZYKLUS-ERGEBNISSE:
Audit: {audit_summary}
Architect: {architect_summary}
Analyst: {analyst_summary}
Refinery: {refinery_summary}

Bestehende Patterns: {existing_patterns}
Main-System Patterns: {main_patterns}
Zyklus: {cycle}
Vision: {vision_context}

Extrahiere Muster und plane den naechsten Zyklus.""",
    },
}

MAX_REFINERY_ITERATIONS = 5
CONVERGENCE_THRESHOLD = 0.5


# === State Management ===

def load_mirror_state() -> Dict:
    """Laedt Mirror-Zustand oder erstellt Default."""
    if MIRROR_STATE_FILE.exists():
        return json.loads(MIRROR_STATE_FILE.read_text())
    default = {
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "cycle": 1,
        "steps_completed": [],
        "context": {},
        "patterns": [],
        "improvements": [],
    }
    save_mirror_state(default)
    return default


def save_mirror_state(state: Dict):
    """Speichert Mirror-Zustand."""
    state["updated"] = datetime.now().isoformat()
    MIRROR_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def append_step_result(step_name: str, result: Dict) -> Dict:
    """Fuegt Schritt-Ergebnis zum Zustand hinzu."""
    state = load_mirror_state()
    state["steps_completed"].append({
        "step": step_name,
        "timestamp": datetime.now().isoformat(),
        "summary": json.dumps(result)[:500],
    })
    state["context"][step_name] = result

    # Output speichern
    output_file = OUTPUT_DIR / f"{step_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    save_mirror_state(state)
    return state


def get_context_for_step(step_name: str) -> Dict:
    """Baut Kontext fuer einen Schritt zusammen."""
    state = load_mirror_state()

    # Main-System Patterns laden (wenn vorhanden)
    main_patterns = []
    main_pattern_file = PROJECT_ROOT / "workflow-system" / "state" / "pattern_library.json"
    if main_pattern_file.exists():
        try:
            main_patterns = json.loads(main_pattern_file.read_text())
        except json.JSONDecodeError:
            pass

    # Vision-Kontext laden
    vision_context = ""
    vision_file = STATE_DIR / "vision_state.json"
    if vision_file.exists():
        try:
            vision_data = json.loads(vision_file.read_text())
            recent_answers = vision_data.get("answers", [])[-10:]
            vision_context = json.dumps(recent_answers, ensure_ascii=False)[:1000]
        except json.JSONDecodeError:
            pass

    return {
        "cycle": state.get("cycle", 1),
        "prior_steps": state.get("context", {}),
        "patterns": state.get("patterns", []),
        "main_patterns": main_patterns,
        "improvements": state.get("improvements", []),
        "vision_context": vision_context,
    }


def advance_cycle() -> int:
    """Archiviert aktuellen Zyklus und startet neuen."""
    state = load_mirror_state()
    old_cycle = state.get("cycle", 1)

    # Archivieren
    archive_file = HISTORY_DIR / f"mirror_cycle_{old_cycle}_{datetime.now().strftime('%Y%m%d')}.json"
    archive_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    # Neuen Zyklus starten (Patterns und Improvements mitnehmen)
    new_state = {
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "cycle": old_cycle + 1,
        "steps_completed": [],
        "context": {},
        "patterns": state.get("patterns", []),
        "improvements": state.get("improvements", []),
    }
    save_mirror_state(new_state)
    logger.info(f"Neuer Zyklus gestartet: {old_cycle + 1}")
    return old_cycle + 1


# === Step Execution ===

async def run_step(
    client: GeminiClient,
    step_name: str,
    context: Optional[Dict] = None,
) -> Dict:
    """Fuehrt einen Workflow-Schritt aus."""
    logger.info(f"=== SCHRITT: {step_name.upper()} ===")

    if context is None:
        context = get_context_for_step(step_name)

    prompts = STEP_PROMPTS[step_name]
    routing = MODEL_ROUTING.get(step_name, {"model": "flash", "temp": 0.7})

    # User-Prompt bauen
    if step_name == "audit":
        user_prompt = prompts["user_template"].format(
            cycle=context.get("cycle", 1),
            prior_steps=json.dumps(list(context.get("prior_steps", {}).keys())),
            main_patterns=json.dumps(context.get("main_patterns", [])[:5], ensure_ascii=False)[:500],
            mirror_patterns=json.dumps(context.get("patterns", [])[:5], ensure_ascii=False)[:500],
            last_results=json.dumps(context.get("prior_steps", {}), ensure_ascii=False)[:1000],
            vision_context=context.get("vision_context", "Keine Vision-Daten"),
        )
    elif step_name == "architect":
        user_prompt = prompts["user_template"].format(
            audit_result=json.dumps(context["prior_steps"].get("audit", {}), ensure_ascii=False)[:2000],
            cycle=context.get("cycle", 1),
            vision_context=context.get("vision_context", "Keine Vision-Daten"),
        )
    elif step_name == "analyst":
        user_prompt = prompts["user_template"].format(
            architect_result=json.dumps(context["prior_steps"].get("architect", {}), ensure_ascii=False)[:2000],
            audit_result=json.dumps(context["prior_steps"].get("audit", {}), ensure_ascii=False)[:1000],
            cycle=context.get("cycle", 1),
            constraints="Budget minimal, Ollama first, Gemini Flash for complex",
        )
    elif step_name == "compounder":
        user_prompt = prompts["user_template"].format(
            audit_summary=json.dumps(context["prior_steps"].get("audit", {}), ensure_ascii=False)[:500],
            architect_summary=json.dumps(context["prior_steps"].get("architect", {}), ensure_ascii=False)[:500],
            analyst_summary=json.dumps(context["prior_steps"].get("analyst", {}), ensure_ascii=False)[:500],
            refinery_summary=json.dumps(context["prior_steps"].get("refinery", {}), ensure_ascii=False)[:500],
            existing_patterns=json.dumps(context.get("patterns", []), ensure_ascii=False)[:500],
            main_patterns=json.dumps(context.get("main_patterns", [])[:5], ensure_ascii=False)[:500],
            cycle=context.get("cycle", 1),
            vision_context=context.get("vision_context", "Keine Vision-Daten"),
        )
    else:
        user_prompt = ""

    messages = [
        {"role": "system", "content": prompts["system"]},
        {"role": "user", "content": user_prompt},
    ]

    result = await client.chat_json(
        messages=messages,
        model=routing["model"],
        temperature=routing["temp"],
        max_tokens=6000,
    )

    parsed = result.get("parsed", {})
    if result.get("parse_success"):
        logger.info(f"  ✓ {step_name} erfolgreich (Score: {parsed.get('quality_score', parsed.get('overall_score', '?'))})")
    else:
        logger.warning(f"  ⚠ {step_name} JSON-Parse fehlgeschlagen, Raw gespeichert")

    # Ergebnis speichern
    step_result = {
        "step": step_name,
        "timestamp": datetime.now().isoformat(),
        "model_used": result.get("model", "unknown"),
        "source": result.get("source", "unknown"),
        "cost_usd": result.get("cost_usd", 0),
        "latency_ms": result.get("latency_ms", 0),
        "data": parsed,
    }

    append_step_result(step_name, step_result)
    return step_result


async def run_refinery_loop(
    client: GeminiClient,
    context: Dict,
) -> Dict:
    """Refinery-Konvergenzschleife."""
    logger.info("=== REFINERY KONVERGENZ-LOOP ===")

    routing = MODEL_ROUTING.get("refinery", {"model": "pro", "temp": 0.6})
    previous_score = 0
    previous_result = context["prior_steps"].get("analyst", {})
    best_result = None

    for iteration in range(1, MAX_REFINERY_ITERATIONS + 1):
        logger.info(f"  Iteration {iteration}/{MAX_REFINERY_ITERATIONS}")

        system_prompt = STEP_PROMPTS["refinery"]["system"].format(
            iteration=iteration,
            max_iterations=MAX_REFINERY_ITERATIONS,
            previous_score=previous_score,
        )
        user_prompt = STEP_PROMPTS["refinery"]["user_template"].format(
            previous_result=json.dumps(previous_result, ensure_ascii=False)[:2000],
            analyst_result=json.dumps(
                context["prior_steps"].get("analyst", {}), ensure_ascii=False
            )[:1000],
            iteration=iteration,
            max_iterations=MAX_REFINERY_ITERATIONS,
            previous_score=previous_score,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = await client.chat_json(
            messages=messages,
            model=routing["model"],
            temperature=routing["temp"],
            max_tokens=6000,
        )

        parsed = result.get("parsed", {})
        current_score = parsed.get("quality_score", 5)

        logger.info(f"    Score: {current_score}/10 (vorher: {previous_score})")

        if current_score > (previous_score or 0):
            best_result = parsed

        # Konvergenz pruefen
        if parsed.get("converged") or (
            previous_score > 0
            and abs(current_score - previous_score) < CONVERGENCE_THRESHOLD
        ):
            logger.info(f"  ✓ Konvergiert bei Iteration {iteration}")
            break

        previous_score = current_score
        previous_result = parsed

    final_result = {
        "step": "refinery",
        "timestamp": datetime.now().isoformat(),
        "iterations": iteration,
        "final_score": current_score,
        "model_used": result.get("model", "unknown"),
        "cost_usd": result.get("cost_usd", 0),
        "data": best_result or parsed,
    }

    append_step_result("refinery", final_result)
    return final_result


# === Main Loop ===

async def run_full_loop():
    """Fuehrt den kompletten 5-Schritt Mirror-Loop aus."""
    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║  GEMINI MIRROR - 5-STEP COMPOUND LOOP   ║")
    logger.info("╚══════════════════════════════════════════╝")

    client = GeminiClient()
    state = load_mirror_state()
    logger.info(f"Zyklus: {state.get('cycle', 1)}")

    # Step 1: AUDIT
    await run_step(client, "audit")

    # Step 2: ARCHITECT
    await run_step(client, "architect")

    # Step 3: ANALYST
    await run_step(client, "analyst")

    # Step 4: REFINERY (Konvergenz-Loop)
    context = get_context_for_step("refinery")
    await run_refinery_loop(client, context)

    # Step 5: COMPOUNDER
    await run_step(client, "compounder")

    # Kosten-Report
    stats = client.get_cost_stats()
    logger.info(f"\n=== ZYKLUS ABGESCHLOSSEN ===")
    logger.info(f"Kosten: ${stats['today_cost_usd']:.4f}")
    logger.info(f"Calls: {stats['total_calls']}")
    logger.info(f"Tokens: {stats['total_tokens_in'] + stats['total_tokens_out']:,}")

    return load_mirror_state()


async def run_single_step(step_name: str):
    """Fuehrt einen einzelnen Schritt aus."""
    client = GeminiClient()

    if step_name == "refinery":
        context = get_context_for_step("refinery")
        return await run_refinery_loop(client, context)
    else:
        return await run_step(client, step_name)


def show_status():
    """Zeigt den aktuellen Mirror-Status."""
    state = load_mirror_state()
    print("\n╔══════════════════════════════════════════╗")
    print("║     GEMINI MIRROR - SYSTEM STATUS        ║")
    print("╚══════════════════════════════════════════╝")
    print(f"  Zyklus:      {state.get('cycle', 1)}")
    print(f"  Erstellt:    {state.get('created', 'N/A')}")
    print(f"  Aktualisiert: {state.get('updated', 'N/A')}")
    print(f"  Schritte:    {len(state.get('steps_completed', []))}")
    print(f"  Patterns:    {len(state.get('patterns', []))}")

    if state.get("steps_completed"):
        print("\n  Abgeschlossene Schritte:")
        for s in state["steps_completed"][-10:]:
            print(f"    - {s['step']} ({s['timestamp'][:16]})")

    if state.get("context"):
        print("\n  Verfuegbarer Kontext:")
        for key in state["context"]:
            print(f"    - {key}")

    print()


# === CLI ===

def main():
    parser = argparse.ArgumentParser(description="Gemini Mirror Orchestrator")
    parser.add_argument("--step", choices=["audit", "architect", "analyst", "refinery", "compounder"],
                        help="Einzelnen Schritt ausfuehren")
    parser.add_argument("--new-cycle", action="store_true", help="Neuen Zyklus starten")
    parser.add_argument("--status", action="store_true", help="Status anzeigen")
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.new_cycle:
        new_cycle = advance_cycle()
        print(f"Neuer Zyklus gestartet: {new_cycle}")
    elif args.step:
        asyncio.run(run_single_step(args.step))
    else:
        asyncio.run(run_full_loop())


if __name__ == "__main__":
    main()
