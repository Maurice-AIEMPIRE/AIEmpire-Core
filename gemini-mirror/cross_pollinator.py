#!/usr/bin/env python3
"""
CROSS-POLLINATOR - Bidirectional Improvement Protocol
Makes both brains (Claude + Gemini) continuously improve each other.

How it works:
1. Each brain independently works on tasks/strategies
2. Cross-Pollinator compares outputs from both
3. Extracts the best ideas from each
4. Merges improvements into a unified "best of both" result
5. Both brains receive the merged improvements

This creates an evolutionary loop where each generation is better
than what either brain could produce alone.

Usage:
  python cross_pollinator.py                     # Run one pollination cycle
  python cross_pollinator.py --compare           # Compare latest outputs
  python cross_pollinator.py --merge             # Merge pending improvements
  python cross_pollinator.py --evolve            # Run full evolution cycle
  python cross_pollinator.py --status            # Show pollination status
"""

import asyncio
import aiohttp
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    PROJECT_ROOT, MIRROR_DIR, STATE_DIR, OUTPUT_DIR,
    CROSS_POLLINATION_CONFIG, MODEL_ROUTING,
)
from mirror_core import call_gemini, call_gemini_flash, get_pending_improvements

# ── State ────────────────────────────────────────────────────

POLLINATION_STATE_FILE = STATE_DIR / "pollination_state.json"
EVOLUTION_DIR = OUTPUT_DIR / "evolution"
EVOLUTION_DIR.mkdir(parents=True, exist_ok=True)


def load_pollination_state() -> Dict:
    if POLLINATION_STATE_FILE.exists():
        return json.loads(POLLINATION_STATE_FILE.read_text())
    return {
        "created": datetime.now().isoformat(),
        "total_cycles": 0,
        "total_merges": 0,
        "total_improvements_applied": 0,
        "evolution_generation": 0,
        "best_practices": [],       # Accumulated best practices
        "failed_experiments": [],    # Things that didn't work
        "active_comparisons": [],
        "merge_history": [],
    }


def save_pollination_state(state: Dict) -> None:
    state["updated"] = datetime.now().isoformat()
    POLLINATION_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ── Dual-Brain Challenge ─────────────────────────────────────

async def dual_brain_challenge(task: str, context: str = "") -> Dict:
    """Send the same task to both brains and compare results.

    This is the core mechanism: both brains solve the same problem,
    then we compare and merge the best of both.
    """
    print(f"\n  DUAL-BRAIN CHALLENGE")
    print(f"  Task: {task[:60]}")
    print("  " + "-" * 50)

    system_instruction = (
        "Du bist Teil von Maurice Pfeifer's AI Empire. "
        "Loesung muss KONKRET, UMSETZBAR und MESSBAR sein. "
        f"Zusaetzlicher Kontext: {context[:500]}" if context else
        "Du bist Teil von Maurice Pfeifer's AI Empire. "
        "Loesung muss KONKRET, UMSETZBAR und MESSBAR sein."
    )

    # Send to Gemini
    print("  [1/3] Gemini brain working...")
    gemini_result = await call_gemini(task, system_instruction=system_instruction)

    # Send to Kimi (as proxy for Claude primary processing)
    print("  [2/3] Kimi brain working...")
    kimi_result = await call_kimi(task, system_instruction)

    # Compare and merge
    print("  [3/3] Merging best of both...")
    merged = await merge_results(task, gemini_result, kimi_result)

    result = {
        "task": task,
        "gemini_response": gemini_result[:2000],
        "kimi_response": kimi_result[:2000],
        "merged_result": merged,
        "timestamp": datetime.now().isoformat(),
    }

    # Save evolution
    gen = load_pollination_state().get("evolution_generation", 0) + 1
    evo_file = EVOLUTION_DIR / f"gen_{gen:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    evo_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    return result


async def call_kimi(prompt: str, system_instruction: str = "") -> str:
    """Call Kimi API (represents the existing primary brain's processing)."""
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        return "[KIMI OFFLINE] MOONSHOT_API_KEY not set"

    url = "https://api.moonshot.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "moonshot-v1-32k",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 4000,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload,
                                     timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"[KIMI ERROR] Status {resp.status}"
        except Exception as e:
            return f"[KIMI ERROR] {str(e)}"


