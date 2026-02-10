#!/usr/bin/env python3
"""
Gemini Mirror Daemon - Main orchestrator for the dual-system architecture.

Usage:
    # Full daemon mode (runs continuously)
    python gemini-mirror/mirror_daemon.py --daemon

    # Single cycle
    python gemini-mirror/mirror_daemon.py

    # Generate vision questions
    python gemini-mirror/mirror_daemon.py --questions [morning|evening]

    # Answer a vision question
    python gemini-mirror/mirror_daemon.py --answer <question_id> "Your answer"

    # View vision profile
    python gemini-mirror/mirror_daemon.py --profile

    # Run evolution
    python gemini-mirror/mirror_daemon.py --evolve [daily|weekly]

    # Sync now
    python gemini-mirror/mirror_daemon.py --sync

    # Full status
    python gemini-mirror/mirror_daemon.py --status

    # Seed initial knowledge
    python gemini-mirror/mirror_daemon.py --seed
"""

import os
import sys
import json
import asyncio
import argparse
import signal
from pathlib import Path
from datetime import datetime, timezone

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent))

from gemini_client import MirrorGeminiClient as GeminiClient
from digital_memory import DigitalMemory
from mirror_sync import MirrorSyncEngine
from vision_discovery import VisionDiscoveryEngine
from evolution_protocol import EvolutionProtocol


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║              GEMINI MIRROR - DUAL SYSTEM ENGINE              ║
║                                                              ║
║  Claude (Mac) ←──── Git Sync ────→ Gemini (Cloud)           ║
║                                                              ║
║  Vision Discovery │ Digital Memory │ Cross-Evolution         ║
╚══════════════════════════════════════════════════════════════╝
"""


class GeminiMirrorDaemon:
    """
    Main orchestrator that ties all components together.

    Components:
    - GeminiClient: API interface to Gemini models
    - DigitalMemory: Persistent knowledge graph
    - MirrorSyncEngine: Bidirectional sync
    - VisionDiscoveryEngine: Daily questions
    - EvolutionProtocol: Cross-system evolution
    """

    def __init__(self):
        self.gemini = GeminiClient()
        self.memory = DigitalMemory()
        self.sync = MirrorSyncEngine(self.gemini)
        self.vision = VisionDiscoveryEngine(self.gemini, self.memory)
        self.evolution = EvolutionProtocol(self.gemini, self.memory, self.sync)
        self._running = True

    async def single_cycle(self) -> dict:
        """Run one complete cycle: sync → evolve → questions → sync."""
        print("\n[CYCLE] Starting Gemini Mirror cycle...")
        results = {}

        # Step 1: Sync
        print("[1/4] Syncing systems...")
        results["sync"] = await self.sync.sync()
        print(f"       Synced: {results['sync'].get('total_artifacts', 0)} artifacts")

        # Step 2: Evolution (daily)
        print("[2/4] Running daily evolution...")
        results["evolution"] = await self.evolution.run_daily_evolution()
        print(f"       Evolution complete")

        # Step 3: Generate questions if needed
        pending = await self.vision.get_pending_questions()
        if len(pending) < 3:
            print("[3/4] Generating vision questions...")
            results["questions"] = await self.vision.generate_daily_questions("morning")
            print(f"       Generated {len(results.get('questions', []))} questions")
        else:
            print(f"[3/4] {len(pending)} questions pending - skipping generation")
            results["questions"] = pending

        # Step 4: Final sync (push evolution results)
        print("[4/4] Final sync...")
        results["final_sync"] = await self.sync.sync()

        # Memory decay
        self.memory.decay()

        print(f"\n[DONE] Cycle complete. Gemini stats: {self.gemini.stats()}")
        return results

    async def daemon_mode(self, interval: int = 1800):
        """Run continuously every N seconds."""
        print(BANNER)
        print(f"[DAEMON] Running every {interval}s (Ctrl+C to stop)\n")

        cycle = 0
        while self._running:
            cycle += 1
            print(f"\n{'='*60}")
            print(f"[DAEMON] Cycle {cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")

            try:
                results = await self.single_cycle()
            except Exception as e:
                print(f"[ERROR] Cycle failed: {e}")

            if self._running:
                print(f"\n[DAEMON] Next cycle in {interval}s...")
                await asyncio.sleep(interval)

    async def generate_questions(self, session: str = "morning") -> list:
        """Generate vision discovery questions."""
        print(f"\n[QUESTIONS] Generating {session} questions...\n")
        questions = await self.vision.generate_daily_questions(session)

        for i, q in enumerate(questions, 1):
            print(f"  [{i}] ({q.get('category', '?')}) {q.get('question', '?')}")
            print(f"      Warum: {q.get('why', '?')}")
            print(f"      ID: {q.get('id', '?')}")
            print()

        return questions

    async def answer_question(self, question_id: str, answer: str) -> dict:
        """Process an answer to a vision question."""
        print(f"\n[ANSWER] Processing answer for {question_id}...")
        result = await self.vision.process_answer(question_id, answer)

        if result.get("error"):
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Insights extracted: {result.get('insights_extracted', 0)}")
            print(f"  Memory updates: {result.get('memory_updates', 0)}")
            print(f"  Actions identified: {result.get('actions_identified', 0)}")

            if result.get("insights", {}).get("actions"):
                print("\n  Empfohlene Aktionen:")
                for action in result["insights"]["actions"]:
                    print(f"    → {action}")

        return result

    async def show_profile(self) -> dict:
        """Show the current vision profile."""
        print("\n[PROFILE] Generating vision profile...\n")
        profile = await self.vision.get_vision_profile()

        if profile.get("status") == "no_data":
            print("  Noch keine Daten. Starte mit: --questions morning")
            return profile

        for key, value in profile.items():
            if isinstance(value, list):
                print(f"  {key}:")
                for item in value:
                    print(f"    - {item}")
            elif isinstance(value, dict):
                print(f"  {key}: {json.dumps(value, ensure_ascii=False)}")
            else:
                print(f"  {key}: {value}")
            print()

        return profile

    async def run_evolution(self, mode: str = "daily") -> dict:
        """Run evolution protocol."""
        print(f"\n[EVOLUTION] Running {mode} evolution...\n")

        if mode == "weekly":
            results = await self.evolution.run_weekly_evolution()
        else:
            results = await self.evolution.run_daily_evolution()

        for strategy, outcome in results.items():
            print(f"  {strategy}:")
            if isinstance(outcome, dict):
                for k, v in list(outcome.items())[:3]:
                    if isinstance(v, list):
                        print(f"    {k}: {len(v)} items")
                    else:
                        preview = str(v)[:100]
                        print(f"    {k}: {preview}")
            else:
                print(f"    {str(outcome)[:100]}")
            print()

        return results

    async def run_sync(self) -> dict:
        """Run a sync cycle."""
        print("\n[SYNC] Running sync...\n")
        result = await self.sync.sync()

        print(f"  Status: {result.get('status')}")
        print(f"  From Claude: {result.get('claude_synced', 0)}")
        print(f"  From Gemini: {result.get('gemini_synced', 0)}")
        print(f"  Total: {result.get('total_artifacts', 0)}")

        return result

    def show_status(self) -> dict:
        """Show full system status."""
        print(BANNER)

        # Memory stats
        mem_stats = self.memory.stats()
        print("[DIGITAL MEMORY]")
        print(f"  Total memories: {mem_stats['total_memories']}")
        print(f"  High confidence: {mem_stats['high_confidence']}")
        print(f"  Knowledge gaps: {len(mem_stats['gaps'])}")
        for gap in mem_stats["gaps"]:
            print(f"    ! {gap}")
        print()

        # Sync stats
        sync_stats = self.sync.status()
        print("[MIRROR SYNC]")
        print(f"  Claude outbox: {sync_stats['claude_outbox']} ({sync_stats['claude_unsynced']} unsynced)")
        print(f"  Gemini outbox: {sync_stats['gemini_outbox']} ({sync_stats['gemini_unsynced']} unsynced)")
        print(f"  Total syncs: {sync_stats['total_syncs']}")
        print(f"  Last sync: {sync_stats['last_sync']}")
        print()

        # Evolution stats
        evo_stats = self.evolution.status()
        print("[EVOLUTION]")
        print(f"  Total evolutions: {evo_stats['total_evolutions']}")
        print(f"  Total benchmarks: {evo_stats['total_benchmarks']}")
        print(f"  Last evolution: {evo_stats['last_evolution']}")
        print()

        # Gemini API stats
        api_stats = self.gemini.stats()
        print("[GEMINI API]")
        print(f"  Calls: {api_stats['total_calls']}")
        print(f"  Tokens: {api_stats['total_tokens']}")
        print(f"  Cost: ${api_stats['total_cost_usd']}")
        print()

        # Pending questions
        state_dir = Path(__file__).parent / "state"
        q_file = state_dir / "vision_questions.json"
        if q_file.exists():
            try:
                questions = json.loads(q_file.read_text())
                pending = [q for q in questions if not q.get("answered")]
                print("[VISION DISCOVERY]")
                print(f"  Total questions: {len(questions)}")
                print(f"  Pending answers: {len(pending)}")
                if pending:
                    print("  Next question:")
                    print(f"    [{pending[0].get('id')}] {pending[0].get('question', '?')}")
                print()
            except (json.JSONDecodeError, OSError):
                pass

        return {
            "memory": mem_stats,
            "sync": sync_stats,
            "evolution": evo_stats,
            "api": api_stats,
        }

    def seed_knowledge(self):
        """Seed initial knowledge about Maurice."""
        print("\n[SEED] Seeding initial knowledge...")
        self.memory.seed_initial_knowledge()
        stats = self.memory.stats()
        print(f"  Seeded {stats['total_memories']} memories")
        print(f"  Categories filled: {sum(1 for v in stats['by_category'].values() if v['count'] > 0)}")
        print("  Done.")

    def stop(self):
        """Stop the daemon gracefully."""
        self._running = False
        print("\n[STOP] Shutting down Gemini Mirror...")


async def main():
    parser = argparse.ArgumentParser(
        description="Gemini Mirror - Dual System Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mirror_daemon.py --status              # System status
  python mirror_daemon.py --seed                 # Seed initial knowledge
  python mirror_daemon.py --questions morning    # Generate morning questions
  python mirror_daemon.py --answer q_123 "..."   # Answer a question
  python mirror_daemon.py --profile              # Vision profile
  python mirror_daemon.py --evolve daily         # Run evolution
  python mirror_daemon.py --sync                 # Run sync
  python mirror_daemon.py --daemon               # Run continuously
  python mirror_daemon.py                        # Single cycle
        """,
    )

    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    parser.add_argument("--interval", type=int, default=1800, help="Daemon interval (seconds)")
    parser.add_argument("--questions", nargs="?", const="morning", help="Generate questions [morning|evening]")
    parser.add_argument("--answer", nargs=2, metavar=("QUESTION_ID", "ANSWER"), help="Answer a question")
    parser.add_argument("--profile", action="store_true", help="Show vision profile")
    parser.add_argument("--evolve", nargs="?", const="daily", help="Run evolution [daily|weekly]")
    parser.add_argument("--sync", action="store_true", help="Run sync")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--seed", action="store_true", help="Seed initial knowledge")
    parser.add_argument("--pending", action="store_true", help="Show pending questions")

    args = parser.parse_args()

    daemon = GeminiMirrorDaemon()

    # Handle Ctrl+C
    def signal_handler(sig, frame):
        daemon.stop()
    signal.signal(signal.SIGINT, signal_handler)

    if args.status:
        daemon.show_status()
    elif args.seed:
        daemon.seed_knowledge()
    elif args.questions:
        await daemon.generate_questions(args.questions)
    elif args.answer:
        await daemon.answer_question(args.answer[0], args.answer[1])
    elif args.pending:
        pending = await daemon.vision.get_pending_questions()
        if pending:
            for q in pending:
                print(f"  [{q.get('id')}] ({q.get('category')}) {q.get('question')}")
        else:
            print("  Keine offenen Fragen.")
    elif args.profile:
        await daemon.show_profile()
    elif args.evolve:
        await daemon.run_evolution(args.evolve)
    elif args.sync:
        await daemon.run_sync()
    elif args.daemon:
        await daemon.daemon_mode(args.interval)
    else:
        await daemon.single_cycle()


if __name__ == "__main__":
    asyncio.run(main())
