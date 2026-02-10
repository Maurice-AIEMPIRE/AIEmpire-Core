#!/usr/bin/env python3
"""
AI EMPIRE - Unified Control Center
Ein Kommando fuer alle Systeme.

Usage:
  python empire.py status              # Gesamtstatus aller Systeme
  python empire.py workflow             # 5-Step Loop ausfuehren
  python empire.py workflow --step audit
  python empire.py cowork               # Ein Cowork-Zyklus
  python empire.py cowork --daemon      # Cowork Daemon starten
  python empire.py guard                # Resource Guard Status
  python empire.py cycle                # Neuen Wochen-Zyklus starten
  python empire.py full                 # Workflow + Cowork nacheinander
  python empire.py gemini status        # Gemini Mirror Status
  python empire.py gemini questions     # Vision Discovery Fragen
  python empire.py gemini evolve        # Cross-System Evolution
  python empire.py gemini daemon        # Gemini Mirror Daemon
"""

import asyncio
import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path

EMPIRE_ROOT = Path(__file__).parent.parent
WORKFLOW_DIR = Path(__file__).parent
GEMINI_DIR = EMPIRE_ROOT / "gemini-mirror"

sys.path.insert(0, str(WORKFLOW_DIR))
sys.path.insert(0, str(GEMINI_DIR))


