#!/usr/bin/env python3
"""
VISION DISCOVERY ENGINE - Daily Question System
Both brains (Claude + Gemini) ask Maurice targeted questions every day
to build a precise, evolving model of his vision, priorities, and decisions.

The answers accumulate into a "Vision Profile" that makes both brains
progressively smarter about what Maurice actually wants.

Usage:
  python vision_engine.py                    # Generate today's questions
  python vision_engine.py --answer           # Record answers interactively
  python vision_engine.py --profile          # Show current vision profile
  python vision_engine.py --history          # Show question/answer history
"""

import asyncio
import aiohttp
import argparse
import json
import os
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    MIRROR_DIR, STATE_DIR, MEMORY_DIR, OUTPUT_DIR,
    GEMINI_API_KEY, VISION_CONFIG,
)
from mirror_core import call_gemini, call_gemini_flash

# ── State Files ──────────────────────────────────────────────

VISION_STATE_FILE = STATE_DIR / "vision_state.json"
VISION_PROFILE_FILE = MEMORY_DIR / "vision_profile.json"
QA_HISTORY_FILE = MEMORY_DIR / "qa_history.json"


def load_vision_state() -> Dict:
    if VISION_STATE_FILE.exists():
        return json.loads(VISION_STATE_FILE.read_text())
    return {
        "created": datetime.now().isoformat(),
        "total_questions_asked": 0,
        "total_answers_received": 0,
        "last_question_date": None,
        "unanswered_questions": [],
        "question_queue": [],
        "categories_covered": {},
        "confidence_scores": {},  # How confident we are about each vision aspect
    }


def save_vision_state(state: Dict) -> None:
    state["updated"] = datetime.now().isoformat()
    VISION_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def load_vision_profile() -> Dict:
    if VISION_PROFILE_FILE.exists():
        return json.loads(VISION_PROFILE_FILE.read_text())
    return {
        "created": datetime.now().isoformat(),
        "owner": "Maurice Pfeifer",
        "core_identity": {
            "profession": "Elektrotechnikmeister, 16 Jahre BMA-Expertise",
            "age": 37,
            "location": "Deutschland",
        },
        "vision": {
            "financial_goal": "100 Mio EUR in 1-3 Jahren",
            "automation_level": "Alles automatisiert mit AI",
            "unique_advantage": "BMA + AI Kombination = niemand sonst hat das",
        },
        "priorities": {},        # Ranked by importance
        "preferences": {},       # How he likes things done
        "boundaries": {},        # What he does NOT want
        "decisions_made": [],    # Key decisions with reasoning
        "personality_traits": {},# Work style, communication, risk tolerance
        "life_goals": {},        # Beyond business
        "knowledge_gaps": [],    # What we still don't know
        "last_updated": None,
        "update_count": 0,
    }


def save_vision_profile(profile: Dict) -> None:
    profile["last_updated"] = datetime.now().isoformat()
    profile["update_count"] = profile.get("update_count", 0) + 1
    VISION_PROFILE_FILE.write_text(json.dumps(profile, indent=2, ensure_ascii=False))


def load_qa_history() -> List[Dict]:
    if QA_HISTORY_FILE.exists():
        return json.loads(QA_HISTORY_FILE.read_text())
    return []


def save_qa_history(history: List[Dict]) -> None:
    QA_HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False))


# ── Question Generation ──────────────────────────────────────

