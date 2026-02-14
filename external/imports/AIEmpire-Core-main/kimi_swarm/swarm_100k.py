#!/usr/bin/env python3
"""
100.000 KIMI AGENTS SWARM
Maurice's AI Empire - Maximum Free Power
Budget: $15 = ~30 Mio Tokens
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import os
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
MAX_CONCURRENT = 50  # Reduced to avoid rate limits
TOTAL_AGENTS = 100000
BUDGET_USD = 15.0
BATCH_DELAY = 0.5  # Delay between batches in seconds

# Validation and estimation constants
ESTIMATED_SECONDS_PER_TASK = 0.5  # Average time per task for capacity estimation

# Output directories
OUTPUT_DIR = Path(__file__).parent / "output_100k"
LEADS_DIR = OUTPUT_DIR / "leads"
CONTENT_DIR = OUTPUT_DIR / "content"
COMPETITORS_DIR = OUTPUT_DIR / "competitors"
NUGGETS_DIR = OUTPUT_DIR / "gold_nuggets"

# Create directories
for d in [OUTPUT_DIR, LEADS_DIR, CONTENT_DIR, COMPETITORS_DIR, NUGGETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Task Types für die Agents
TASK_TYPES = [
    {
        "type": "lead_research",
        "output_dir": LEADS_DIR,
        "prompt": """Du bist ein Lead-Research-Agent. Generiere ein REALISTISCHES Lead-Profil fuer X/Twitter.

Zielgruppe: Unternehmen die AI-Automation brauchen (E-Commerce, SaaS, Agenturen)

OUTPUT als JSON:
{
    "handle": "@beispiel_firma",
    "company": "Firmenname",
    "industry": "Branche",
    "pain_points": ["Problem 1", "Problem 2"],
    "ai_opportunity": "Wie AI helfen kann",
    "outreach_hook": "Erster DM-Satz",
    "priority": "high/medium/low"
}"""
    },
    {
        "type": "content_idea",
        "output_dir": CONTENT_DIR,
        "prompt": """Generiere eine virale X/Twitter Content-Idee ueber AI-Automation.

Formate: Thread, Single Tweet, Meme-Konzept, Hot Take

OUTPUT als JSON:
{
    "format": "thread/single/meme/take",
    "hook": "Erster Satz",
    "main_content": "Hauptinhalt",
    "cta": "Call to Action",
    "hashtags": ["#AI", "#Automation"],
    "viral_score": 1-10
}"""
    },
    {
        "type": "competitor_analysis",
        "output_dir": COMPETITORS_DIR,
        "prompt": """Analysiere einen FIKTIVEN AI-Berater/Agentur Konkurrenten.

OUTPUT als JSON:
{
    "name": "Konkurrentenname",
    "positioning": "USP",
    "services": ["Service 1", "Service 2"],
    "pricing": "Preismodell",
    "strengths": ["Staerke 1"],
    "weaknesses": ["Schwaeche 1"],
    "opportunity": "Wie Maurice gewinnen kann"
}"""
    },
    {
        "type": "gold_nugget",
        "output_dir": NUGGETS_DIR,
        "prompt": """Extrahiere ein wertvolles Gold Nugget - eine Business-Erkenntnis.

Kategorien: Monetarisierung, Effizienz, Strategie, Technik