def show_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ██████╗ ██╗    ███████╗███╗   ███╗██████╗ ██╗██████╗    ║
║    ██╔══██╗██║    ██╔════╝████╗ ████║██╔══██╗██║██╔══██╗   ║
║    ███████║██║    █████╗  ██╔████╔██║██████╔╝██║██████╔╝   ║
║    ██╔══██║██║    ██╔══╝  ██║╚██╔╝██║██╔═══╝ ██║██╔══██╗   ║
║    ██║  ██║██║    ███████╗██║ ╚═╝ ██║██║     ██║██║  ██║   ║
║    ╚═╝  ╚═╝╚═╝    ╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝   ║
║                                                              ║
║    Control Center - Maurice Pfeifer                          ║
║    {date}                                        ║
╚══════════════════════════════════════════════════════════════╝
    """.format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


def show_full_status():
    """Zeige Status aller Subsysteme."""
    show_banner()

    # 1. Resource Guard
    from resource_guard import ResourceGuard
    guard = ResourceGuard()
    status = guard.get_status()
    print(f"  RESOURCES: {guard.format_status()}")
    print()

    # 2. Workflow System
    state_file = WORKFLOW_DIR / "state" / "current_state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text())
        cycle = state.get("cycle", 0)
        steps = len(state.get("steps_completed", []))
        patterns = len(state.get("patterns", []))
        updated = state.get("updated", "never")
        print(f"  WORKFLOW:")
        print(f"    Cycle:    #{cycle}")
        print(f"    Steps:    {steps} completed")
        print(f"    Patterns: {patterns} in library")
        print(f"    Updated:  {updated}")

        if state.get("steps_completed"):
            print(f"    Recent:")
            for s in state["steps_completed"][-3:]:
                summary = s.get("summary", "")[:60]
                print(f"      [{s['step'].upper():12s}] {summary}")
    else:
        print(f"  WORKFLOW: Not initialized")
        print(f"    Run: python empire.py workflow")
    print()

    # 3. Cowork Engine
    cowork_file = WORKFLOW_DIR / "state" / "cowork_state.json"
    if cowork_file.exists():
        cw = json.loads(cowork_file.read_text())
        print(f"  COWORK:")
        print(f"    Cycles:   {cw.get('total_cycles', 0)}")
        print(f"    Focus:    {cw.get('active_focus', 'N/A')}")
        print(f"    Actions:  {len(cw.get('actions_taken', []))}")
        print(f"    Patterns: {len(cw.get('patterns_discovered', []))}")
        print(f"    Updated:  {cw.get('updated', 'never')}")

        pending = cw.get("pending_recommendations", [])
        if pending:
            print(f"    Pending:")
            for p in pending[:3]:
                print(f"      - {p.get('title', 'N/A')[:50]}")
    else:
        print(f"  COWORK: Not started")
        print(f"    Run: python empire.py cowork")
    print()

    # 4. Output Inventory
    output_dirs = {
        "Workflow outputs": WORKFLOW_DIR / "output",
        "Cowork outputs": WORKFLOW_DIR / "cowork_output",
        "Swarm outputs": EMPIRE_ROOT / "kimi-swarm" / "output_500k",
        "Reactor reports": EMPIRE_ROOT / "atomic-reactor" / "reports",
    }

    print(f"  OUTPUT INVENTORY:")
    for name, path in output_dirs.items():
        if path.exists():
            files = list(path.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            print(f"    {name:20s}: {len(files):4d} files ({total_size/1024:.0f} KB)")
        else:
            print(f"    {name:20s}: (not created)")
    print()

    # 5. Gemini Mirror
    gemini_state = GEMINI_DIR / "state" / "memory.json"
    if gemini_state.exists():
        try:
            sys.path.insert(0, str(GEMINI_DIR))
            from digital_memory import DigitalMemory
            mem = DigitalMemory()
            mem_stats = mem.stats()
            print(f"  GEMINI MIRROR:")
            print(f"    Memories:  {mem_stats['total_memories']}")
            print(f"    High conf: {mem_stats['high_confidence']}")
            print(f"    Gaps:      {len(mem_stats['gaps'])}")

            # Check pending questions
            q_file = GEMINI_DIR / "state" / "vision_questions.json"
            if q_file.exists():
                qs = json.loads(q_file.read_text())
                pending = [q for q in qs if not q.get("answered")]
                print(f"    Questions: {len(pending)} pending")
        except Exception as e:
            print(f"  GEMINI MIRROR: Error - {e}")
    else:
        print(f"  GEMINI MIRROR: Not initialized")
        print(f"    Run: python empire.py gemini seed")
    print()

    # 6. Git Status
    import subprocess
    try:
        branch = subprocess.check_output(
            ["git", "-C", str(EMPIRE_ROOT), "branch", "--show-current"],
            text=True, timeout=5
        ).strip()
        uncommitted = subprocess.check_output(
            ["git", "-C", str(EMPIRE_ROOT), "status", "--porcelain"],
            text=True, timeout=5
        ).strip()
        changes = len(uncommitted.split("\n")) if uncommitted else 0
        print(f"  GIT: {branch} | {changes} uncommitted changes")
    except (subprocess.SubprocessError, FileNotFoundError):
        print(f"  GIT: (could not read)")
    print()

    # 7. Quick Commands
    print(f"  COMMANDS:")
    print(f"    python empire.py workflow          # Run 5-step loop")
    print(f"    python empire.py cowork --daemon   # Start background agent")
    print(f"    python empire.py gemini questions   # Vision discovery")
    print(f"    python empire.py gemini daemon      # Gemini mirror daemon")
    print(f"    python empire.py cycle             # New weekly cycle")
    print(f"    python empire.py full              # Workflow + Cowork")
    print()


async def run_workflow(args):
    """Run the 5-step workflow orchestrator."""
    from orchestrator import run_full_loop, run_step, run_refinery_loop, show_status
    from state.context import advance_cycle

    if hasattr(args, "new_cycle") and args.new_cycle:
        cycle = advance_cycle()
        print(f"New cycle started: #{cycle}")
        return

    if hasattr(args, "step") and args.step:
        if args.step == "refinery":
            await run_refinery_loop()
        else:
            await run_step(args.step)
    else:
        await run_full_loop()


async def run_cowork(args):
    """Run the cowork engine."""
    from cowork import run_cycle, run_daemon, show_status as cowork_status

    if hasattr(args, "status") and args.status:
        cowork_status()
        return

    focus = getattr(args, "focus", None)
    if hasattr(args, "daemon") and args.daemon:
        interval = getattr(args, "interval", 1800)
        await run_daemon(interval=interval, focus=focus)
    else:
        await run_cycle(focus=focus)


async def run_full(args):
    """Run workflow loop followed by cowork cycle."""
    from orchestrator import run_full_loop
    from cowork import run_cycle

    print("Phase 1: Workflow System (5-Step Loop)")
    await run_full_loop()

    print("\nPhase 2: Cowork Engine (Observe-Plan-Act-Reflect)")
    await run_cycle(focus=getattr(args, "focus", None))

    print("\nFull run complete.")


async def run_gemini(args):
    """Run Gemini Mirror operations."""
    sys.path.insert(0, str(GEMINI_DIR))
    from mirror_daemon import GeminiMirrorDaemon

    daemon = GeminiMirrorDaemon()
    action = getattr(args, "action", "status")

    if action == "status":
        daemon.show_status()
    elif action == "seed":
        daemon.seed_knowledge()
    elif action == "questions":
        session = getattr(args, "session", "morning") or "morning"
        await daemon.generate_questions(session)
    elif action == "answer":
        q_id = getattr(args, "question_id", None)
        answer_text = getattr(args, "answer_text", None)
        if q_id and answer_text:
            await daemon.answer_question(q_id, answer_text)
        else:
            print("Usage: empire.py gemini answer <question_id> <answer>")
    elif action == "profile":
        await daemon.show_profile()
    elif action == "evolve":
        mode = getattr(args, "mode", "daily") or "daily"
        await daemon.run_evolution(mode)
    elif action == "sync":
        await daemon.run_sync()
    elif action == "daemon":
        interval = getattr(args, "interval", 1800)
        await daemon.daemon_mode(interval)
    elif action == "pending":
        pending = await daemon.vision.get_pending_questions()
        if pending:
            for q in pending:
                print(f"  [{q.get('id')}] ({q.get('category')}) {q.get('question')}")
        else:
            print("  Keine offenen Fragen.")
    else:
        await daemon.single_cycle()


def main():
    parser = argparse.ArgumentParser(
        description="AI Empire - Unified Control Center",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python empire.py status                    Show all systems
  python empire.py workflow                  Run 5-step loop
  python empire.py workflow --step audit     Run single step
  python empire.py cowork --daemon           Start background agent
  python empire.py cowork --focus revenue    Focus on revenue
  python empire.py cycle                     New weekly cycle
  python empire.py full                      Workflow + Cowork
  python empire.py guard                     Resource guard status
  python empire.py gemini status             Gemini mirror status
  python empire.py gemini seed               Seed initial knowledge
  python empire.py gemini questions          Generate vision questions
  python empire.py gemini evolve             Run cross-system evolution
  python empire.py gemini daemon             Start mirror daemon
        """
    )

    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="Show full system status")

    # workflow
    wf = sub.add_parser("workflow", help="Run 5-step workflow loop")
    wf.add_argument("--step", choices=["audit", "architect", "analyst", "refinery", "compounder"])
    wf.add_argument("--new-cycle", action="store_true")

    # cowork
    cw = sub.add_parser("cowork", help="Run cowork engine")
    cw.add_argument("--daemon", action="store_true")
    cw.add_argument("--interval", type=int, default=1800)
    cw.add_argument("--focus", choices=["revenue", "content", "automation", "product"])
    cw.add_argument("--status", action="store_true")

    # cycle
    sub.add_parser("cycle", help="Start new weekly cycle")

    # guard
    sub.add_parser("guard", help="Show resource guard status")

    # full
    full_p = sub.add_parser("full", help="Run workflow + cowork")
    full_p.add_argument("--focus", choices=["revenue", "content", "automation", "product"])

    # gemini mirror
    gm = sub.add_parser("gemini", help="Gemini Mirror dual-system operations")
    gm.add_argument("action", nargs="?", default="status",
                     choices=["status", "seed", "questions", "answer", "profile",
                              "evolve", "sync", "daemon", "pending", "cycle"],
                     help="Gemini mirror action")
    gm.add_argument("--session", choices=["morning", "evening"], default="morning")
    gm.add_argument("--mode", choices=["daily", "weekly"], default="daily")
    gm.add_argument("--interval", type=int, default=1800)
    gm.add_argument("question_id", nargs="?", default=None)
    gm.add_argument("answer_text", nargs="?", default=None)

    args = parser.parse_args()

    if not args.command or args.command == "status":
        show_full_status()
    elif args.command == "workflow":
        asyncio.run(run_workflow(args))
    elif args.command == "cowork":
        asyncio.run(run_cowork(args))
    elif args.command == "cycle":
        from state.context import advance_cycle
        cycle = advance_cycle()
        print(f"New weekly cycle started: #{cycle}")
    elif args.command == "guard":
        from resource_guard import main as guard_main
        guard_main()
    elif args.command == "full":
        asyncio.run(run_full(args))
    elif args.command == "gemini":
        asyncio.run(run_gemini(args))


if __name__ == "__main__":
    main()
