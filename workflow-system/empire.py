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
  python empire.py mirror               # Gemini Mirror Status
  python empire.py mirror --init        # Initialize Gemini Mirror
  python empire.py mirror --sync        # Run sync cycle
  python empire.py mirror --daemon      # Continuous sync daemon
  python empire.py vision               # Today's vision questions
  python empire.py vision --answer      # Answer questions interactively
  python empire.py vision --profile     # Show vision profile
  python empire.py evolve               # Run cross-pollination evolution cycle
  python empire.py factory              # Product Factory status
  python empire.py factory --pipeline   # Run full product pipeline
  python empire.py memory               # Shared memory status
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
MIRROR_DIR = EMPIRE_ROOT / "gemini-mirror"
FACTORY_DIR = EMPIRE_ROOT / "product-factory"

sys.path.insert(0, str(WORKFLOW_DIR))
sys.path.insert(0, str(MIRROR_DIR))
sys.path.insert(0, str(FACTORY_DIR))


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

    # 4. Gemini Mirror
    mirror_state_file = MIRROR_DIR / "state" / "gemini_state.json"
    if mirror_state_file.exists():
        ms = json.loads(mirror_state_file.read_text())
        print(f"  GEMINI MIRROR:")
        print(f"    Initialized: {ms.get('initialized', 'NOT YET')}")
        print(f"    Sync Cycles: {ms.get('total_sync_cycles', 0)}")
        print(f"    Improvements Sent: {ms.get('total_improvements_sent', 0)}")
        print(f"    Last Sync:   {ms.get('last_sync', 'never')}")

        questions = ms.get("pending_questions", [])
        if questions:
            print(f"    Fragen an Maurice: {len(questions)}")
    else:
        print(f"  GEMINI MIRROR: Not initialized")
        print(f"    Run: python empire.py mirror --init")
    print()

    # 5. Vision Profile
    vision_state_file = MIRROR_DIR / "state" / "vision_state.json"
    if vision_state_file.exists():
        vs = json.loads(vision_state_file.read_text())
        print(f"  VISION ENGINE:")
        print(f"    Questions Asked:    {vs.get('total_questions_asked', 0)}")
        print(f"    Answers Received:   {vs.get('total_answers_received', 0)}")
        print(f"    Unanswered:         {len(vs.get('unanswered_questions', []))}")
        confidence = vs.get("confidence_scores", {})
        if confidence:
            avg = sum(confidence.values()) / len(confidence) if confidence else 0
            print(f"    Avg Confidence:     {avg:.0%}")
    else:
        print(f"  VISION ENGINE: Not started")
        print(f"    Run: python empire.py vision")
    print()

    # 6. Product Factory
    factory_state_file = FACTORY_DIR / "runs" / "pipeline_state.json"
    if factory_state_file.exists():
        fs = json.loads(factory_state_file.read_text())
        print(f"  PRODUCT FACTORY:")
        print(f"    Ideas:    {fs.get('total_ideas', 0)}")
        print(f"    Products: {fs.get('total_products', 0)}")
        print(f"    Launched: {fs.get('total_launched', 0)}")
        print(f"    Revenue:  {fs.get('total_revenue', 0):.2f} EUR")
    else:
        print(f"  PRODUCT FACTORY: Not started")
        print(f"    Run: python empire.py factory --pipeline")
    print()

    # 7. Cross-Pollinator
    pollination_file = MIRROR_DIR / "state" / "pollination_state.json"
    if pollination_file.exists():
        ps = json.loads(pollination_file.read_text())
        print(f"  CROSS-POLLINATOR:")
        print(f"    Generation:    #{ps.get('evolution_generation', 0)}")
        print(f"    Total Merges:  {ps.get('total_merges', 0)}")
        print(f"    Best Practices: {len(ps.get('best_practices', []))}")
    else:
        print(f"  CROSS-POLLINATOR: Not started")
        print(f"    Run: python empire.py evolve")
    print()

    # 8. Shared Memory
    memory_file = MIRROR_DIR / "memory" / "shared_knowledge.json"
    if memory_file.exists():
        mk = json.loads(memory_file.read_text())
        print(f"  SHARED MEMORY:")
        print(f"    Knowledge Entries: {mk.get('total_entries', 0)}")
        non_empty = {k: len(v) for k, v in mk.get("categories", {}).items() if v}
        if non_empty:
            for cat, count in sorted(non_empty.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"      {cat}: {count}")
    else:
        print(f"  SHARED MEMORY: Empty")
        print(f"    Run: python empire.py memory --import-all")
    print()

    # 9. Output Inventory
    output_dirs = {
        "Workflow outputs": WORKFLOW_DIR / "output",
        "Cowork outputs": WORKFLOW_DIR / "cowork_output",
        "Swarm outputs": EMPIRE_ROOT / "kimi-swarm" / "output_500k",
        "Reactor reports": EMPIRE_ROOT / "atomic-reactor" / "reports",
        "Mirror outputs": MIRROR_DIR / "output",
        "Factory products": FACTORY_DIR / "products",
        "Marketing": FACTORY_DIR / "marketing",
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

    # 5. Git Status
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

    # 10. Quick Commands
    print(f"  COMMANDS:")
    print(f"    python empire.py workflow            # Run 5-step loop")
    print(f"    python empire.py cowork --daemon     # Start background agent")
    print(f"    python empire.py mirror --init       # Initialize Gemini Mirror")
    print(f"    python empire.py mirror --sync       # Sync both brains")
    print(f"    python empire.py vision              # Today's questions")
    print(f"    python empire.py vision --answer     # Answer questions")
    print(f"    python empire.py evolve              # Cross-pollination cycle")
    print(f"    python empire.py factory --pipeline  # Full product pipeline")
    print(f"    python empire.py memory              # Shared memory status")
    print(f"    python empire.py cycle               # New weekly cycle")
    print(f"    python empire.py full                # Workflow + Cowork + Mirror")
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


async def run_mirror(args):
    """Run the Gemini Mirror system."""
    from mirror_core import initialize_mirror, sync_cycle, run_daemon as mirror_daemon, show_status as mirror_status

    if hasattr(args, "status") and args.status:
        mirror_status()
    elif hasattr(args, "init") and args.init:
        await initialize_mirror()
    elif hasattr(args, "daemon") and args.daemon:
        interval = getattr(args, "interval", 300)
        await mirror_daemon(interval=interval)
    elif hasattr(args, "sync") and args.sync:
        await sync_cycle()
    else:
        mirror_status()


async def run_vision(args):
    """Run the Vision Discovery Engine."""
    from vision_engine import (
        generate_daily_questions, interactive_answer_session,
        show_profile_summary, show_todays_questions, show_qa_history,
    )

    if hasattr(args, "answer") and args.answer:
        await interactive_answer_session()
    elif hasattr(args, "profile") and args.profile:
        show_profile_summary()
    elif hasattr(args, "history") and args.history:
        show_qa_history()
    elif hasattr(args, "generate") and args.generate:
        await generate_daily_questions(force=True)
        show_todays_questions()
    else:
        show_todays_questions()


async def run_evolve(args):
    """Run cross-pollination evolution cycle."""
    from cross_pollinator import run_evolution_cycle, show_status as pollination_status

    if hasattr(args, "status") and args.status:
        pollination_status()
    else:
        await run_evolution_cycle()


async def run_factory(args):
    """Run the Product Factory."""
    from factory import (
        run_full_pipeline, score_ideas, design_product,
        produce_assets, generate_marketing, add_idea,
        show_status as factory_status, list_products,
    )

    if hasattr(args, "list") and args.list:
        list_products()
    elif hasattr(args, "pipeline") and args.pipeline:
        idea = getattr(args, "idea", None)
        await run_full_pipeline(idea)
    elif hasattr(args, "score") and args.score:
        await score_ideas()
    elif hasattr(args, "add_idea") and args.add_idea:
        add_idea(args.add_idea)
    else:
        factory_status()


async def run_memory(args):
    """Run memory bridge operations."""
    from memory_bridge import (
        show_status as memory_status, import_from_workflow_patterns,
        import_from_cowork_state, consolidate_knowledge, search_knowledge,
    )

    if hasattr(args, "import_all") and args.import_all:
        wf = import_from_workflow_patterns()
        cw = import_from_cowork_state()
        print(f"  Imported: {wf} from workflow, {cw} from cowork")
    elif hasattr(args, "consolidate") and args.consolidate:
        stats = consolidate_knowledge()
        print(f"  Consolidated: {stats}")
    elif hasattr(args, "search") and args.search:
        results = search_knowledge(args.search)
        print(f"\n  Search: '{args.search}' -> {len(results)} results")
        for r in results[:10]:
            print(f"    [{r['category']}] {r['key']}: {r.get('value', 'N/A')[:50]}")
    else:
        memory_status()


async def run_full(args):
    """Run workflow loop followed by cowork cycle and mirror sync."""
    from orchestrator import run_full_loop
    from cowork import run_cycle

    print("Phase 1: Workflow System (5-Step Loop)")
    await run_full_loop()

    print("\nPhase 2: Cowork Engine (Observe-Plan-Act-Reflect)")
    await run_cycle(focus=getattr(args, "focus", None))

    # Phase 3: Mirror sync (if initialized)
    mirror_state = MIRROR_DIR / "state" / "gemini_state.json"
    if mirror_state.exists():
        print("\nPhase 3: Gemini Mirror Sync")
        try:
            from mirror_core import sync_cycle
            await sync_cycle()
        except Exception as e:
            print(f"  Mirror sync skipped: {e}")

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
    full_p = sub.add_parser("full", help="Run workflow + cowork + mirror")
    full_p.add_argument("--focus", choices=["revenue", "content", "automation", "product"])

    # mirror (Gemini Mirror)
    mi = sub.add_parser("mirror", help="Gemini Mirror - Dual-Brain System")
    mi.add_argument("--init", action="store_true", help="Initialize Gemini mirror")
    mi.add_argument("--sync", action="store_true", help="Run one sync cycle")
    mi.add_argument("--daemon", action="store_true", help="Continuous sync daemon")
    mi.add_argument("--interval", type=int, default=300, help="Sync interval (seconds)")
    mi.add_argument("--status", action="store_true", help="Show mirror status")

    # vision (Vision Discovery Engine)
    vi = sub.add_parser("vision", help="Vision Discovery - Daily Questions")
    vi.add_argument("--answer", action="store_true", help="Answer questions interactively")
    vi.add_argument("--profile", action="store_true", help="Show vision profile")
    vi.add_argument("--history", action="store_true", help="Show Q&A history")
    vi.add_argument("--generate", action="store_true", help="Generate new questions")

    # evolve (Cross-Pollinator)
    ev = sub.add_parser("evolve", help="Cross-Pollination Evolution Cycle")
    ev.add_argument("--status", action="store_true", help="Show pollination status")

    # factory (Product Factory)
    fa = sub.add_parser("factory", help="Product Factory Pipeline")
    fa.add_argument("--pipeline", action="store_true", help="Run full product pipeline")
    fa.add_argument("--idea", type=str, help="Add idea and run pipeline")
    fa.add_argument("--score", action="store_true", help="Score all ideas")
    fa.add_argument("--add-idea", type=str, help="Add idea to inbox")
    fa.add_argument("--list", action="store_true", help="List all products")

    # memory (Memory Bridge)
    me = sub.add_parser("memory", help="Shared Memory / Knowledge Graph")
    me.add_argument("--import-all", action="store_true", help="Import from existing systems")
    me.add_argument("--consolidate", action="store_true", help="Merge and deduplicate")
    me.add_argument("--search", type=str, help="Search knowledge graph")

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
    elif args.command == "mirror":
        asyncio.run(run_mirror(args))
    elif args.command == "vision":
        asyncio.run(run_vision(args))
    elif args.command == "evolve":
        asyncio.run(run_evolve(args))
    elif args.command == "factory":
        asyncio.run(run_factory(args))
    elif args.command == "memory":
        asyncio.run(run_memory(args))


if __name__ == "__main__":
    main()