QUESTION_CATEGORIES = {
    "vision_clarity": {
        "de": "Vision & Zielklarheit",
        "focus": "Was genau sieht Erfolg fuer dich aus? Wie fuehlt sich das Ziel an?",
    },
    "priority_ranking": {
        "de": "Prioritaeten",
        "focus": "Was ist JETZT am wichtigsten? Was kann warten?",
    },
    "resource_allocation": {
        "de": "Ressourcen & Investitionen",
        "focus": "Wo soll Zeit/Geld/Energie hinfliessen?",
    },
    "risk_tolerance": {
        "de": "Risikobereitschaft",
        "focus": "Wie aggressiv darf das System sein?",
    },
    "lifestyle_goals": {
        "de": "Lebensziele",
        "focus": "Welches Leben willst du leben? Wie sieht ein perfekter Tag aus?",
    },
    "business_model": {
        "de": "Geschaeftsmodell",
        "focus": "Wie soll Geld fliessen? Welche Revenue Streams?",
    },
    "tech_preferences": {
        "de": "Technologie & Tools",
        "focus": "Welche Tools/Ansaetze passen zu dir?",
    },
    "relationship_goals": {
        "de": "Beziehungen & Netzwerk",
        "focus": "Mit wem willst du arbeiten? Welche Partnerschaften?",
    },
    "timeline_pressure": {
        "de": "Zeitdruck & Deadlines",
        "focus": "Wie dringend ist was? Wann muss was fertig sein?",
    },
    "unfair_advantages": {
        "de": "Unfaire Vorteile",
        "focus": "Was macht dich einzigartig? Welche Staerken nutzen?",
    },
    "product_vision": {
        "de": "Produkt-Vision",
        "focus": "Welche Produkte? Fuer wen? Zu welchem Preis?",
    },
    "personal_values": {
        "de": "Werte & Prinzipien",
        "focus": "Was ist dir wichtig? Wofuer stehst du?",
    },
}


async def generate_daily_questions(force: bool = False) -> List[Dict]:
    """Generate today's targeted questions for Maurice."""
    state = load_vision_state()
    profile = load_vision_profile()
    history = load_qa_history()

    # Check if already generated today
    today = date.today().isoformat()
    if state.get("last_question_date") == today and not force:
        print(f"  Fragen fuer heute ({today}) bereits generiert.")
        return state.get("unanswered_questions", [])

    # Find least-covered categories
    coverage = state.get("categories_covered", {})
    least_covered = sorted(
        QUESTION_CATEGORIES.keys(),
        key=lambda c: coverage.get(c, 0)
    )[:5]

    # Build context from profile and history
    recent_answers = history[-10:] if history else []
    knowledge_gaps = profile.get("knowledge_gaps", [])

    prompt = f"""Du bist der Vision Discovery Agent fuer Maurice Pfeifer's AI Empire.

MAURICE'S AKTUELLES PROFIL:
{json.dumps(profile, indent=2, ensure_ascii=False)[:3000]}

LETZTE ANTWORTEN (die letzten 10):
{json.dumps(recent_answers, indent=2, ensure_ascii=False)[:2000]}

WISSENSLUCKEN:
{json.dumps(knowledge_gaps, ensure_ascii=False)[:500]}

AM WENIGSTEN ABGEDECKTE KATEGORIEN:
{json.dumps(least_covered, ensure_ascii=False)}

KATEGORIEN MIT BESCHREIBUNG:
{json.dumps({k: v['de'] for k, v in QUESTION_CATEGORIES.items()}, indent=2, ensure_ascii=False)}

Generiere genau 5 Fragen fuer heute. Die Fragen muessen:
1. KONKRET sein (keine vagen "Was denkst du?"-Fragen)
2. ENTSCHEIDUNGEN erzwingen (A oder B, nicht "was findest du?")
3. NEUE INFORMATIONEN liefern (nichts fragen was wir schon wissen)
4. VERSCHIEDENE KATEGORIEN abdecken
5. AUF DEUTSCH sein (Maurice spricht Deutsch)
6. KURZ sein (max 2 Saetze pro Frage)

Antworte als JSON Array:
[
  {{
    "id": "q_{today}_001",
    "category": "vision_clarity",
    "question_de": "...",
    "why_this_question": "...",
    "expected_insight": "..."
  }}
]"""

    print("  Generating daily questions...")
    response = await call_gemini(prompt, system_instruction=(
        "Du bist Maurice's digitales Gedaechtnis. Du stellst jeden Tag "
        "praezise Fragen um seine Vision, Prioritaeten und Entscheidungen "
        "besser zu verstehen. Dein Ziel: Ein so genaues Modell von Maurice "
        "aufbauen, dass du seine Entscheidungen vorhersagen kannst. "
        "Antworte NUR als valides JSON Array."
    ))

    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        questions = json.loads(response.strip())
    except (json.JSONDecodeError, IndexError):
        # Fallback: generate basic questions
        questions = generate_fallback_questions(least_covered, today)

    # Update state
    state["last_question_date"] = today
    state["total_questions_asked"] += len(questions)
    state["unanswered_questions"] = questions
    for q in questions:
        cat = q.get("category", "unknown")
        state["categories_covered"][cat] = state["categories_covered"].get(cat, 0) + 1
    state["question_queue"] = questions
    save_vision_state(state)

    return questions


