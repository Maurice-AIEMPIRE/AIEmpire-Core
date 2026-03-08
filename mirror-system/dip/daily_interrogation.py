#!/usr/bin/env python3
"""
DAILY INTERROGATION PROTOCOL (DIP) - Vision-Motor

Stellt dir jeden Tag gezielte Fragen, um deine Vision zu schärfen.
Speichert Antworten in vision_state.json + decisions_log.jsonl.
Generiert task_orders.md für beide Systeme (Mac + Cloud).

Usage:
  python daily_interrogation.py morning    # Morgen-Fragen (10 Fragen)
  python daily_interrogation.py evening    # Abend-Fragen (3 Fragen)
  python daily_interrogation.py status     # Zeige aktuellen Vision-Stand
  python daily_interrogation.py history    # Zeige Entscheidungs-History
  python daily_interrogation.py generate   # Generiere adaptive Fragen (Ollama)
"""

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

DIP_DIR = Path(__file__).parent
VISION_FILE = DIP_DIR / "vision_state.json"
DECISIONS_LOG = DIP_DIR / "decisions_log.jsonl"
TASK_ORDERS = DIP_DIR / "task_orders.md"
TEMPLATES_DIR = DIP_DIR / "templates"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
FAST_MODEL = "llama3.1:8b"


# ── QUESTION TEMPLATES ──────────────────────────────────────────────

MORNING_QUESTIONS = [
    # Block A – Vision
    {
        "id": "vision_one_output",
        "block": "A_VISION",
        "question": "Was ist heute der EINE Output, der dich real weiterbringt?",
        "type": "text",
        "maps_to": "daily_focus",
    },
    {
        "id": "vision_three_wins",
        "block": "A_VISION",
        "question": "Welche 3 Dinge wären heute ein 'Sieg'?",
        "type": "list_3",
        "maps_to": "daily_wins",
    },
    {
        "id": "vision_not_happen",
        "block": "A_VISION",
        "question": "Was darf heute NICHT passieren?",
        "type": "text",
        "maps_to": "daily_avoid",
    },
    # Block B – Prioritäten
    {
        "id": "prio_main_fronts",
        "block": "B_PRIORITIES",
        "question": "Welche 2 Projekte sind die 'Hauptfronten'?",
        "type": "list_2",
        "maps_to": "main_fronts",
    },
    {
        "id": "prio_biggest_block",
        "block": "B_PRIORITIES",
        "question": "Was ist aktuell die größte Blockade?",
        "type": "text",
        "maps_to": "biggest_blocker",
    },
    {
        "id": "prio_60min",
        "block": "B_PRIORITIES",
        "question": "Wenn du nur 60 Minuten hättest: worauf?",
        "type": "text",
        "maps_to": "sixty_min_focus",
    },
    # Block C – Regeln & Stil
    {
        "id": "style_risk",
        "block": "C_STYLE",
        "question": "Mehr Risiko oder mehr Stabilität – heute?",
        "type": "choice",
        "choices": ["risiko", "stabilität", "balanced"],
        "maps_to": "risk_mode",
    },
    {
        "id": "style_comm",
        "block": "C_STYLE",
        "question": "Welche Kommunikation heute? (hart/knapp/freundlich/ausführlich)",
        "type": "choice",
        "choices": ["hart", "knapp", "freundlich", "ausführlich"],
        "maps_to": "communication_style",
    },
    {
        "id": "style_noise",
        "block": "C_STYLE",
        "question": "Was soll das System ignorieren (Noise)?",
        "type": "text",
        "maps_to": "ignore_list",
    },
    # Block D – Kontext
    {
        "id": "context_new",
        "block": "D_CONTEXT",
        "question": "Neue Infos? (Anwalt/Kunden/Finanzen/Gesundheit/Familie)",
        "type": "text",
        "maps_to": "new_context",
    },
]

EVENING_QUESTIONS = [
    {
        "id": "review_time_cost",
        "block": "E_REVIEW",
        "question": "Was hat dich heute am meisten Zeit gekostet?",
        "type": "text",
        "maps_to": "time_sinks",
    },
    {
        "id": "review_bad_decision",
        "block": "E_REVIEW",
        "question": "Welche Entscheidung war falsch oder zu langsam?",
        "type": "text",
        "maps_to": "bad_decisions",
    },
    {
        "id": "review_prepare",
        "block": "E_REVIEW",
        "question": "Welche Aufgabe soll morgen automatisch vorbereitet sein?",
        "type": "text",
        "maps_to": "prepare_tomorrow",
    },
]