async def merge_results(task: str, result_a: str, result_b: str) -> Dict:
    """Merge the best of both brain results using Gemini as judge."""
    prompt = f"""Du bist der Merge-Judge im Dual-Brain System.

AUFGABE:
{task}

ERGEBNIS BRAIN A (Gemini):
{result_a[:3000]}

ERGEBNIS BRAIN B (Kimi/Primary):
{result_b[:3000]}

Dein Job:
1. Bewerte beide Ergebnisse (Score 1-10)
2. Identifiziere die STAERKEN jedes Ergebnisses
3. Erstelle eine MERGED VERSION die das Beste aus beiden kombiniert
4. Liste konkrete VERBESSERUNGEN auf die nur durch den Merge moeglich sind

Antworte als JSON:
{{
  "score_a": 8,
  "score_b": 7,
  "strengths_a": ["..."],
  "strengths_b": ["..."],
  "merged_result": "Die beste kombinierte Loesung...",
  "merge_improvements": ["..."],
  "winner": "a|b|merged",
  "confidence": 0.85
}}"""

    response = await call_gemini(prompt, system_instruction=(
        "Du bist ein objektiver Judge der zwei AI-Ergebnisse vergleicht "
        "und das Beste aus beiden kombiniert. Sei fair und praezise. "
        "Antworte NUR als valides JSON."
    ))

    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        return json.loads(response.strip())
    except (json.JSONDecodeError, IndexError):
        return {
            "merged_result": f"[MERGE FAILED] Bestes Einzelergebnis wird verwendet.\n\n{result_a[:1000]}",
            "score_a": 5,
            "score_b": 5,
            "winner": "unknown",
        }


# ── Evolution Cycle ──────────────────────────────────────────

async def run_evolution_cycle() -> Dict:
    """Run a full evolution cycle: challenge, compare, merge, apply."""
    print("\n  EVOLUTION CYCLE")
    print("  " + "=" * 50)

    state = load_pollination_state()
    gen = state.get("evolution_generation", 0) + 1
    print(f"  Generation: #{gen}")

    # Define challenges based on current system needs
    challenges = await identify_challenges()

    results = []
    for i, challenge in enumerate(challenges[:3], 1):  # Max 3 per cycle
        print(f"\n  Challenge {i}/{min(len(challenges), 3)}: {challenge['title'][:50]}")
        result = await dual_brain_challenge(
            task=challenge["prompt"],
            context=challenge.get("context", ""),
        )
        results.append(result)

    # Extract best practices from this generation
    best_practices = await extract_best_practices(results)

    # Update state
    state["total_cycles"] += 1
    state["evolution_generation"] = gen
    state["best_practices"].extend(best_practices)
    # Keep last 50 best practices
    state["best_practices"] = state["best_practices"][-50:]
    state["total_merges"] += len(results)

    save_pollination_state(state)

    print(f"\n  Evolution cycle #{gen} complete.")
    print(f"  Challenges solved: {len(results)}")
    print(f"  Best practices extracted: {len(best_practices)}")

    return {
        "generation": gen,
        "challenges_solved": len(results),
        "best_practices": best_practices,
    }


async def identify_challenges() -> List[Dict]:
    """Identify the most important challenges to solve right now."""

    # Read current system state
    system_context = []

    # Check workflow state
    wf_state = PROJECT_ROOT / "workflow-system" / "state" / "current_state.json"
    if wf_state.exists():
        system_context.append(f"Workflow: {wf_state.read_text()[:500]}")

    # Check vision profile
    vision_profile = MIRROR_DIR / "memory" / "vision_profile.json"
    if vision_profile.exists():
        system_context.append(f"Vision: {vision_profile.read_text()[:500]}")

    prompt = f"""Basierend auf dem aktuellen System-Zustand von Maurice's AI Empire,
identifiziere die 3 wichtigsten Herausforderungen die JETZT geloest werden muessen.

SYSTEM-KONTEXT:
{chr(10).join(system_context)[:2000]}

EMPIRE ZIEL: 100 Mio EUR in 1-3 Jahren, alles automatisiert.
AKTUELLE BLOCKER: Revenue = 0 EUR, keine aktiven Produkte, kein Traffic.

Generiere 3 Challenges die beide AI-Brains gleichzeitig loesen sollen:

Antworte als JSON Array:
[
  {{
    "title": "...",
    "prompt": "Detaillierte Aufgabenbeschreibung...",
    "context": "Relevanter Kontext...",
    "expected_outcome": "...",
    "priority": "critical|high|medium"
  }}
]"""

    response = await call_gemini_flash(prompt, system_instruction=(
        "Du bist der Challenge-Generator im Dual-Brain System. "
        "Identifiziere die wichtigsten Probleme die geloest werden muessen. "
        "Fokus auf REVENUE und PRODUKT-LAUNCH. Antworte als JSON Array."
    ))

    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        challenges = json.loads(response.strip())
        if isinstance(challenges, list):
            return challenges
    except (json.JSONDecodeError, IndexError):
        pass

    # Fallback challenges
    return [
        {
            "title": "Erstes Produkt definieren und strukturieren",
            "prompt": "Definiere das erste verkaufbare Produkt fuer Maurice's AI Empire. "
                      "Es muss in 48h produzierbar sein und mindestens 29 EUR kosten. "
                      "Zielgruppe: Handwerksmeister und kleine Betriebe.",
            "context": "Maurice ist Elektrotechnikmeister mit 16 Jahren BMA-Erfahrung.",
            "expected_outcome": "Komplettes Produkt-Konzept mit Inhalten und Preisstruktur",
            "priority": "critical",
        },
        {
            "title": "Revenue Pipeline aktivieren",
            "prompt": "Erstelle einen konkreten 7-Tage-Plan um den ersten Euro Umsatz zu generieren. "
                      "Kanaele: Gumroad, Fiverr, X/Twitter, LinkedIn.",
            "context": "Revenue aktuell 0 EUR. Infrastruktur steht.",
            "expected_outcome": "Tagesgenauer Aktionsplan mit messbaren Meilensteinen",
            "priority": "critical",
        },
        {
            "title": "Content Engine fuer organischen Traffic starten",
            "prompt": "Erstelle eine Content-Strategie die in 30 Tagen 1000 Follower und "
                      "10 qualifizierte Leads generiert. Plattform: X/Twitter und LinkedIn.",
            "context": "X Lead Machine vorhanden aber nicht aktiv.",
            "expected_outcome": "30-Tage-Contentplan mit Templates und Posting-Zeiten",
            "priority": "high",
        },
    ]