def generate_fallback_questions(categories: List[str], today: str) -> List[Dict]:
    """Generate basic fallback questions if Gemini is unavailable."""
    fallback_templates = {
        "vision_clarity": "Wenn du in 12 Monaten zurueckschaust - was MUSS passiert sein damit du sagst 'Das Jahr war ein voller Erfolg'?",
        "priority_ranking": "Du kannst diese Woche NUR an EINEM Projekt arbeiten. Welches waere es und warum?",
        "resource_allocation": "Du hast 1000 EUR Budget fuer die naechsten 7 Tage. Wofuer gibst du es aus?",
        "risk_tolerance": "Wuerdest du lieber 50K EUR sicher verdienen oder eine 30% Chance auf 500K EUR?",
        "lifestyle_goals": "Beschreibe deinen perfekten Dienstag in 2 Jahren. Von morgens bis abends.",
        "business_model": "Welcher Revenue Stream soll in 90 Tagen dein Haupteinkommen sein?",
        "tech_preferences": "Wenn du nur EINE AI nutzen koenntest - welche und wofuer?",
        "relationship_goals": "Welche 3 Personen wuerden dein Business am meisten beschleunigen?",
        "timeline_pressure": "Was muss DIESE WOCHE passieren, damit du am Sonntag zufrieden bist?",
        "unfair_advantages": "Was kannst du besser als 99% der Leute die das Gleiche versuchen?",
        "product_vision": "Wenn du JETZT ein Produkt launchen muesstest - was waere es und fuer wen?",
        "personal_values": "Wofuer willst du bekannt sein? Was sollen Leute ueber dich sagen?",
    }

    questions = []
    for i, cat in enumerate(categories[:5]):
        questions.append({
            "id": f"q_{today}_{i+1:03d}",
            "category": cat,
            "question_de": fallback_templates.get(cat, f"Was ist dir im Bereich {cat} am wichtigsten?"),
            "why_this_question": f"Kategorie {cat} am wenigsten abgedeckt",
            "expected_insight": f"Besseres Verstaendnis von {QUESTION_CATEGORIES.get(cat, {}).get('de', cat)}",
        })

    return questions


# ── Answer Processing ────────────────────────────────────────

async def process_answer(question_id: str, answer: str) -> Dict:
    """Process Maurice's answer and update the vision profile."""
    state = load_vision_state()
    profile = load_vision_profile()
    history = load_qa_history()

    # Find the question
    question = None
    for q in state.get("unanswered_questions", []):
        if q.get("id") == question_id:
            question = q
            break

    if not question:
        # Try matching by index
        unanswered = state.get("unanswered_questions", [])
        try:
            idx = int(question_id) - 1
            if 0 <= idx < len(unanswered):
                question = unanswered[idx]
        except ValueError:
            pass

    if not question:
        return {"error": f"Frage {question_id} nicht gefunden"}

    # Store Q&A
    qa_entry = {
        "date": datetime.now().isoformat(),
        "question": question,
        "answer": answer,
    }
    history.append(qa_entry)
    save_qa_history(history)

    # Update profile using Gemini
    print("  Processing answer and updating vision profile...")
    profile_update = await extract_profile_update(question, answer, profile)

    # Apply updates
    if profile_update:
        for key, value in profile_update.items():
            if key in profile and isinstance(profile[key], dict) and isinstance(value, dict):
                profile[key].update(value)
            elif key in profile and isinstance(profile[key], list) and isinstance(value, list):
                profile[key].extend(value)
            else:
                profile[key] = value

    save_vision_profile(profile)

    # Remove from unanswered
    state["unanswered_questions"] = [
        q for q in state.get("unanswered_questions", [])
        if q.get("id") != question.get("id")
    ]
    state["total_answers_received"] += 1

    # Update confidence
    category = question.get("category", "unknown")
    current_confidence = state.get("confidence_scores", {}).get(category, 0)
    state["confidence_scores"][category] = min(1.0, current_confidence + 0.1)

    save_vision_state(state)

    return {
        "status": "processed",
        "question": question.get("question_de", ""),
        "answer": answer,
        "profile_updated": bool(profile_update),
        "confidence": state["confidence_scores"].get(category, 0),
    }


