#!/usr/bin/env python3
"""
Setup-Script fuer das Gemini Mirror System.
Initialisiert alle State-Dateien, Verzeichnisse und Fallback-Daten.
Kann ohne API-Key ausgefuehrt werden.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

MIRROR_DIR = Path(__file__).parent
sys.path.insert(0, str(MIRROR_DIR))

from config import (
    STATE_DIR, OUTPUT_DIR, HISTORY_DIR, MEMORY_DIR,
    MIRROR_STATE_FILE, VISION_STATE_FILE, SYNC_STATE_FILE,
    DUAL_BRAIN_STATE_FILE, QUESTION_LOG_FILE,
    VISION_MEMORY_FILE, PATTERN_CROSS_FILE, PERSONALITY_FILE,
)


def init_directories():
    """Erstellt alle benoetigten Verzeichnisse."""
    dirs = [STATE_DIR, OUTPUT_DIR, HISTORY_DIR, MEMORY_DIR, OUTPUT_DIR / "deliverables"]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  [OK] {d}")


def init_state_file(path: Path, default_data: dict, name: str):
    """Initialisiert eine State-Datei wenn sie nicht existiert."""
    if path.exists():
        print(f"  [SKIP] {name} existiert bereits")
        return
    path.write_text(json.dumps(default_data, indent=2, ensure_ascii=False))
    print(f"  [INIT] {name}")


def init_all_states():
    """Initialisiert alle State-Dateien."""
    now = datetime.now().isoformat()

    # Mirror State
    init_state_file(MIRROR_STATE_FILE, {
        "created": now,
        "updated": now,
        "cycle": 1,
        "steps_completed": [],
        "context": {},
        "patterns": [],
        "improvements": [],
    }, "Mirror Orchestrator State")

    # Vision State
    init_state_file(VISION_STATE_FILE, {
        "created": now,
        "updated": now,
        "total_questions_asked": 0,
        "total_answers_received": 0,
        "answers": [],
        "pending_questions": [],
        "daily_stats": {},
    }, "Vision Interrogator State")

    # Sync State
    init_state_file(SYNC_STATE_FILE, {
        "created": now,
        "updated": now,
        "last_sync": None,
        "sync_count": 0,
        "conflicts_resolved": 0,
        "bytes_transferred": 0,
        "sync_history": [],
    }, "Sync Engine State")

    # Dual Brain State
    init_state_file(DUAL_BRAIN_STATE_FILE, {
        "created": now,
        "updated": now,
        "total_cycles": 0,
        "reviews_done": 0,
        "amplifications": 0,
        "competitive_analyses": 0,
        "cross_insights": [],
        "improvement_queue": [],
        "synergy_history": [],
    }, "Dual Brain State")

    # Question Log
    init_state_file(QUESTION_LOG_FILE, [], "Question Log")

    # Cowork State
    cowork_file = STATE_DIR / "mirror_cowork_state.json"
    init_state_file(cowork_file, {
        "created": now,
        "updated": now,
        "total_cycles": 0,
        "active_focus": "revenue",
        "actions_taken": [],
        "patterns_discovered": [],
        "pending_recommendations": [],
        "messages_for_main": [],
    }, "Mirror Cowork State")


def init_memory():
    """Initialisiert Memory-Dateien."""
    # Vision Memory
    init_state_file(VISION_MEMORY_FILE, {
        "entries": [],
        "summary": {},
        "last_updated": datetime.now().isoformat(),
        "total_entries": 0,
    }, "Vision Memory")

    # Cross Patterns
    init_state_file(PATTERN_CROSS_FILE, [], "Cross Patterns Library")

    # Maurice Profile
    init_state_file(PERSONALITY_FILE, {
        "name": "Maurice Pfeifer",
        "age": 37,
        "expertise": "Elektrotechnikmeister, 16 Jahre BMA (Brandmeldeanlagen)",
        "primary_goal": "100 Mio EUR in 1-3 Jahren, alles automatisiert mit AI",
        "known_preferences": [],
        "known_values": [],
        "known_blockers": ["Revenue = 0 EUR", "Keine Fiverr Gigs live", "Telegram Bot Token invalid"],
        "vision_clarity_score": 1,
        "total_answers": 0,
        "personality_traits": ["ambitioniert", "technisch-versiert", "automatisierungs-fokussiert"],
        "decision_patterns": [],
        "updated": datetime.now().isoformat(),
    }, "Maurice Profile")


def init_fallback_questions():
    """Generiert Starter-Fragen ohne API-Key."""
    state = json.loads(VISION_STATE_FILE.read_text()) if VISION_STATE_FILE.exists() else {}

    if state.get("pending_questions"):
        print("  [SKIP] Fragen existieren bereits")
        return

    starter_questions = [
        {
            "id": "Q-001",
            "question": "Was ist dein ULTIMATIVES Ziel in 12 Monaten - nicht finanziell, sondern wie soll dein LEBEN aussehen?",
            "category": "vision",
            "depth": "deep",
            "purpose": "Kernvision jenseits von Geld verstehen",
            "expected_insight": "Lebensvorstellung und wahre Motivation",
            "generated_at": datetime.now().isoformat(),
            "answered": False,
            "source": "setup_init",
        },
        {
            "id": "Q-002",
            "question": "Welcher Revenue-Kanal ist fuer DICH am einfachsten zu starten - Gumroad Produkte, Fiverr Services, oder BMA+AI Consulting?",
            "category": "strategy",
            "depth": "medium",
            "purpose": "Schnellsten Weg zum ersten Umsatz finden",
            "expected_insight": "Praeferenz und Selbsteinschaetzung",
            "generated_at": datetime.now().isoformat(),
            "answered": False,
            "source": "setup_init",
        },
        {
            "id": "Q-003",
            "question": "Hast du schon ein konkretes Produkt im Kopf das du auf Gumroad verkaufen koenntest? Wenn ja, welches?",
            "category": "priorities",
            "depth": "medium",
            "purpose": "Konkretes erstes Produkt identifizieren",
            "expected_insight": "Produktideen und Marktverstaendnis",
            "generated_at": datetime.now().isoformat(),
            "answered": False,
            "source": "setup_init",
        },
        {
            "id": "Q-004",
            "question": "Wieviele Stunden pro Tag kannst/willst du SELBST aktiv am Empire arbeiten? Und was davon ist AI-delegierbar?",
            "category": "preferences",
            "depth": "medium",
            "purpose": "Verfuegbare Kapazitaet und Delegationsbereitschaft",
            "expected_insight": "Arbeitsbudget und Automatisierungsgrad",
            "generated_at": datetime.now().isoformat(),
            "answered": False,
            "source": "setup_init",
        },
        {
            "id": "Q-005",
            "question": "Was ist gerade dein GROESSTER Frust mit dem AIEmpire System? Was funktioniert nicht wie gewollt?",
            "category": "blockers",
            "depth": "deep",
            "purpose": "Hauptblocker und Schmerzpunkte identifizieren",
            "expected_insight": "Wo der Schuh drueckt",
            "generated_at": datetime.now().isoformat(),
            "answered": False,
            "source": "setup_init",
        },
    ]

    state["pending_questions"] = starter_questions
    state["total_questions_asked"] = len(starter_questions)
    VISION_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    print(f"  [INIT] {len(starter_questions)} Starter-Fragen generiert")


def check_api_key():
    """Prueft ob Gemini API Key gesetzt ist."""
    key = os.getenv("GEMINI_API_KEY", "")
    if key:
        print(f"  [OK] GEMINI_API_KEY gesetzt ({key[:8]}...)")
        return True
    else:
        print("  [WARN] GEMINI_API_KEY NICHT gesetzt!")
        print("         Hol dir einen Key: https://aistudio.google.com/apikey")
        print("         Dann: export GEMINI_API_KEY='dein-key'")
        print("         Oder: cp .env.example .env && nano .env && source .env")
        return False


def main():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║    GEMINI MIRROR - SETUP & INITIALIZATION           ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    print("1. Verzeichnisse erstellen...")
    init_directories()

    print("\n2. State-Dateien initialisieren...")
    init_all_states()

    print("\n3. Memory-Dateien initialisieren...")
    init_memory()

    print("\n4. Starter-Fragen generieren...")
    init_fallback_questions()

    print("\n5. API-Key pruefen...")
    has_key = check_api_key()

    print("\n══════════════════════════════════════════════════════")
    print("  SETUP ABGESCHLOSSEN!")
    print()
    if has_key:
        print("  System ist VOLL EINSATZBEREIT.")
        print()
        print("  Naechste Schritte:")
        print("    python gemini-mirror/gemini_empire.py status")
        print("    python gemini-mirror/gemini_empire.py full")
    else:
        print("  System ist OFFLINE initialisiert.")
        print("  Fragen sind bereit - du kannst sie schon beantworten!")
        print()
        print("  JETZT:")
        print("    1. Gemini API Key holen (kostenlos!):")
        print("       https://aistudio.google.com/apikey")
        print()
        print("    2. Key setzen:")
        print("       export GEMINI_API_KEY='AIza...'")
        print()
        print("    3. System starten:")
        print("       python gemini-mirror/gemini_empire.py full")
    print()


if __name__ == "__main__":
    main()