OUTPUT als JSON:
{
    "category": "monetization/efficiency/strategy/tech",
    "title": "Kurzer Titel",
    "insight": "Die Erkenntnis",
    "action": "Naechster Schritt",
    "value_eur": 1000,
    "priority": "high/medium/low"
}"""
    },
]

class KimiSwarm:
    def __init__(self):
        self.stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "tokens_used": 0,
            "cost_usd": 0.0,
            "start_time": None,
            "results": [],
            "by_type": {"lead_research": 0, "content_idea": 0, "competitor_analysis": 0, "gold_nugget": 0}
        }
        self.running = True
        self.max_concurrent = MAX_CONCURRENT  # Store for validation
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        self.session = None
        self.task_counter = 0
        
    def validate_max_agent_capacity(self) -> bool:
        """Validate that system is configured to spawn max agents."""
        print(f"\n{'='*60}")
        print("🔍 VALIDATING MAX AGENT CAPACITY")
        print(f"{'='*60}")
        
        validation_passed = True
        
        # Check TOTAL_AGENTS configuration
        print(f"Total Agents Capacity: {TOTAL_AGENTS:,}")
        if TOTAL_AGENTS <= 0:
            print("  ❌ TOTAL_AGENTS must be > 0")
            validation_passed = False
        else:
            print("  ✅ Valid agent capacity configured")
        
        # Check MAX_CONCURRENT configuration
        print(f"Max Concurrent Workers: {MAX_CONCURRENT}")
        if MAX_CONCURRENT <= 0:
            print("  ❌ MAX_CONCURRENT must be > 0")
            validation_passed = False
        elif MAX_CONCURRENT > 200:
            print("  ⚠️  Warning: MAX_CONCURRENT > 200 may cause rate limiting")
        else:
            print("  ✅ Valid concurrency level")
        
        # Check API key is set
        if not MOONSHOT_API_KEY:
            print("  ❌ MOONSHOT_API_KEY not set")
            validation_passed = False
        else:
            print("  ✅ API key configured")
        
        # Check semaphore capacity matches configuration
        if self.max_concurrent != MAX_CONCURRENT:
            print("  ❌ Semaphore capacity mismatch")
            validation_passed = False
        else:
            print("  ✅ Semaphore initialized correctly")
        
        # Check output directories exist
        for dir_path in [OUTPUT_DIR, LEADS_DIR, CONTENT_DIR, COMPETITORS_DIR, NUGGETS_DIR]:
            if not dir_path.exists():
                print(f"  ❌ Output directory missing: {dir_path}")
                validation_passed = False
        print("  ✅ All output directories exist")
        
        # Capacity report
        estimated_time = (TOTAL_AGENTS / MAX_CONCURRENT) * ESTIMATED_SECONDS_PER_TASK
        print("\nCapacity Report:")
        print(f"  • Max Agents: {TOTAL_AGENTS:,}")
        print(f"  • Concurrent Workers: {MAX_CONCURRENT}")
        print(f"  • Estimated Time for Full Run: {estimated_time/3600:.1f} hours")
        print(f"  • Estimated Cost: ${BUDGET_USD:.2f}")
        
        if validation_passed:
            print("\n✅ System validated - ready to spawn max agents!")
        else:
            print("\n❌ Validation failed - fix issues before spawning agents")
        
        print(f"{'='*60}\n")
        return validation_passed

    async def init_session(self):
        """Initialize shared session for all requests."""
        connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT, limit_per_host=MAX_CONCURRENT)
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def close_session(self):
        """Close shared session."""
        if self.session:
            await self.session.close()

    def save_result(self, task_id: int, task_type: Dict, content: str):
        """Save individual result to file."""
        output_dir = task_type.get("output_dir", OUTPUT_DIR)
        filename = output_dir / f"{task_type['type']}_{task_id:06d}.json"

        try:
            # Try to parse JSON from content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            parsed = json.loads(content.strip())
            data = {"task_id": task_id, "type": task_type["type"], "timestamp": datetime.now().isoformat(), "data": parsed}
        except Exception:
            data = {"task_id": task_id, "type": task_type["type"], "timestamp": datetime.now().isoformat(), "raw": content}

        with open(filename, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def execute_task(self, task_id: int, task_type: Dict, retries: int = 3) -> Dict:
        """Execute single task with rate limiting."""
        async with self.semaphore:
            for attempt in range(retries):
                try:
                    async with self.session.post(
                        "https://api.moonshot.ai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "moonshot-v1-8k",
                            "messages": [
                                {"role": "system", "content": "Du bist ein Research-Agent. Antworte NUR mit validem JSON."},
                                {"role": "user", "content": task_type["prompt"]}
                            ],
                            "temperature": 0.8,
                            "max_tokens": 400
                        }
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = data["choices"][0]["message"]["content"]
                            tokens = data.get("usage", {}).get("total_tokens", 300)

                            self.stats["completed"] += 1
                            self.stats["tokens_used"] += tokens
                            self.stats["by_type"][task_type["type"]] += 1
                            # Kimi moonshot-v1-8k: $0.0005 per 1K tokens
                            self.stats["cost_usd"] += (tokens / 1000) * 0.0005

                            # Save to file
                            self.save_result(task_id, task_type, content)

                            return {
                                "task_id": task_id,
                                "type": task_type["type"],
                                "status": "success",
                                "tokens": tokens
                            }
                        elif resp.status == 429:
                            # Rate limited - longer exponential backoff
                            wait = (3 ** attempt) + 2
                            await asyncio.sleep(wait)
                            continue
                        else:
                            text = await resp.text()
                            if attempt == retries - 1:
                                self.stats["failed"] += 1
                                return {"task_id": task_id, "status": "error", "error": f"HTTP {resp.status}: {text[:100]}"}
                except asyncio.TimeoutError:
                    if attempt == retries - 1:
                        self.stats["failed"] += 1
                        return {"task_id": task_id, "status": "error", "error": "timeout"}
                    await asyncio.sleep(1)
                except Exception as e:
                    if attempt == retries - 1:
                        self.stats["failed"] += 1
                        return {"task_id": task_id, "status": "error", "error": str(e)}
                    await asyncio.sleep(1)

            self.stats["failed"] += 1
            return {"task_id": task_id, "status": "error", "error": "max retries"}

    async def run_batch(self, start_id: int, count: int) -> List[Dict]:
        """Run a batch of tasks."""
        tasks = []
        for i in range(count):
            task_id = start_id + i
            task_type = TASK_TYPES[task_id % len(TASK_TYPES)]
            tasks.append(self.execute_task(task_id, task_type))
            self.stats["total_tasks"] += 1

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def print_stats(self):
        """Print current stats."""
        elapsed = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        rate = self.stats["completed"] / elapsed if elapsed > 0 else 0
        eta = (self.stats["total_tasks"] - self.stats["completed"]) / rate if rate > 0 else 0

        print(f"\n{'='*60}")
        print("KIMI SWARM STATS")
        print(f"{'='*60}")
        print(f"Completed:      {self.stats['completed']:,} / {self.stats['total_tasks']:,}")
        print(f"Failed:         {self.stats['failed']:,}")
        print(f"Tokens Used:    {self.stats['tokens_used']:,}")
        print(f"Cost:           ${self.stats['cost_usd']:.4f} / ${BUDGET_USD:.2f}")
        print(f"Rate:           {rate:.1f} tasks/sec")
        print(f"Elapsed:        {elapsed:.1f}s | ETA: {eta:.0f}s")
        print("---")
        print(f"Leads:          {self.stats['by_type']['lead_research']:,}")
        print(f"Content:        {self.stats['by_type']['content_idea']:,}")
        print(f"Competitors:    {self.stats['by_type']['competitor_analysis']:,}")
        print(f"Gold Nuggets:   {self.stats['by_type']['gold_nugget']:,}")
        print(f"{'='*60}\n")

    async def run_swarm(self, total_tasks: int = 1000):
        """Run the full swarm."""
        # Validate system capacity before starting
        if not self.validate_max_agent_capacity():
            print("❌ Validation failed. Aborting swarm run.")
            return None
        
        self.stats["start_time"] = time.time()
        await self.init_session()

        print(f"""
{'='*60}
     KIMI 100K SWARM - MAURICE'S AI EMPIRE
{'='*60}
   Total Tasks:  {total_tasks:,}
   Max Capacity: {TOTAL_AGENTS:,}
   Concurrent:   {MAX_CONCURRENT}
   Budget:       ${BUDGET_USD}
   Output:       {OUTPUT_DIR}
{'='*60}
""")

        batch_size = min(MAX_CONCURRENT, total_tasks)
        batches = (total_tasks + batch_size - 1) // batch_size
        task_id = 0

        try:
            for batch in range(batches):
                if self.stats["cost_usd"] >= BUDGET_USD * 0.95:
                    print("Budget nearly exhausted! Stopping...")
                    break

                remaining = total_tasks - task_id
                current_batch = min(batch_size, remaining)

                print(f"Batch {batch + 1}/{batches} ({current_batch} tasks)...")
                await self.run_batch(task_id, current_batch)
                task_id += current_batch

                # Small delay between batches to avoid rate limits
                await asyncio.sleep(BATCH_DELAY)

                # Progress update every 5 batches
                if (batch + 1) % 5 == 0:
                    self.print_stats()

        finally:
            await self.close_session()

        self.print_stats()

        # Save final stats
        output_file = OUTPUT_DIR / f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump({
                "completed": self.stats["completed"],
                "failed": self.stats["failed"],
                "tokens_used": self.stats["tokens_used"],
                "cost_usd": self.stats["cost_usd"],
                "by_type": self.stats["by_type"],
                "duration_sec": time.time() - self.stats["start_time"]
            }, f, indent=2)

        print(f"Stats saved to: {output_file}")
        print("\nResults in:")
        print(f"  Leads:       {LEADS_DIR}")
        print(f"  Content:     {CONTENT_DIR}")
        print(f"  Competitors: {COMPETITORS_DIR}")
        print(f"  Nuggets:     {NUGGETS_DIR}")

        return self.stats


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="KIMI 100K Swarm")
    parser.add_argument("-n", "--tasks", type=int, default=1000, help="Number of tasks (default: 1000, max: 100000)")
    parser.add_argument("--test", action="store_true", help="Test mode (10 tasks)")
    parser.add_argument("--max", action="store_true", help="Max mode - spawn all 100K agents (WARNING: expensive!)")
    args = parser.parse_args()

    if args.test:
        num_tasks = 10
    elif args.max:
        num_tasks = TOTAL_AGENTS
        print(f"⚠️  WARNING: Running MAX 100K agents (~${BUDGET_USD} cost)")
        print("⚠️  Press Ctrl+C within 5 seconds to cancel...")
        await asyncio.sleep(5)
    else:
        num_tasks = min(args.tasks, TOTAL_AGENTS)

    swarm = KimiSwarm()
    await swarm.run_swarm(total_tasks=num_tasks)


if __name__ == "__main__":
    asyncio.run(main())
