#!/usr/bin/env python3
"""
Gemini Empire - Unified CLI fuer das gesamte Gemini Mirror System.
Spiegelt workflow_system/empire.py fuer die Gemini-Seite.

Befehle:
  status       - Gesamtstatus aller Mirror-Systeme
  workflow     - 5-Step Compound Loop auf Gemini
  cowork       - Autonomer Hintergrund-Agent
  sync         - Bidirektionaler Sync mit Main
  vision       - Vision Interrogator (Fragen generieren/beantworten)
  brain        - Dual-Brain Amplification
  questions    - Offene Fragen anzeigen
  answer       - Frage beantworten
  full         - Alles ausfuehren (Workflow + Cowork + Sync + Brain)
  cycle        - Neuen Zyklus starten
  daemon       - Alle Daemons starten
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

MIRROR_DIR = Path(__file__).parent
sys.path.insert(0, str(MIRROR_DIR))

from config import (
    STATE_DIR,
    OUTPUT_DIR,
    MIRROR_STATE_FILE,
    VISION_STATE_FILE,
    SYNC_STATE_FILE,
    DUAL_BRAIN_STATE_FILE,
    PERSONALITY_FILE,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [GEMINI-EMPIRE] %(levelname)s %(message)s",
)
logger = logging.getLogger("gemini-empire")


# === Status ===

def show_full_status():
    """Zeigt den Gesamtstatus aller Mirror-Systeme."""
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                            ║")
    print("║       ⚡ GEMINI EMPIRE - MIRROR CONTROL CENTER ⚡          ║")
    print("║                                                            ║")
    print("║       Main (Kimi/Ollama)  ←→  Mirror (Gemini)              ║")
    print("║       Dual-Brain Amplification Active                      ║")
    print("║                                                            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # 1. Mirror Orchestrator
    print("┌─── MIRROR ORCHESTRATOR ───────────────────────────────────┐")
    if MIRROR_STATE_FILE.exists():
        state = json.loads(MIRROR_STATE_FILE.read_text())
        print(f"│  Zyklus:       {state.get('cycle', 0):>5}                                │")
        print(f"│  Schritte:     {len(state.get('steps_completed', [])):>5}                                │")
        print(f"│  Patterns:     {len(state.get('patterns', [])):>5}                                │")
        print(f"│  Aktualisiert: {state.get('updated', 'N/A')[:16]:<20}               │")
    else:
        print("│  Status: Nicht initialisiert                             │")
    print("└──────────────────────────────────────────────────────────┘")

    # 2. Mirror Cowork
    cowork_file = STATE_DIR / "mirror_cowork_state.json"
    print("┌─── MIRROR COWORK ─────────────────────────────────────────┐")
    if cowork_file.exists():
        cowork = json.loads(cowork_file.read_text())
        print(f"│  Zyklen:       {cowork.get('total_cycles', 0):>5}                                │")
        print(f"│  Fokus:        {cowork.get('active_focus', 'N/A'):<10}                           │")
        print(f"│  Aktionen:     {len(cowork.get('actions_taken', [])):>5}                                │")
        print(f"│  Patterns:     {len(cowork.get('patterns_discovered', [])):>5}                                │")
        recent = cowork.get("actions_taken", [])[-3:]
        if recent:
            print("│  Letzte Aktionen:                                        │")
            for a in recent:
                title = a.get('action', '?')[:45]
                score = a.get('score', '?')
                print(f"│    [{score}/10] {title:<47}│")
    else:
        print("│  Status: Nicht initialisiert                             │")
    print("└──────────────────────────────────────────────────────────┘")

    # 3. Sync Engine
    print("┌─── SYNC ENGINE ───────────────────────────────────────────┐")
    if SYNC_STATE_FILE.exists():
        sync = json.loads(SYNC_STATE_FILE.read_text())
        print(f"│  Syncs:        {sync.get('sync_count', 0):>5}                                │")
        print(f"│  Letzter Sync: {(sync.get('last_sync', 'Nie'))[:16]:<20}               │")
        print(f"│  Konflikte:    {sync.get('conflicts_resolved', 0):>5}                                │")
    else:
        print("│  Status: Noch kein Sync durchgefuehrt                    │")
    print("└──────────────────────────────────────────────────────────┘")

    # 4. Vision Interrogator
    print("┌─── VISION INTERROGATOR ───────────────────────────────────┐")
    if VISION_STATE_FILE.exists():
        vision = json.loads(VISION_STATE_FILE.read_text())
        print(f"│  Fragen:       {vision.get('total_questions_asked', 0):>5}                                │")
        print(f"│  Antworten:    {vision.get('total_answers_received', 0):>5}                                │")
        pending = [q for q in vision.get('pending_questions', []) if not q.get('answered')]
        print(f"│  Offen:        {len(pending):>5}                                │")
    else:
        print("│  Status: Noch keine Fragen generiert                     │")

    if PERSONALITY_FILE.exists():
        profile = json.loads(PERSONALITY_FILE.read_text())
        clarity = profile.get('vision_clarity_score', 1)
        bar = "█" * int(clarity) + "░" * (10 - int(clarity))
        print(f"│  Vision-Klarheit: [{bar}] {clarity}/10              │")
        print(f"│  Praeferenzen:    {len(profile.get('known_preferences', [])):>3} bekannt                       │")
        print(f"│  Werte:           {len(profile.get('known_values', [])):>3} bekannt                       │")
    print("└──────────────────────────────────────────────────────────┘")

    # 5. Dual Brain
    print("┌─── DUAL BRAIN ────────────────────────────────────────────┐")
    if DUAL_BRAIN_STATE_FILE.exists():
        brain = json.loads(DUAL_BRAIN_STATE_FILE.read_text())
        print(f"│  Zyklen:           {brain.get('total_cycles', 0):>5}                             │")
        print(f"│  Reviews:          {brain.get('reviews_done', 0):>5}                             │")
        print(f"│  Amplifications:   {brain.get('amplifications', 0):>5}                             │")
        print(f"│  Cross-Insights:   {len(brain.get('cross_insights', [])):>5}                             │")

        history = brain.get("synergy_history", [])
        if history:
            avg = sum(h["score"] for h in history[-10:]) / min(len(history), 10)
            bar = "█" * int(avg) + "░" * (10 - int(avg))
            print(f"│  Synergy Score:    [{bar}] {avg:.1f}/10           │")
    else:
        print("│  Status: Noch kein Dual-Brain Zyklus                     │")
    print("└──────────────────────────────────────────────────────────┘")

    # 6. Outputs
    print("┌─── OUTPUTS ───────────────────────────────────────────────┐")
    if OUTPUT_DIR.exists():
        all_files = list(OUTPUT_DIR.glob("*.json"))
        print(f"│  Dateien:      {len(all_files):>5}                                │")
        recent = sorted(all_files, key=lambda f: f.stat().st_mtime, reverse=True)[:3]
        if recent:
            print("│  Neueste:                                                │")
            for f in recent:
                print(f"│    {f.name[:55]:<55}│")
    else:
        print("│  Keine Outputs vorhanden                                 │")
    print("└──────────────────────────────────────────────────────────┘")

    # 7. Offene Fragen
    if VISION_STATE_FILE.exists():
        vision = json.loads(VISION_STATE_FILE.read_text())
        pending = [q for q in vision.get('pending_questions', []) if not q.get('answered')]
        if pending:
            print()
            print("┌─── OFFENE FRAGEN AN DICH ─────────────────────────────────┐")
            for q in pending[:5]:
                qtext = q.get('question', '')[:55]
                qid = q.get('id', '?')
                print(f"│  [{qid}] {qtext:<51}│")
            if len(pending) > 5:
                print(f"│  ... und {len(pending)-5} weitere                                     │")
            print("│                                                          │")
            print("│  Beantworten: python gemini_empire.py answer Q-001 \"...\" │")
            print("└──────────────────────────────────────────────────────────┘")

    print()


# === Workflow ===

async def run_workflow(step: str = None):
    """Fuehrt den Mirror-Workflow aus."""
    from mirror_orchestrator import run_full_loop, run_single_step

    if step:
        await run_single_step(step)
    else:
        await run_full_loop()


# === Cowork ===

async def run_cowork(daemon: bool = False, interval: int = 1800, focus: str = "revenue"):
    """Startet den Mirror-Cowork Agent."""
    from mirror_cowork import MirrorCowork, run_daemon

    if daemon:
        await run_daemon(interval, focus)
    else:
        cowork = MirrorCowork(focus=focus)
        await cowork.run_cycle()


# === Sync ===

async def run_sync(daemon: bool = False, interval: int = 900):
    """Fuehrt Sync durch."""
    from sync_engine import SyncEngine, run_sync_daemon

    if daemon:
        await run_sync_daemon(interval)
    else:
        engine = SyncEngine()
        result = await engine.full_sync()
        print(json.dumps(result, indent=2, ensure_ascii=False))


# === Vision ===

async def run_vision(action: str, **kwargs):
    """Vision Interrogator Befehle."""
    from vision_interrogator import VisionInterrogator

    vi = VisionInterrogator()

    if action == "generate":
        questions = await vi.generate_daily_questions(
            focus=kwargs.get("focus"),
            count=kwargs.get("count", 5),
            depth=kwargs.get("depth", "medium"),
        )
        print(f"\n{len(questions)} Fragen generiert:\n")
        for q in questions:
            print(f"  [{q['id']}] ({q.get('category', '?')}, {q.get('depth', '?')})")
            print(f"    {q['question']}")
            print()

    elif action == "answer":
        result = await vi.process_answer(
            kwargs.get("question_id", ""),
            kwargs.get("answer_text", ""),
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif action == "summary":
        summary = await vi.generate_vision_summary()
        print(json.dumps(summary, indent=2, ensure_ascii=False))

    elif action == "status":
        vi.show_status()

    elif action == "pending":
        questions = vi.get_pending_questions()
        if not questions:
            print("Keine offenen Fragen.")
        else:
            for q in questions:
                print(f"\n  [{q.get('id', '?')}] ({q.get('category', '?')})")
                print(f"    {q.get('question', '')}")


# === Brain ===

async def run_brain(action: str = "cycle", daemon: bool = False, interval: int = 3600):
    """Dual-Brain Befehle."""
    from dual_brain import DualBrain, run_dual_brain_daemon

    if daemon:
        await run_dual_brain_daemon(interval)
        return

    brain = DualBrain()

    if action == "cycle":
        await brain.full_cycle()
    elif action == "review":
        await brain.review_main_output()
    elif action == "amplify":
        await brain.amplify()
    elif action == "compete":
        await brain.competitive_analysis()
    elif action == "status":
        brain.show_status()


# === Full Run ===

async def run_full():
    """Fuehrt alles nacheinander aus."""
    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║    GEMINI EMPIRE - FULL EXECUTION        ║")
    logger.info("╚══════════════════════════════════════════╝")

    # 1. Sync
    logger.info("\n=== Phase 1: SYNC ===")
    from sync_engine import SyncEngine
    engine = SyncEngine()
    await engine.full_sync()

    # 2. Workflow
    logger.info("\n=== Phase 2: WORKFLOW ===")
    from mirror_orchestrator import run_full_loop
    await run_full_loop()

    # 3. Cowork
    logger.info("\n=== Phase 3: COWORK ===")
    from mirror_cowork import MirrorCowork
    cowork = MirrorCowork()
    await cowork.run_cycle()

    # 4. Brain
    logger.info("\n=== Phase 4: DUAL-BRAIN ===")
    from dual_brain import DualBrain
    brain = DualBrain()
    await brain.full_cycle()

    # 5. Vision
    logger.info("\n=== Phase 5: VISION QUESTIONS ===")
    from vision_interrogator import VisionInterrogator
    vi = VisionInterrogator()
    await vi.generate_daily_questions(count=3)

    # 6. Final Sync
    logger.info("\n=== Phase 6: FINAL SYNC ===")
    await engine.full_sync()

    logger.info("\n✓ FULL EXECUTION ABGESCHLOSSEN")


# === All Daemons ===

async def run_all_daemons():
    """Startet alle Daemons gleichzeitig."""
    logger.info("Starte alle Daemons...")

    from sync_engine import run_sync_daemon
    from mirror_cowork import run_daemon as cowork_daemon
    from dual_brain import run_dual_brain_daemon

    await asyncio.gather(
        run_sync_daemon(900),           # Sync alle 15 Min
        cowork_daemon(1800, "revenue"),  # Cowork alle 30 Min
        run_dual_brain_daemon(3600),    # Brain jede Stunde
    )


# === CLI ===

def main():
    parser = argparse.ArgumentParser(
        description="Gemini Empire - Mirror Control Center",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python gemini_empire.py status                    # Gesamtstatus
  python gemini_empire.py workflow                  # 5-Step Loop
  python gemini_empire.py workflow --step audit     # Einzelner Schritt
  python gemini_empire.py cowork --focus revenue    # Cowork-Zyklus
  python gemini_empire.py cowork --daemon           # Cowork-Daemon
  python gemini_empire.py sync                      # Einmal synchronisieren
  python gemini_empire.py vision generate           # Fragen generieren
  python gemini_empire.py questions                 # Offene Fragen
  python gemini_empire.py answer Q-001 "Antwort"   # Frage beantworten
  python gemini_empire.py brain                     # Dual-Brain Zyklus
  python gemini_empire.py full                      # Alles ausfuehren
  python gemini_empire.py cycle                     # Neuer Zyklus
  python gemini_empire.py daemon                    # Alle Daemons
        """,
    )

    subparsers = parser.add_subparsers(dest="command")

    # status
    subparsers.add_parser("status", help="Gesamtstatus anzeigen")

    # workflow
    wf = subparsers.add_parser("workflow", help="5-Step Compound Loop")
    wf.add_argument("--step", choices=["audit", "architect", "analyst", "refinery", "compounder"])

    # cowork
    cw = subparsers.add_parser("cowork", help="Autonomer Cowork Agent")
    cw.add_argument("--daemon", action="store_true")
    cw.add_argument("--interval", type=int, default=1800)
    cw.add_argument("--focus", choices=["revenue", "content", "automation", "product", "mirror"], default="revenue")

    # sync
    sy = subparsers.add_parser("sync", help="Bidirektionaler Sync")
    sy.add_argument("--daemon", action="store_true")
    sy.add_argument("--interval", type=int, default=900)

    # vision
    vi = subparsers.add_parser("vision", help="Vision Interrogator")
    vi.add_argument("action", choices=["generate", "answer", "summary", "status", "pending"])
    vi.add_argument("--focus", type=str)
    vi.add_argument("--depth", choices=["surface", "medium", "deep"], default="medium")
    vi.add_argument("--count", type=int, default=5)

    # questions (shortcut)
    subparsers.add_parser("questions", help="Offene Fragen anzeigen")

    # answer (shortcut)
    ans = subparsers.add_parser("answer", help="Frage beantworten")
    ans.add_argument("question_id", help="Fragen-ID (z.B. Q-001)")
    ans.add_argument("answer_text", help="Deine Antwort")

    # brain
    br = subparsers.add_parser("brain", help="Dual-Brain Amplification")
    br.add_argument("action", nargs="?", default="cycle", choices=["cycle", "review", "amplify", "compete", "status"])
    br.add_argument("--daemon", action="store_true")
    br.add_argument("--interval", type=int, default=3600)

    # full
    subparsers.add_parser("full", help="Alles ausfuehren")

    # cycle
    subparsers.add_parser("cycle", help="Neuen Zyklus starten")

    # daemon
    subparsers.add_parser("daemon", help="Alle Daemons starten")

    args = parser.parse_args()

    if not args.command or args.command == "status":
        show_full_status()

    elif args.command == "workflow":
        asyncio.run(run_workflow(args.step))

    elif args.command == "cowork":
        asyncio.run(run_cowork(args.daemon, args.interval, args.focus))

    elif args.command == "sync":
        asyncio.run(run_sync(args.daemon, args.interval))

    elif args.command == "vision":
        if args.action == "answer":
            print("Verwende: python gemini_empire.py answer <ID> \"<Antwort>\"")
        else:
            asyncio.run(run_vision(args.action, focus=args.focus, count=args.count, depth=args.depth))

    elif args.command == "questions":
        asyncio.run(run_vision("pending"))

    elif args.command == "answer":
        asyncio.run(run_vision("answer", question_id=args.question_id, answer_text=args.answer_text))

    elif args.command == "brain":
        asyncio.run(run_brain(args.action, args.daemon, args.interval))

    elif args.command == "full":
        asyncio.run(run_full())

    elif args.command == "cycle":
        from mirror_orchestrator import advance_cycle
        new_cycle = advance_cycle()
        print(f"Neuer Zyklus gestartet: {new_cycle}")

    elif args.command == "daemon":
        asyncio.run(run_all_daemons())


if __name__ == "__main__":
    main()
