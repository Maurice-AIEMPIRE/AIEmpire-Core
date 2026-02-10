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
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

EMPIRE_ROOT = Path(__file__).parent.parent
WORKFLOW_DIR = Path(__file__).parent

sys.path.insert(0, str(WORKFLOW_DIR))


def show_banner():
    print(
        """
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
    """.format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )


def show_full_status():
    """Zeige Status aller Subsysteme."""
    show_banner()

    # 1. Resource Guard
    from resource_guard import ResourceGuard

    guard = ResourceGuard()
    guard.get_status()
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
        print("  WORKFLOW:")
        print(f"    Cycle:    #{cycle}")
        print(f"    Steps:    {steps} completed")
        print(f"    Patterns: {patterns} in library")
        print(f"    Updated:  {updated}")

        if state.get("steps_completed"):
            print("    Recent:")
            for s in state["steps_completed"][-3:]:
                summary = s.get("summary", "")[:60]
                print(f"      [{s['step'].upper():12s}] {summary}")
    else:
        print("  WORKFLOW: Not initialized")
        print("    Run: python empire.py workflow")
    print()

    # 3. Cowork Engine
    cowork_file = WORKFLOW_DIR / "state" / "cowork_state.json"
    if cowork_file.exists():
        cw = json.loads(cowork_file.read_text())
        print("  COWORK:")
        print(f"    Cycles:   {cw.get('total_cycles', 0)}")
        print(f"    Focus:    {cw.get('active_focus', 'N/A')}")
        print(f"    Actions:  {len(cw.get('actions_taken', []))}")
        print(f"    Patterns: {len(cw.get('patterns_discovered', []))}")
        print(f"    Updated:  {cw.get('updated', 'never')}")

        pending = cw.get("pending_recommendations", [])
        if pending:
            print("    Pending:")
            for p in pending[:3]:
                print(f"      - {p.get('title', 'N/A')[:50]}")
    else:
        print("  COWORK: Not started")
        print("    Run: python empire.py cowork")
    print()

    # 4. Output Inventory
    output_dirs = {
        "Workflow outputs": WORKFLOW_DIR / "output",
        "Cowork outputs": WORKFLOW_DIR / "cowork_output",
        "Swarm outputs": EMPIRE_ROOT / "kimi-swarm" / "output_500k",
        "Reactor reports": EMPIRE_ROOT / "atomic-reactor" / "reports",
    }

    print("  OUTPUT INVENTORY:")
    for name, path in output_dirs.items():
        if path.exists():
            files = list(path.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            print(f"    {name:20s}: {len(files):4d} files ({total_size / 1024:.0f} KB)")
        else:
            print(f"    {name:20s}: (not created)")
    print()

    # 5. Git Status
    import subprocess

    try:
        branch = subprocess.check_output(
            ["git", "-C", str(EMPIRE_ROOT), "branch", "--show-current"],
            text=True,
            timeout=5,
        ).strip()
        uncommitted = subprocess.check_output(
            ["git", "-C", str(EMPIRE_ROOT), "status", "--porcelain"],
            text=True,
            timeout=5,
        ).strip()
        changes = len(uncommitted.split("\n")) if uncommitted else 0
        print(f"  GIT: {branch} | {changes} uncommitted changes")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("  GIT: (could not read)")
    print()

    # 6. Quick Commands
    print("  COMMANDS:")
    print("    python empire.py workflow          # Run 5-step loop")
    print("    python empire.py cowork --daemon   # Start background agent")
    print("    python empire.py cycle             # New weekly cycle")
    print("    python empire.py full              # Workflow + Cowork")
    print()


async def run_workflow(args):
    """Run the 5-step workflow orchestrator."""
    from orchestrator import run_full_loop, run_refinery_loop, run_step
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
    from cowork import run_cycle, run_daemon
    from cowork import show_status as cowork_status

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
    from cowork import run_cycle
    from orchestrator import run_full_loop

    print("Phase 1: Workflow System (5-Step Loop)")
    await run_full_loop()

    print("\nPhase 2: Cowork Engine (Observe-Plan-Act-Reflect)")
    await run_cycle(focus=getattr(args, "focus", None))

    print("\nFull run complete.")


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
        """,
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


if __name__ == "__main__":
    main()