# ── CORE FUNCTIONS ──────────────────────────────────────────────────

def load_vision_state() -> dict:
    """Load current vision state."""
    if VISION_FILE.exists():
        try:
            return json.loads(VISION_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "updated": None,
        "sessions_completed": 0,
        "vision": {},
        "priorities": {},
        "style": {},
        "context": {},
        "review": {},
        "meta": {
            "streak_days": 0,
            "last_session_date": None,
        },
    }


def save_vision_state(state: dict):
    """Save vision state to file."""
    state["updated"] = datetime.now().isoformat()
    VISION_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def log_decision(question_id: str, question: str, answer: str):
    """Append to decisions log (JSONL, append-only)."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "question_id": question_id,
        "question": question,
        "answer": answer,
    }
    with open(DECISIONS_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def ask_question(q: dict) -> str:
    """Ask a single question and get user input."""
    print(f"\n  [{q['block']}]")
    print(f"  {q['question']}")

    if q.get("type") == "choice" and q.get("choices"):
        for i, c in enumerate(q["choices"], 1):
            print(f"    {i}) {c}")
        print()

    answer = input("  → ").strip()

    if q.get("type") == "choice" and q.get("choices"):
        try:
            idx = int(answer) - 1
            if 0 <= idx < len(q["choices"]):
                answer = q["choices"][idx]
        except ValueError:
            pass

    return answer


def run_session(questions: list, session_type: str):
    """Run an interrogation session."""
    state = load_vision_state()
    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"  DAILY INTERROGATION PROTOCOL - {session_type.upper()}")
    print(f"  {date_str}")
    print(f"  Session #{state['sessions_completed'] + 1}")
    print(f"{'='*60}")

    if session_type == "morning":
        print("\n  10 Fragen. Kurze Antworten reichen. Los geht's.\n")
    else:
        print("\n  3 Fragen. Tagesreview. Ehrlich sein.\n")

    answers = {}
    for q in questions:
        answer = ask_question(q)
        if answer:
            answers[q["maps_to"]] = answer
            log_decision(q["id"], q["question"], answer)

    # Update vision state
    mapping = {
        "A_VISION": "vision",
        "B_PRIORITIES": "priorities",
        "C_STYLE": "style",
        "D_CONTEXT": "context",
        "E_REVIEW": "review",
    }

    for q in questions:
        block_key = mapping.get(q["block"], "context")
        if q["maps_to"] in answers:
            state[block_key][q["maps_to"]] = answers[q["maps_to"]]

    # Update meta
    last_date = state["meta"].get("last_session_date")
    if last_date == date_str:
        pass  # Same day, don't increment streak
    elif last_date == (datetime.now().replace(day=datetime.now().day - 1)).strftime("%Y-%m-%d"):
        state["meta"]["streak_days"] += 1
    else:
        state["meta"]["streak_days"] = 1

    state["meta"]["last_session_date"] = date_str
    state["sessions_completed"] += 1

    save_vision_state(state)
    generate_task_orders(state)

    print(f"\n{'='*60}")
    print("  Session gespeichert.")
    print(f"  Streak: {state['meta']['streak_days']} Tage")
    print("  → vision_state.json aktualisiert")
    print("  → task_orders.md generiert")
    print(f"{'='*60}\n")


def generate_task_orders(state: dict):
    """Generate task_orders.md from current vision state."""
    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# TASK ORDERS - {date_str}",
        f"Generated: {datetime.now().strftime('%H:%M')}",
        "",
        "## FOCUS",
        f"- **Hauptfokus:** {state.get('vision', {}).get('daily_focus', 'nicht gesetzt')}",
        f"- **Hauptfronten:** {state.get('priorities', {}).get('main_fronts', 'nicht gesetzt')}",
        f"- **60-Min-Fokus:** {state.get('priorities', {}).get('sixty_min_focus', 'nicht gesetzt')}",
        "",
        "## SIEGE HEUTE",
    ]

    wins = state.get("vision", {}).get("daily_wins", "")
    if isinstance(wins, str):
        for w in wins.split(","):
            lines.append(f"- [ ] {w.strip()}")
    elif isinstance(wins, list):
        for w in wins:
            lines.append(f"- [ ] {w}")

    lines.extend([
        "",
        "## BLOCKER",
        f"- {state.get('priorities', {}).get('biggest_blocker', 'keiner')}",
        "",
        "## VERMEIDEN",
        f"- {state.get('vision', {}).get('daily_avoid', 'nichts')}",
        "",
        "## MODUS",
        f"- Risiko: {state.get('style', {}).get('risk_mode', 'balanced')}",
        f"- Kommunikation: {state.get('style', {}).get('communication_style', 'knapp')}",
        f"- Ignorieren: {state.get('style', {}).get('ignore_list', 'nichts')}",
        "",
        "## NEUER KONTEXT",
        f"- {state.get('context', {}).get('new_context', 'keiner')}",
        "",
        "## REVIEW (Vortag)",
        f"- Zeitfresser: {state.get('review', {}).get('time_sinks', '-')}",
        f"- Schlechte Entscheidung: {state.get('review', {}).get('bad_decisions', '-')}",
        f"- Morgen vorbereiten: {state.get('review', {}).get('prepare_tomorrow', '-')}",
        "",
        "---",
        f"*Streak: {state.get('meta', {}).get('streak_days', 0)} Tage | "
        f"Sessions: {state.get('sessions_completed', 0)}*",
    ])

    TASK_ORDERS.write_text("\n".join(lines))


def generate_adaptive_questions(state: dict) -> list:
    """Use Ollama to generate context-aware follow-up questions."""
    prompt = f"""Du bist der Vision-Motor für Maurice's AI Empire.