async def extract_best_practices(results: List[Dict]) -> List[Dict]:
    """Extract reusable best practices from challenge results."""
    if not results:
        return []

    merged_texts = []
    for r in results:
        merged = r.get("merged_result", {})
        if isinstance(merged, dict):
            merged_texts.append(merged.get("merged_result", ""))
        elif isinstance(merged, str):
            merged_texts.append(merged)

    prompt = f"""Extrahiere wiederverwendbare Best Practices aus diesen Dual-Brain Ergebnissen:

{chr(10).join(merged_texts)[:4000]}

Identifiziere 3-5 Best Practices die:
1. In zukuenftigen Challenges wiederverwendet werden koennen
2. Das System nachhaltig verbessern
3. Konkret und umsetzbar sind

Antworte als JSON Array:
[
  {{
    "practice": "...",
    "applies_to": "strategy|code|content|revenue|automation",
    "confidence": 0.8,
    "source_generation": "current"
  }}
]"""

    response = await call_gemini_flash(prompt, system_instruction=(
        "Du bist der Best-Practice-Extraktor. Finde wiederverwendbare "
        "Muster und Strategien. Antworte als JSON Array."
    ))

    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        practices = json.loads(response.strip())
        if isinstance(practices, list):
            return practices
    except (json.JSONDecodeError, IndexError):
        pass

    return []


# ── Status Display ───────────────────────────────────────────

def show_status() -> None:
    """Show cross-pollination status."""
    state = load_pollination_state()

    print("\n  CROSS-POLLINATOR STATUS")
    print("  " + "=" * 50)
    print(f"  Evolution Generation: #{state.get('evolution_generation', 0)}")
    print(f"  Total Cycles:         {state.get('total_cycles', 0)}")
    print(f"  Total Merges:         {state.get('total_merges', 0)}")
    print(f"  Improvements Applied: {state.get('total_improvements_applied', 0)}")
    print(f"  Last Updated:         {state.get('updated', 'never')}")

    # Best practices
    practices = state.get("best_practices", [])
    if practices:
        print(f"\n  BEST PRACTICES ({len(practices)}):")
        for p in practices[-5:]:
            if isinstance(p, dict):
                applies = p.get("applies_to", "?")
                practice = p.get("practice", str(p))
                print(f"    [{applies:12s}] {practice[:55]}")
            else:
                print(f"    - {str(p)[:60]}")

    # Evolution files
    evo_files = sorted(EVOLUTION_DIR.glob("gen_*.json"))
    if evo_files:
        print(f"\n  EVOLUTION HISTORY ({len(evo_files)} generations):")
        for f in evo_files[-5:]:
            print(f"    {f.name}")

    # Pending improvements
    pending = get_pending_improvements()
    if pending:
        print(f"\n  PENDING IMPROVEMENTS ({len(pending)}):")
        for imp in pending[:3]:
            print(f"    [{imp.get('priority', '?').upper():6s}] {imp.get('title', 'N/A')[:50]}")

    print()


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cross-Pollinator - Dual-Brain Evolution")
    parser.add_argument("--compare", action="store_true", help="Compare latest outputs")
    parser.add_argument("--merge", action="store_true", help="Merge pending improvements")
    parser.add_argument("--evolve", action="store_true", help="Run full evolution cycle")
    parser.add_argument("--challenge", type=str, help="Run a specific challenge")
    parser.add_argument("--status", action="store_true", help="Show pollination status")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.evolve:
        asyncio.run(run_evolution_cycle())
    elif args.challenge:
        asyncio.run(dual_brain_challenge(args.challenge))
    else:
        show_status()


if __name__ == "__main__":
    main()