async def extract_profile_update(question: Dict, answer: str, profile: Dict) -> Optional[Dict]:
    """Use Gemini to extract structured insights from an answer."""
    prompt = f"""Maurice hat eine Frage beantwortet. Extrahiere die Erkenntnisse fuer sein Profil.

FRAGE:
Kategorie: {question.get('category', 'unknown')}
Frage: {question.get('question_de', 'N/A')}

MAURICE'S ANTWORT:
{answer}

AKTUELLES PROFIL (Ausschnitt):
{json.dumps(profile, indent=2, ensure_ascii=False)[:2000]}

Extrahiere die neuen Erkenntnisse und gib zurueck welche Profil-Felder aktualisiert werden sollen.
Moegliche Felder: priorities, preferences, boundaries, decisions_made, personality_traits, life_goals, knowledge_gaps, vision

Antworte als JSON:
{{
  "priorities": {{"key": "value"}},
  "preferences": {{"key": "value"}},
  "decisions_made": ["Entscheidung mit Begruendung"],
  "knowledge_gaps": ["Was wir noch nicht wissen"],
  "new_insights": "Zusammenfassung der neuen Erkenntnis"
}}

Nur Felder mit echten neuen Erkenntnissen zurueckgeben. Leere Felder weglassen."""

    response = await call_gemini_flash(prompt, system_instruction=(
        "Du bist der Profil-Analyst fuer Maurice's digitales Gedaechtnis. "
        "Extrahiere praezise, strukturierte Erkenntnisse aus seinen Antworten. "
        "Antworte NUR als valides JSON."
    ))

    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        return json.loads(response.strip())
    except (json.JSONDecodeError, IndexError):
        return None


# ── Interactive Answer Session ───────────────────────────────

async def interactive_answer_session() -> None:
    """Interactive session where Maurice answers today's questions."""
    state = load_vision_state()
    questions = state.get("unanswered_questions", [])

    if not questions:
        print("\n  Keine offenen Fragen. Generiere neue...")
        questions = await generate_daily_questions(force=True)

    if not questions:
        print("  Konnte keine Fragen generieren.")
        return

    print(f"\n  VISION DISCOVERY - {len(questions)} Fragen fuer heute")
    print("  " + "=" * 50)
    print("  Antworte kurz in Stichworten oder ganzen Saetzen.")
    print("  Tippe 'skip' um eine Frage zu ueberspringen.")
    print("  Tippe 'quit' um die Session zu beenden.\n")

    answered = 0
    for i, q in enumerate(questions, 1):
        category = QUESTION_CATEGORIES.get(q.get("category", ""), {})
        cat_name = category.get("de", q.get("category", ""))

        print(f"  [{i}/{len(questions)}] {cat_name}")
        print(f"  {q.get('question_de', 'N/A')}")
        print()

        answer = input("  >>> ").strip()

        if answer.lower() == "quit":
            print("\n  Session beendet.")
            break
        elif answer.lower() == "skip":
            print("  Uebersprungen.\n")
            continue
        elif not answer:
            print("  Keine Antwort. Uebersprungen.\n")
            continue

        result = await process_answer(q.get("id", str(i)), answer)
        if result.get("profile_updated"):
            print(f"  Profil aktualisiert. Confidence: {result.get('confidence', 0):.0%}")
        answered += 1
        print()

    print(f"\n  Session abgeschlossen: {answered}/{len(questions)} Fragen beantwortet.")

    # Show profile summary if answers were given
    if answered > 0:
        show_profile_summary()


# ── Display Functions ────────────────────────────────────────

def show_todays_questions() -> None:
    """Display today's questions."""
    state = load_vision_state()
    questions = state.get("unanswered_questions", [])

    if not questions:
        print("\n  Keine offenen Fragen vorhanden.")
        print("  Generiere mit: python vision_engine.py --generate\n")
        return

    print(f"\n  TAGESFRAGEN ({state.get('last_question_date', 'N/A')})")
    print("  " + "=" * 50)

    for i, q in enumerate(questions, 1):
        category = QUESTION_CATEGORIES.get(q.get("category", ""), {})
        cat_name = category.get("de", q.get("category", ""))
        print(f"\n  [{i}] {cat_name}")
        print(f"      {q.get('question_de', 'N/A')}")

    print(f"\n  Beantworte mit: python vision_engine.py --answer\n")