Aktuelle Vision: {json.dumps(state.get('vision', {}), ensure_ascii=False)}
Aktuelle Prioritäten: {json.dumps(state.get('priorities', {}), ensure_ascii=False)}
Aktueller Kontext: {json.dumps(state.get('context', {}), ensure_ascii=False)}
Review: {json.dumps(state.get('review', {}), ensure_ascii=False)}

Generiere 5 ultra-gezielte Folgefragen, die Maurice ZWINGEN, konkreter zu werden.
Keine generischen Fragen. Jede Frage muss eine Entscheidung erzwingen.
Format: Nummerierte Liste, 1 Frage pro Zeile."""

    try:
        result = subprocess.run(
            ["curl", "-s", f"{OLLAMA_HOST}/api/generate",
             "-d", json.dumps({"model": FAST_MODEL, "prompt": prompt, "stream": False})],
            capture_output=True, text=True, timeout=60
        )
        response = json.loads(result.stdout)
        return response.get("response", "Keine Fragen generiert.").split("\n")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return ["[Ollama nicht erreichbar - adaptive Fragen nicht verfügbar]"]


def show_status():
    """Show current vision state."""
    state = load_vision_state()

    print(f"\n{'='*60}")
    print("  VISION STATE")
    print(f"{'='*60}")
    print(f"  Sessions: {state.get('sessions_completed', 0)}")
    print(f"  Streak:   {state.get('meta', {}).get('streak_days', 0)} Tage")
    print(f"  Updated:  {state.get('updated', 'nie')}")
    print()

    for section in ["vision", "priorities", "style", "context", "review"]:
        data = state.get(section, {})
        if data:
            print(f"  [{section.upper()}]")
            for k, v in data.items():
                print(f"    {k}: {v}")
            print()


def show_history(n: int = 20):
    """Show recent decisions from log."""
    if not DECISIONS_LOG.exists():
        print("  Keine Entscheidungen bisher.")
        return

    print(f"\n{'='*60}")
    print("  ENTSCHEIDUNGS-HISTORY (letzte {n})")
    print(f"{'='*60}\n")

    lines = DECISIONS_LOG.read_text().strip().split("\n")
    for line in lines[-n:]:
        try:
            entry = json.loads(line)
            ts = entry.get("timestamp", "?")[:16]
            q = entry.get("question", "?")[:50]
            a = entry.get("answer", "?")[:50]
            print(f"  [{ts}] {q}")
            print(f"           → {a}\n")
        except json.JSONDecodeError:
            pass


def main():
    parser = argparse.ArgumentParser(description="Daily Interrogation Protocol (DIP)")
    parser.add_argument("command", choices=["morning", "evening", "status", "history", "generate"],
                       help="Which session to run")
    parser.add_argument("--count", type=int, default=20, help="History entries to show")
    args = parser.parse_args()

    if args.command == "morning":
        run_session(MORNING_QUESTIONS, "morning")
    elif args.command == "evening":
        run_session(EVENING_QUESTIONS, "evening")
    elif args.command == "status":
        show_status()
    elif args.command == "history":
        show_history(args.count)
    elif args.command == "generate":
        state = load_vision_state()
        questions = generate_adaptive_questions(state)
        print("\n  ADAPTIVE FRAGEN:\n")
        for q in questions:
            if q.strip():
                print(f"  {q}")
        print()


if __name__ == "__main__":
    main()
