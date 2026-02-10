#!/usr/bin/env python3
"""
UNIVERSAL KIMI SWARM
The "Maximum Integration" Agent Swarm.
- Uses 'systems/kimi_bridge' for Hybrid Intelligence (Local + Cloud).
- accepts DYNAMIC task types via arguments or JSON config.
- No longer hardcoded to just 6 task types.
"""

import asyncio
import json
import os
import argparse
import time
from datetime import datetime
from pathlib import Path

# Import the new Bridge Client
# Add parent directory to path to import systems module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from systems.kimi_bridge.kimi_client import KimiClient

# Configuration
MAX_CONCURRENT = int(os.getenv("SWARM_CONCURRENCY", 50))
DEFAULT_OUTPUT_DIR = Path("output_universal")

class UniversalSwarm:
    def __init__(self, output_dir: Path = DEFAULT_OUTPUT_DIR):
        self.client = KimiClient()
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "start_time": time.time()
        }
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def worker(self, task_id: int, prompt: str, system_prompt: str, model: str = None, use_local: bool = True):
        async with self.semaphore:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            try:
                # Use the Hybrid Client
                response = await self.client.chat(messages, model=model, use_local=use_local)

                # Save result
                self._save_result(task_id, response)
                self.stats["success"] += 1

                # Feedback (brief)
                print(f"✅ Task {task_id} completed via {response['source']} ({response['model']})")

            except Exception as e:
                self.stats["failed"] += 1
                print(f"❌ Task {task_id} failed: {e}")

    def _save_result(self, task_id: int, data: dict):
        filename = self.output_dir / f"task_{task_id:06d}.json"
        with open(filename, "w") as f:
            json.dump({
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "result": data
            }, f, indent=2)

    async def run_swarm(self, count: int, prompt_template: str, system_prompt: str, use_local: bool = True):
        print(f"🚀 Starting Universal Swarm: {count} agents")
        print(f"   Mode: {'Local First' if use_local else 'API Only'}")

        tasks = []
        for i in range(count):
            # Dynamic prompt injection if needed (e.g. unique IDs)
            final_prompt = prompt_template.replace("{{id}}", str(i))
            tasks.append(self.worker(i, final_prompt, system_prompt, use_local=use_local))

        await asyncio.gather(*tasks)

        duration = time.time() - self.stats["start_time"]
        print(f"\n🏁 Swarm Finished in {duration:.2f}s")
        print(f"   Success: {self.stats['success']}")
        print(f"   Failed:  {self.stats['failed']}")

async def main():
    parser = argparse.ArgumentParser(description="Universal Kimi Swarm")
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of agents")
    parser.add_argument("--prompt", type=str, default="Generate a unique business idea for AI automation.", help="Task prompt")
    parser.add_argument("--system", type=str, default="You are a creative AI expert.", help="System prompt")
    parser.add_argument("--api-only", action="store_true", help="Force API usage (disable local)")

    args = parser.parse_args()

    swarm = UniversalSwarm()
    await swarm.run_swarm(
        count=args.count,
        prompt_template=args.prompt,
        system_prompt=args.system,
        use_local=not args.api_only
    )

if __name__ == "__main__":
    asyncio.run(main())
