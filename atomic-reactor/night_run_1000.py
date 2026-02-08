#!/usr/bin/env python3
"""
NIGHT RUN 1000 - Overnight System Improvement
1000 Tasks via Kimi Moonshot Swarm + 100 Claude Agents
Maurice's AI Empire - 2026

Usage:
    python3 night_run_1000.py --test          # Test: 20 tasks (dry run)
    python3 night_run_1000.py                 # Default: 1000 tasks
    python3 night_run_1000.py --kimi-only     # Only Kimi tasks
    python3 night_run_1000.py --claude-only   # Only Claude tasks
"""

import asyncio
import aiohttp
import json
import os
import time
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from night_tasks_config import generate_task_list, TASK_CATEGORIES

# ═══════════════════════════════════════════
# API Configuration
# ═══════════════════════════════════════════
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ═══════════════════════════════════════════
# Swarm Configuration
# ═══════════════════════════════════════════
KIMI_CONCURRENT = 200       # Max concurrent Kimi API calls
CLAUDE_CONCURRENT = 100     # 100 Claude agents as requested
KIMI_BUDGET_USD = 15.0      # Budget for Kimi Moonshot
CLAUDE_BUDGET_USD = 10.0    # Budget for Claude agents
BATCH_DELAY = 0.05          # Delay between batches (seconds)
CLAUDE_REVIEW_INTERVAL = 200  # Claude meta-review every N tasks
BUDGET_THRESHOLD = 0.95       # Stop at 95% of budget

# ═══════════════════════════════════════════
# Output Directories
# ═══════════════════════════════════════════
OUTPUT_DIR = Path(__file__).parent / "night_output"
KIMI_OUTPUT = OUTPUT_DIR / "kimi_results"
CLAUDE_OUTPUT = OUTPUT_DIR / "claude_results"
REPORTS_DIR = OUTPUT_DIR / "reports"
META_DIR = OUTPUT_DIR / "meta_reviews"