def show_profile_summary() -> None:
    """Show the current vision profile summary."""
    profile = load_vision_profile()

    print(f"\n  VISION PROFILE - {profile.get('owner', 'N/A')}")
    print("  " + "=" * 50)

    # Core identity
    identity = profile.get("core_identity", {})
    print(f"\n  IDENTITAET:")
    for k, v in identity.items():
        print(f"    {k}: {v}")

    # Vision
    vision = profile.get("vision", {})
    print(f"\n  VISION:")
    for k, v in vision.items():
        print(f"    {k}: {v}")

    # Priorities
    priorities = profile.get("priorities", {})
    if priorities:
        print(f"\n  PRIORITAETEN:")
        for k, v in priorities.items():
            print(f"    {k}: {v}")

    # Preferences
    preferences = profile.get("preferences", {})
    if preferences:
        print(f"\n  PRAEFERENZEN:")
        for k, v in preferences.items():
            print(f"    {k}: {v}")

    # Boundaries
    boundaries = profile.get("boundaries", {})
    if boundaries:
        print(f"\n  GRENZEN (was NICHT):")
        for k, v in boundaries.items():
            print(f"    {k}: {v}")

    # Decisions
    decisions = profile.get("decisions_made", [])
    if decisions:
        print(f"\n  ENTSCHEIDUNGEN ({len(decisions)}):")
        for d in decisions[-5:]:
            if isinstance(d, str):
                print(f"    - {d[:70]}")
            elif isinstance(d, dict):
                print(f"    - {d.get('decision', str(d))[:70]}")

    # Confidence scores
    state = load_vision_state()
    confidence = state.get("confidence_scores", {})
    if confidence:
        print(f"\n  CONFIDENCE SCORES:")
        for cat, score in sorted(confidence.items(), key=lambda x: x[1], reverse=True):
            bar = "#" * int(score * 20)
            cat_name = QUESTION_CATEGORIES.get(cat, {}).get("de", cat)
            print(f"    {cat_name:25s} [{bar:20s}] {score:.0%}")

    # Knowledge gaps
    gaps = profile.get("knowledge_gaps", [])
    if gaps:
        print(f"\n  WISSENSLUECKEN:")
        for g in gaps[-5:]:
            print(f"    - {g[:70]}")

    # Stats
    print(f"\n  STATS:")
    print(f"    Profil-Updates: {profile.get('update_count', 0)}")
    print(f"    Letzte Aktualisierung: {profile.get('last_updated', 'nie')}")
    print(f"    Fragen beantwortet: {state.get('total_answers_received', 0)}")
    print()


def show_qa_history() -> None:
    """Show question/answer history."""
    history = load_qa_history()

    if not history:
        print("\n  Noch keine Fragen beantwortet.\n")
        return

    print(f"\n  Q&A HISTORY ({len(history)} Eintraege)")
    print("  " + "=" * 50)

    for entry in history[-20:]:
        date_str = entry.get("date", "N/A")[:10]
        question = entry.get("question", {})
        answer = entry.get("answer", "N/A")
        cat = question.get("category", "?")

        print(f"\n  [{date_str}] ({cat})")
        print(f"  F: {question.get('question_de', 'N/A')[:70]}")
        print(f"  A: {answer[:70]}")

    print()


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Vision Discovery Engine")
    parser.add_argument("--generate", action="store_true", help="Generate today's questions")
    parser.add_argument("--answer", action="store_true", help="Answer questions interactively")
    parser.add_argument("--profile", action="store_true", help="Show vision profile")
    parser.add_argument("--history", action="store_true", help="Show Q&A history")
    parser.add_argument("--force", action="store_true", help="Force regenerate questions")

    args = parser.parse_args()

    if args.answer:
        asyncio.run(interactive_answer_session())
    elif args.profile:
        show_profile_summary()
    elif args.history:
        show_qa_history()
    elif args.generate or args.force:
        asyncio.run(generate_daily_questions(force=args.force))
        show_todays_questions()
    else:
        show_todays_questions()


if __name__ == "__main__":
    main()