for d in [OUTPUT_DIR, KIMI_OUTPUT, CLAUDE_OUTPUT, REPORTS_DIR, META_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class KimiSwarmAgent:
    """Kimi Moonshot Agent Swarm - für Bulk-Tasks."""

    def __init__(self):
        self.semaphore = asyncio.Semaphore(KIMI_CONCURRENT)
        self.session = None
        self.stats = {
            "completed": 0,
            "failed": 0,
            "tokens_used": 0,
            "cost_usd": 0.0,
        }

    async def init_session(self):
        connector = aiohttp.TCPConnector(
            limit=KIMI_CONCURRENT,
            limit_per_host=KIMI_CONCURRENT,
        )
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(
            connector=connector, timeout=timeout
        )

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def execute(self, task: Dict, retries: int = 3) -> Dict:
        """Execute a single Kimi task with retry logic."""
        async with self.semaphore:
            for attempt in range(retries):
                try:
                    async with self.session.post(
                        "https://api.moonshot.ai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "moonshot-v1-8k",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "Du bist ein Elite Research Agent. Antworte NUR mit validem JSON.",
                                },
                                {"role": "user", "content": task["prompt"]},
                            ],
                            "temperature": 0.8,
                            "max_tokens": 500,
                        },
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = data["choices"][0]["message"]["content"]
                            tokens = data.get("usage", {}).get(
                                "total_tokens", 400
                            )
                            cost = (tokens / 1000) * 0.0005

                            self.stats["completed"] += 1
                            self.stats["tokens_used"] += tokens
                            self.stats["cost_usd"] += cost

                            self._save_result(task, content)

                            return {
                                "task_id": task["task_id"],
                                "status": "success",
                                "tokens": tokens,
                                "cost": cost,
                            }
                        elif resp.status == 429:
                            wait = (2**attempt) + random.uniform(0, 1)
                            await asyncio.sleep(wait)
                            continue
                        else:
                            if attempt == retries - 1:
                                self.stats["failed"] += 1
                                return {
                                    "task_id": task["task_id"],
                                    "status": "error",
                                    "error": f"HTTP {resp.status}",
                                }
                except asyncio.TimeoutError:
                    if attempt == retries - 1:
                        self.stats["failed"] += 1
                        return {
                            "task_id": task["task_id"],
                            "status": "error",
                            "error": "timeout",
                        }
                    await asyncio.sleep(1)
                except (aiohttp.ClientError, Exception) as e:
                    if attempt == retries - 1:
                        self.stats["failed"] += 1
                        return {
                            "task_id": task["task_id"],
                            "status": "error",
                            "error": str(e)[:200],
                        }
                    await asyncio.sleep(1)

            self.stats["failed"] += 1
            return {
                "task_id": task["task_id"],
                "status": "error",
                "error": "max retries",
            }

    def _save_result(self, task: Dict, content: str):
        """Save result to JSON file."""
        filename = KIMI_OUTPUT / f"{task['task_id']}.json"
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            parsed = json.loads(content.strip())
            data = {
                "task_id": task["task_id"],
                "category": task["category_name"],
                "variant": task["variant"],
                "priority": task["priority"],
                "revenue_potential": task["revenue_potential"],
                "timestamp": datetime.now().isoformat(),
                "data": parsed,
            }
        except (json.JSONDecodeError, IndexError, KeyError):
            data = {
                "task_id": task["task_id"],
                "category": task["category_name"],
                "timestamp": datetime.now().isoformat(),
                "raw": content,
            }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class ClaudeAgentArmy:
    """100 Claude Agents for strategic analysis tasks."""

    def __init__(self):
        self.semaphore = asyncio.Semaphore(CLAUDE_CONCURRENT)
        self.session = None
        self.stats = {
            "completed": 0,
            "failed": 0,
            "tokens_used": 0,
            "cost_usd": 0.0,
        }

    async def init_session(self):
        connector = aiohttp.TCPConnector(
            limit=CLAUDE_CONCURRENT,
            limit_per_host=CLAUDE_CONCURRENT,
        )
        timeout = aiohttp.ClientTimeout(total=90)
        self.session = aiohttp.ClientSession(
            connector=connector, timeout=timeout
        )

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def execute(self, task: Dict, retries: int = 3) -> Dict:
        """Execute a single Claude task."""
        async with self.semaphore:
            for attempt in range(retries):
                try:
                    async with self.session.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": ANTHROPIC_API_KEY,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        },
                        json={
                            "model": "claude-3-haiku-20240307",
                            "max_tokens": 1024,
                            "messages": [
                                {"role": "user", "content": task["prompt"]}
                            ],
                        },
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = data["content"][0]["text"]
                            input_tokens = data.get("usage", {}).get(
                                "input_tokens", 0
                            )
                            output_tokens = data.get("usage", {}).get(
                                "output_tokens", 0
                            )
                            # Claude Haiku pricing
                            cost = (input_tokens / 1_000_000) * 0.25 + (
                                output_tokens / 1_000_000
                            ) * 1.25

                            self.stats["completed"] += 1
                            self.stats["tokens_used"] += (
                                input_tokens + output_tokens
                            )
                            self.stats["cost_usd"] += cost

                            self._save_result(task, content)

                            return {
                                "task_id": task["task_id"],
                                "status": "success",
                                "tokens": input_tokens + output_tokens,
                                "cost": cost,
                            }
                        elif resp.status == 429:
                            wait = (2**attempt) + random.uniform(0, 2)
                            await asyncio.sleep(wait)
                            continue
                        else:
                            if attempt == retries - 1:
                                self.stats["failed"] += 1
                                return {
                                    "task_id": task["task_id"],
                                    "status": "error",
                                    "error": f"HTTP {resp.status}",
                                }
                except asyncio.TimeoutError:
                    if attempt == retries - 1:
                        self.stats["failed"] += 1
                        return {
                            "task_id": task["task_id"],
                            "status": "error",
                            "error": "timeout",
                        }
                    await asyncio.sleep(2)
                except (aiohttp.ClientError, Exception) as e:
                    if attempt == retries - 1:
                        self.stats["failed"] += 1
                        return {
                            "task_id": task["task_id"],
                            "status": "error",
                            "error": str(e)[:200],
                        }
                    await asyncio.sleep(2)

            self.stats["failed"] += 1
            return {
                "task_id": task["task_id"],
                "status": "error",
                "error": "max retries",
            }

    def _save_result(self, task: Dict, content: str):
        """Save Claude result to JSON file."""
        filename = CLAUDE_OUTPUT / f"{task['task_id']}.json"
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            parsed = json.loads(content.strip())
            data = {
                "task_id": task["task_id"],
                "category": task["category_name"],
                "variant": task["variant"],
                "priority": task["priority"],
                "revenue_potential": task["revenue_potential"],
                "agent": "claude",
                "timestamp": datetime.now().isoformat(),
                "data": parsed,
            }
        except (json.JSONDecodeError, IndexError, KeyError):
            data = {
                "task_id": task["task_id"],
                "category": task["category_name"],
                "agent": "claude",
                "timestamp": datetime.now().isoformat(),
                "raw": content,
            }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def meta_review(
        self, kimi_stats: Dict, claude_stats: Dict, total_tasks: int
    ) -> Dict:
        """Claude meta-agent reviews overall swarm progress."""
        if not ANTHROPIC_API_KEY:
            return {"status": "skipped", "reason": "no API key"}

        prompt = f"""Du bist der Lead Claude Orchestrator. Analysiere den Fortschritt der Night Run.

Kimi Swarm Stats:
- Completed: {kimi_stats['completed']}
- Failed: {kimi_stats['failed']}
- Tokens: {kimi_stats['tokens_used']:,}
- Cost: ${kimi_stats['cost_usd']:.4f}

Claude Army Stats:
- Completed: {claude_stats['completed']}
- Failed: {claude_stats['failed']}
- Tokens: {claude_stats['tokens_used']:,}
- Cost: ${claude_stats['cost_usd']:.4f}

Total Tasks Remaining: {total_tasks - kimi_stats['completed'] - claude_stats['completed']}

Gib strategische Empfehlungen als JSON:
{{
    "performance_rating": "1-10",
    "bottlenecks": ["Issue 1"],
    "recommendations": ["Action 1", "Action 2"],
    "priority_shift": "mehr_leads/mehr_content/balanced",
    "estimated_completion_time": "X Stunden"
}}"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 512,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["content"][0]["text"]
                        review_file = (
                            META_DIR
                            / f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        )
                        with open(review_file, "w") as f:
                            json.dump(
                                {
                                    "timestamp": datetime.now().isoformat(),
                                    "review": content,
                                },
                                f,
                                indent=2,
                            )
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            return {"status": "ok", "raw": content}
        except (aiohttp.ClientError, asyncio.TimeoutError, Exception) as e:
            return {"status": "error", "error": str(e)[:200]}

        return {"status": "fallback", "recommendations": ["Continue"]}


class NightRunner:
    """Orchestrates 1000 tasks across Kimi swarm + Claude agents."""

    def __init__(self):
        self.kimi = KimiSwarmAgent()
        self.claude = ClaudeAgentArmy()
        self.start_time = None
        self.all_results = []

    async def run(
        self,
        num_tasks: int = 1000,
        kimi_only: bool = False,
        claude_only: bool = False,
    ):
        """Run the overnight task batch."""
        self.start_time = time.time()

        # Generate tasks
        all_tasks = generate_task_list()[:num_tasks]
        kimi_tasks = [t for t in all_tasks if t["agent"] == "kimi"]
        claude_tasks = [t for t in all_tasks if t["agent"] == "claude"]

        if kimi_only:
            claude_tasks = []
        elif claude_only:
            kimi_tasks = []

        total = len(kimi_tasks) + len(claude_tasks)

        print(f"""
{'='*60}
   🌙 NIGHT RUN 1000 - System Improvement
   Maurice's AI Empire - {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*60}
   Total Tasks:      {total}
   Kimi Tasks:       {len(kimi_tasks)} (Concurrent: {KIMI_CONCURRENT})
   Claude Tasks:     {len(claude_tasks)} (Concurrent: {CLAUDE_CONCURRENT})
   Kimi Budget:      ${KIMI_BUDGET_USD}
   Claude Budget:    ${CLAUDE_BUDGET_USD}
   Output:           {OUTPUT_DIR}
   Kimi API:         {'✅' if MOONSHOT_API_KEY else '❌ Not set'}
   Claude API:       {'✅' if ANTHROPIC_API_KEY else '❌ Not set'}
{'='*60}
""")

        # Initialize sessions
        if kimi_tasks:
            await self.kimi.init_session()
        if claude_tasks:
            await self.claude.init_session()

        try:
            # Run Kimi and Claude tasks concurrently
            coros = []
            if kimi_tasks:
                coros.append(self._run_kimi_batch(kimi_tasks))
            if claude_tasks:
                coros.append(self._run_claude_batch(claude_tasks))

            if coros:
                await asyncio.gather(*coros)

        finally:
            if kimi_tasks:
                await self.kimi.close_session()
            if claude_tasks:
                await self.claude.close_session()

        # Final report
        self._print_final_report(total)
        self._save_final_report(total)

    async def _run_kimi_batch(self, tasks: List[Dict]):
        """Run all Kimi tasks in batches."""
        print(f"🚀 Starting Kimi Swarm ({len(tasks)} tasks)...")

        batch_size = KIMI_CONCURRENT
        completed = 0

        for i in range(0, len(tasks), batch_size):
            # Budget check
            if self.kimi.stats["cost_usd"] >= KIMI_BUDGET_USD * BUDGET_THRESHOLD:
                print("💰 Kimi budget limit reached!")
                break

            batch = tasks[i : i + batch_size]
            coros = [self.kimi.execute(task) for task in batch]
            results = await asyncio.gather(*coros, return_exceptions=True)
            self.all_results.extend(
                [r for r in results if isinstance(r, dict)]
            )

            completed += len(batch)
            if completed % 100 == 0:
                elapsed = time.time() - self.start_time
                rate = self.kimi.stats["completed"] / elapsed if elapsed > 0 else 0
                print(
                    f"  🤖 Kimi: {self.kimi.stats['completed']}/{len(tasks)} "
                    f"({rate:.1f}/s) "
                    f"${self.kimi.stats['cost_usd']:.4f}"
                )

            await asyncio.sleep(BATCH_DELAY)

    async def _run_claude_batch(self, tasks: List[Dict]):
        """Run all Claude tasks in batches."""
        print(f"🧠 Starting Claude Army ({len(tasks)} tasks, {CLAUDE_CONCURRENT} agents)...")

        batch_size = CLAUDE_CONCURRENT
        completed = 0
        review_counter = 0

        for i in range(0, len(tasks), batch_size):
            # Budget check
            if self.claude.stats["cost_usd"] >= CLAUDE_BUDGET_USD * BUDGET_THRESHOLD:
                print("💰 Claude budget limit reached!")
                break

            batch = tasks[i : i + batch_size]
            coros = [self.claude.execute(task) for task in batch]
            results = await asyncio.gather(*coros, return_exceptions=True)
            self.all_results.extend(
                [r for r in results if isinstance(r, dict)]
            )

            completed += len(batch)
            review_counter += len(batch)

            if completed % 50 == 0:
                elapsed = time.time() - self.start_time
                rate = self.claude.stats["completed"] / elapsed if elapsed > 0 else 0
                print(
                    f"  🧠 Claude: {self.claude.stats['completed']}/{len(tasks)} "
                    f"({rate:.1f}/s) "
                    f"${self.claude.stats['cost_usd']:.4f}"
                )

            # Meta review checkpoint
            if review_counter >= CLAUDE_REVIEW_INTERVAL:
                review_counter = 0
                review = await self.claude.meta_review(
                    self.kimi.stats,
                    self.claude.stats,
                    len(tasks),
                )
                if review.get("recommendations"):
                    print(f"  📋 Claude Review: {review.get('recommendations', [])[:2]}")

            await asyncio.sleep(BATCH_DELAY)

    def _print_final_report(self, total_tasks: int):
        elapsed = time.time() - self.start_time
        total_completed = (
            self.kimi.stats["completed"] + self.claude.stats["completed"]
        )
        total_cost = (
            self.kimi.stats["cost_usd"] + self.claude.stats["cost_usd"]
        )

        print(f"""
{'='*60}
   ✅ NIGHT RUN COMPLETE
{'='*60}
   Duration:         {elapsed:.0f}s ({elapsed/60:.1f} min)
   Tasks Completed:  {total_completed}/{total_tasks}
   Total Cost:       ${total_cost:.4f}

   KIMI SWARM:
     Completed:      {self.kimi.stats['completed']}
     Failed:         {self.kimi.stats['failed']}
     Tokens:         {self.kimi.stats['tokens_used']:,}
     Cost:           ${self.kimi.stats['cost_usd']:.4f}

   CLAUDE ARMY (100 agents):
     Completed:      {self.claude.stats['completed']}
     Failed:         {self.claude.stats['failed']}
     Tokens:         {self.claude.stats['tokens_used']:,}
     Cost:           ${self.claude.stats['cost_usd']:.4f}

   Output:           {OUTPUT_DIR}
{'='*60}
""")

    def _save_final_report(self, total_tasks: int):
        elapsed = time.time() - self.start_time
        report = {
            "run_id": f"night_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "started_at": datetime.fromtimestamp(self.start_time).isoformat(),
            "completed_at": datetime.now().isoformat(),
            "duration_seconds": elapsed,
            "total_tasks": total_tasks,
            "kimi_stats": self.kimi.stats,
            "claude_stats": self.claude.stats,
            "total_cost_usd": (
                self.kimi.stats["cost_usd"] + self.claude.stats["cost_usd"]
            ),
            "total_completed": (
                self.kimi.stats["completed"] + self.claude.stats["completed"]
            ),
            "total_failed": (
                self.kimi.stats["failed"] + self.claude.stats["failed"]
            ),
            "categories": {
                cat["name"]: cat["count"] for cat in TASK_CATEGORIES
            },
        }

        report_file = (
            REPORTS_DIR
            / f"night_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📝 Report saved: {report_file}")


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Night Run 1000 - Overnight System Improvement"
    )
    parser.add_argument(
        "-n",
        "--tasks",
        type=int,
        default=1000,
        help="Number of tasks (default: 1000)",
    )
    parser.add_argument(
        "--test", action="store_true", help="Test mode (20 tasks)"
    )
    parser.add_argument(
        "--kimi-only", action="store_true", help="Only run Kimi tasks"
    )
    parser.add_argument(
        "--claude-only", action="store_true", help="Only run Claude tasks"
    )
    args = parser.parse_args()

    num_tasks = 20 if args.test else args.tasks

    runner = NightRunner()
    await runner.run(
        num_tasks=num_tasks,
        kimi_only=args.kimi_only,
        claude_only=args.claude_only,
    )


if __name__ == "__main__":
    asyncio.run(main())
