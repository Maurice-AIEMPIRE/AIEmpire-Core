#!/usr/bin/env python3
"""
500.000 KIMI AGENTS SWARM - WITH CLAUDE ORCHESTRATION
Maurice's AI Empire - Maximum Money-Making Power
Budget: $75 = ~150 Mio Tokens (scaled 5x from 100K system)
Orchestrated by Claude agents for optimal revenue generation
"""

import asyncio
import aiohttp
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import random

# API Keys - MUST be set as environment variables
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
if not MOONSHOT_API_KEY:
    raise ValueError("MOONSHOT_API_KEY environment variable must be set")
    
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # Optional: Falls back to rule-based orchestration

# Configuration
MAX_CONCURRENT = 500  # 10x increase for 500K scale
TOTAL_AGENTS = 500000
BUDGET_USD = 75.0  # 5x budget for 5x agents
BATCH_DELAY = 0.1  # Faster batches with better concurrency
CLAUDE_ORCHESTRATION_INTERVAL = 1000  # Claude reviews every 1000 tasks

# Output directories
OUTPUT_DIR = Path(__file__).parent / "output_500k"
LEADS_DIR = OUTPUT_DIR / "leads"
CONTENT_DIR = OUTPUT_DIR / "content"
COMPETITORS_DIR = OUTPUT_DIR / "competitors"
NUGGETS_DIR = OUTPUT_DIR / "gold_nuggets"
REVENUE_OPS_DIR = OUTPUT_DIR / "revenue_operations"
CLAUDE_INSIGHTS_DIR = OUTPUT_DIR / "claude_insights"

# Create directories
for d in [OUTPUT_DIR, LEADS_DIR, CONTENT_DIR, COMPETITORS_DIR, NUGGETS_DIR, REVENUE_OPS_DIR, CLAUDE_INSIGHTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Enhanced Task Types für maximale Revenue-Generation
TASK_TYPES = [
    {
        "type": "high_value_lead_research",
        "output_dir": LEADS_DIR,
        "priority": "high",
        "revenue_potential": 5000,
        "prompt": """Du bist ein High-Value B2B Lead Research Agent. Generiere ein REALISTISCHES Premium-Lead-Profil.

Zielgruppe: Enterprise/Mid-Market Unternehmen die 10K-100K+ EUR für AI-Automation ausgeben können.
Branchen: SaaS, E-Commerce, Manufacturing, Finance, Healthcare

OUTPUT als JSON:
{
    "handle": "@beispiel_firma",
    "company": "Firmenname",
    "industry": "Branche",
    "company_size": "50-500 employees",
    "annual_revenue": "5M-50M EUR",
    "pain_points": ["Problem 1", "Problem 2", "Problem 3"],
    "ai_opportunity": "Konkrete AI-Lösung Beschreibung",
    "estimated_project_value": "25000 EUR",
    "decision_maker": "CTO/CEO title",
    "outreach_hook": "Personalisierter erster Satz",
    "priority": "high",
    "bant_score": 8
}"""
    },
    {
        "type": "viral_content_idea",
        "output_dir": CONTENT_DIR,
        "priority": "high",
        "revenue_potential": 1000,
        "prompt": """Generiere eine VIRALE X/Twitter Content-Idee mit Lead-Gen Hook.

Fokus: AI-Automation Success Stories, Behind-the-Scenes, Controversial Takes
Ziel: Max. Engagement + Lead-Magnets einbauen

OUTPUT als JSON:
{
    "format": "thread/single/meme/story",
    "hook": "Attention-grabbing erster Satz",
    "main_content": "Story/Insight/Take mit konkreten Zahlen",
    "cta": "Call to Action mit Lead-Magnet (Free Guide/Template/Audit)",
    "lead_magnet": "Kostenloser Download Titel",
    "hashtags": ["#AI", "#Automation", "#BuildInPublic"],
    "viral_score": 8,
    "estimated_reach": 50000,
    "lead_conversion_rate": "2-5%"
}"""
    },
    {
        "type": "competitor_intel",
        "output_dir": COMPETITORS_DIR,
        "priority": "medium",
        "revenue_potential": 2000,
        "prompt": """Analysiere einen FIKTIVEN AI-Automation Konkurrenten mit strategischen Schwachstellen.

OUTPUT als JSON:
{
    "name": "Konkurrenten Name",
    "positioning": "Ihr USP",
    "services": ["Service 1", "Service 2", "Service 3"],
    "pricing": "Preismodell Details",
    "strengths": ["Stärke 1", "Stärke 2"],
    "weaknesses": ["Kritische Schwäche 1", "Schwäche 2"],
    "market_gap": "Opportunity für Maurice",
    "recommended_counter_strategy": "Wie Maurice gewinnt",
    "estimated_market_share": "5-15%",
    "vulnerability_score": 7
}"""
    },
    {
        "type": "gold_nugget_extraction",
        "output_dir": NUGGETS_DIR,
        "priority": "high",
        "revenue_potential": 10000,
        "prompt": """Extrahiere ein HIGH-VALUE Gold Nugget - Business Intelligence für sofortiges Money-Making.

Kategorien: Monetarisierung, Skalierung, Automation, Arbitrage-Opportunity

OUTPUT als JSON:
{
    "category": "monetization/scaling/automation/arbitrage",
    "title": "Actionable Titel",
    "insight": "Die konkrete Business-Erkenntnis mit Zahlen",
    "implementation_steps": ["Schritt 1", "Schritt 2", "Schritt 3"],
    "estimated_revenue": "10000 EUR/Monat",
    "implementation_time": "1-4 Wochen",
    "required_investment": "500 EUR",
    "roi_multiplier": "20x",
    "priority": "critical",
    "competitive_moat": "Wie defensible ist das?"
}"""
    },
    {
        "type": "revenue_optimization",
        "output_dir": REVENUE_OPS_DIR,
        "priority": "critical",
        "revenue_potential": 15000,
        "prompt": """Du bist Revenue Optimization Agent. Identifiziere eine konkrete Revenue-Optimierung.

Bereiche: Pricing, Upsells, Process Automation, Cost Reduction, New Revenue Stream

OUTPUT als JSON:
{
    "optimization_type": "pricing/upsell/automation/cost_reduction/new_stream",
    "current_state": "Problem/Ineffizienz",
    "optimized_state": "Lösung",
    "revenue_impact": "5000 EUR/Monat additional",
    "implementation_complexity": "low/medium/high",
    "time_to_value": "1-2 Wochen",
    "required_resources": ["Resource 1", "Resource 2"],
    "success_metrics": ["Metric 1", "Metric 2"],
    "priority_score": 9
}"""
    },
    {
        "type": "strategic_partnership",
        "output_dir": REVENUE_OPS_DIR,
        "priority": "high",
        "revenue_potential": 20000,
        "prompt": """Identifiziere eine strategische Partnership-Opportunity für AI-Automation Business.

OUTPUT als JSON:
{
    "partner_type": "technology/distribution/complementary_service",
    "partner_profile": "Ideales Partner-Profil",
    "value_proposition": "Win-Win Proposition",
    "revenue_model": "Wie wird Geld verdient",
    "estimated_annual_value": "50000 EUR",
    "partnership_effort": "Aufwand zum Setup",
    "strategic_value": "Langfristige strategische Bedeutung",
    "first_outreach_approach": "Wie initiieren",
    "priority": "high"
}"""
    },
]

class ClaudeOrchestrator:
    """Claude Agent Army für strategische Orchestrierung"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.insights = []
        
    async def analyze_swarm_progress(self, stats: Dict, recent_results: List[Dict]) -> Dict:
        """Claude analysiert Swarm Progress und gibt strategische Empfehlungen."""
        
        if not self.api_key:
            # Fallback: Simple rule-based recommendations
            return {
                "status": "rule_based",
                "recommendations": [
                    "Continue with current task distribution",
                    "Focus on high-value lead research",
                    "Optimize for revenue-generating tasks"
                ],
                "task_priority_adjustment": "none"
            }
        
        prompt = f"""Du bist Lead Claude Orchestrator für eine 500K Kimi Agent Army.

Aktueller Status:
- Completed Tasks: {stats.get('completed', 0)}
- Tokens Used: {stats.get('tokens_used', 0)}
- Cost: ${stats.get('cost_usd', 0):.2f}
- Task Distribution: {stats.get('by_type', {})}

Sample Results (letzte 5):
{json.dumps(recent_results[-5:], indent=2)}

Deine Aufgabe:
1. Evaluiere Swarm Performance
2. Identifiziere High-Value Patterns
3. Empfehle Task-Priority Adjustments für maximale Revenue
4. Spot Optimization-Opportunities

Return JSON:
{{
    "performance_rating": "1-10",
    "key_insights": ["Insight 1", "Insight 2"],
    "recommendations": ["Action 1", "Action 2"],
    "task_priority_adjustment": "mehr_leads/mehr_content/mehr_nuggets/balanced",
    "estimated_revenue_impact": "5000 EUR increase potential",
    "critical_actions": ["Must-do 1", "Must-do 2"]
}}"""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",  # Fast & cheap for orchestration
                        "max_tokens": 1024,
                        "messages": [{
                            "role": "user",
                            "content": prompt
                        }]
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["content"][0]["text"]
                        
                        # Save insight
                        insight_file = CLAUDE_INSIGHTS_DIR / f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(insight_file, "w") as f:
                            json.dump({"timestamp": datetime.now().isoformat(), "analysis": content}, f, indent=2)
                        
                        # Parse response
                        try:
                            analysis = json.loads(content)
                            self.insights.append(analysis)
                            return analysis
                        except json.JSONDecodeError as e:
                            # Claude returned non-JSON response - save but continue
                            return {"status": "parse_error", "raw": content, "error": str(e)}
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            # Network or timeout error - log and fallback to rule-based
            print(f"  ⚠️  Claude API error: {type(e).__name__}: {str(e)[:100]}")
        except Exception as e:
            # Unexpected error - log for debugging
            print(f"  ⚠️  Unexpected error in Claude orchestration: {type(e).__name__}: {str(e)[:100]}")
        
        # Fallback
        return {
            "status": "fallback",
            "recommendations": ["Continue current operations"],
            "task_priority_adjustment": "balanced"
        }

class KimiSwarm500K:
    """Enhanced Swarm System for 500K Agents"""
    
    def __init__(self):
        self.stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "tokens_used": 0,
            "cost_usd": 0.0,
            "start_time": None,
            "results": [],
            "by_type": {t["type"]: 0 for t in TASK_TYPES},
            "estimated_revenue": 0.0,
            "claude_orchestrations": 0
        }
        self.running = True
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        self.session = None
        self.task_counter = 0
        self.recent_results = []
        self.claude = ClaudeOrchestrator(ANTHROPIC_API_KEY)
        self.task_weights = [1.0] * len(TASK_TYPES)  # Dynamic task prioritization
        
    def validate_max_agent_capacity(self) -> bool:
        """Validate that system is configured to spawn max agents."""
        print(f"\n{'='*60}")
        print(f"🔍 VALIDATING MAX AGENT CAPACITY")
        print(f"{'='*60}")
        
        validation_passed = True
        
        # Check TOTAL_AGENTS configuration
        print(f"Total Agents Capacity: {TOTAL_AGENTS:,}")
        if TOTAL_AGENTS <= 0:
            print(f"  ❌ TOTAL_AGENTS must be > 0")
            validation_passed = False
        else:
            print(f"  ✅ Valid agent capacity configured")
        
        # Check MAX_CONCURRENT configuration
        print(f"Max Concurrent Workers: {MAX_CONCURRENT}")
        if MAX_CONCURRENT <= 0:
            print(f"  ❌ MAX_CONCURRENT must be > 0")
            validation_passed = False
        elif MAX_CONCURRENT > 1000:
            print(f"  ⚠️  Warning: MAX_CONCURRENT > 1000 may cause rate limiting")
        else:
            print(f"  ✅ Valid concurrency level")
        
        # Check API key is set
        if not MOONSHOT_API_KEY:
            print(f"  ❌ MOONSHOT_API_KEY not set")
            validation_passed = False
        else:
            print(f"  ✅ API key configured")
        
        # Check semaphore capacity
        if self.semaphore._value != MAX_CONCURRENT:
            print(f"  ❌ Semaphore capacity mismatch")
            validation_passed = False
        else:
            print(f"  ✅ Semaphore initialized correctly")
        
        # Check output directories exist
        for dir_path in [OUTPUT_DIR, LEADS_DIR, CONTENT_DIR, COMPETITORS_DIR, NUGGETS_DIR, REVENUE_OPS_DIR, CLAUDE_INSIGHTS_DIR]:
            if not dir_path.exists():
                print(f"  ❌ Output directory missing: {dir_path}")
                validation_passed = False
        print(f"  ✅ All output directories exist")
        
        # Capacity report
        estimated_time = (TOTAL_AGENTS / MAX_CONCURRENT) * 0.5  # Rough estimate at 0.5s per task
        print(f"\nCapacity Report:")
        print(f"  • Max Agents: {TOTAL_AGENTS:,}")
        print(f"  • Concurrent Workers: {MAX_CONCURRENT}")
        print(f"  • Estimated Time for Full Run: {estimated_time/3600:.1f} hours")
        print(f"  • Estimated Cost: ${BUDGET_USD:.2f}")
        
        if validation_passed:
            print(f"\n✅ System validated - ready to spawn max agents!")
        else:
            print(f"\n❌ Validation failed - fix issues before spawning agents")
        
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
            data = {
                "task_id": task_id,
                "type": task_type["type"],
                "priority": task_type.get("priority", "medium"),
                "revenue_potential": task_type.get("revenue_potential", 0),
                "timestamp": datetime.now().isoformat(),
                "data": parsed
            }
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            # JSON parsing failed - save raw content for manual review
            data = {
                "task_id": task_id,
                "type": task_type["type"],
                "timestamp": datetime.now().isoformat(),
                "raw": content,
                "parse_error": str(e)
            }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Track for Claude analysis
        self.recent_results.append(data)
        if len(self.recent_results) > 100:
            self.recent_results.pop(0)

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
                                {"role": "system", "content": "Du bist ein Elite Research Agent. Antworte NUR mit validem JSON. Fokus auf Qualität und Revenue-Impact."},
                                {"role": "user", "content": task_type["prompt"]}
                            ],
                            "temperature": 0.8,
                            "max_tokens": 500
                        }
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = data["choices"][0]["message"]["content"]
                            tokens = data.get("usage", {}).get("total_tokens", 400)

                            self.stats["completed"] += 1
                            self.stats["tokens_used"] += tokens
                            self.stats["by_type"][task_type["type"]] += 1
                            # Kimi moonshot-v1-8k: $0.0005 per 1K tokens
                            self.stats["cost_usd"] += (tokens / 1000) * 0.0005
                            self.stats["estimated_revenue"] += task_type.get("revenue_potential", 0) * 0.1  # 10% conversion rate assumption

                            # Save to file
                            self.save_result(task_id, task_type, content)

                            return {
                                "task_id": task_id,
                                "type": task_type["type"],
                                "status": "success",
                                "tokens": tokens,
                                "revenue_potential": task_type.get("revenue_potential", 0)
                            }
                        elif resp.status == 429:
                            # Rate limited
                            wait = (2 ** attempt) + random.uniform(0, 1)
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

    def select_task_type(self, task_id: int) -> Dict:
        """Intelligently select task type based on weights."""
        # Weighted random selection
        total_weight = sum(self.task_weights)
        rand_val = random.uniform(0, total_weight)
        
        cumulative = 0
        for i, weight in enumerate(self.task_weights):
            cumulative += weight
            if rand_val <= cumulative:
                return TASK_TYPES[i]
        
        # Fallback
        return TASK_TYPES[task_id % len(TASK_TYPES)]

    async def run_batch(self, start_id: int, count: int) -> List[Dict]:
        """Run a batch of tasks."""
        tasks = []
        for i in range(count):
            task_id = start_id + i
            task_type = self.select_task_type(task_id)
            tasks.append(self.execute_task(task_id, task_type))
            self.stats["total_tasks"] += 1

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def claude_orchestration_checkpoint(self):
        """Let Claude analyze and adjust strategy."""
        self.stats["claude_orchestrations"] += 1
        
        print(f"\n{'='*60}")
        print(f"🧠 CLAUDE ORCHESTRATOR CHECKPOINT #{self.stats['claude_orchestrations']}")
        print(f"{'='*60}")
        
        analysis = await self.claude.analyze_swarm_progress(self.stats, self.recent_results)
        
        print(f"Status: {analysis.get('status', 'unknown')}")
        print(f"Performance Rating: {analysis.get('performance_rating', 'N/A')}")
        
        if "recommendations" in analysis:
            print(f"\nRecommendations:")
            for rec in analysis.get("recommendations", []):
                print(f"  • {rec}")
        
        if "task_priority_adjustment" in analysis:
            adjustment = analysis.get("task_priority_adjustment", "balanced")
            print(f"\nTask Priority Adjustment: {adjustment}")
            
            # Adjust task weights based on Claude's recommendation
            if adjustment == "mehr_leads":
                self.task_weights[0] = 2.0  # High value leads
                self.task_weights[5] = 1.5  # Partnerships
            elif adjustment == "mehr_content":
                self.task_weights[1] = 2.0  # Viral content
            elif adjustment == "mehr_nuggets":
                self.task_weights[3] = 2.0  # Gold nuggets
                self.task_weights[4] = 1.5  # Revenue ops
        
        print(f"{'='*60}\n")

    def print_stats(self):
        """Print current stats."""
        elapsed = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        rate = self.stats["completed"] / elapsed if elapsed > 0 else 0
        eta = (self.stats["total_tasks"] - self.stats["completed"]) / rate if rate > 0 else 0

        print(f"\n{'='*60}")
        print(f"💰 500K KIMI SWARM + CLAUDE ARMY - STATS")
        print(f"{'='*60}")
        print(f"Completed:      {self.stats['completed']:,} / {self.stats['total_tasks']:,}")
        print(f"Failed:         {self.stats['failed']:,}")
        print(f"Tokens Used:    {self.stats['tokens_used']:,}")
        print(f"Cost:           ${self.stats['cost_usd']:.4f} / ${BUDGET_USD:.2f}")
        print(f"Est. Revenue:   €{self.stats['estimated_revenue']:,.0f}")
        print(f"ROI:            {(self.stats['estimated_revenue'] / max(self.stats['cost_usd'], 0.01)):.1f}x")
        print(f"Rate:           {rate:.1f} tasks/sec")
        print(f"Elapsed:        {elapsed:.1f}s | ETA: {eta:.0f}s")
        print(f"Claude Checks:  {self.stats['claude_orchestrations']}")
        print(f"---")
        for task_type in TASK_TYPES:
            count = self.stats['by_type'].get(task_type['type'], 0)
            print(f"{task_type['type'][:25]:25s}: {count:,}")
        print(f"{'='*60}\n")

    async def run_swarm(self, total_tasks: int = 10000):
        """Run the full 500K swarm."""
        # Validate system capacity before starting
        if not self.validate_max_agent_capacity():
            print("❌ Validation failed. Aborting swarm run.")
            return None
        
        self.stats["start_time"] = time.time()
        await self.init_session()

        print(f"""
{'='*60}
   🚀 500K KIMI SWARM + CLAUDE ORCHESTRATION 🚀
      Maurice's AI Empire - Maximum Revenue
{'='*60}
   Total Tasks:  {total_tasks:,}
   Max Capacity: {TOTAL_AGENTS:,}
   Concurrent:   {MAX_CONCURRENT}
   Budget:       ${BUDGET_USD}
   Output:       {OUTPUT_DIR}
   Claude:       {"✅ Active" if ANTHROPIC_API_KEY else "❌ Disabled (rule-based fallback)"}
{'='*60}
""")

        batch_size = min(MAX_CONCURRENT, total_tasks)
        batches = (total_tasks + batch_size - 1) // batch_size
        task_id = 0

        try:
            for batch in range(batches):
                # Budget check
                if self.stats["cost_usd"] >= BUDGET_USD * 0.95:
                    print(f"💰 Budget limit reached! Stopping gracefully...")
                    break

                remaining = total_tasks - task_id
                current_batch = min(batch_size, remaining)

                await self.run_batch(task_id, current_batch)
                task_id += current_batch

                # Claude orchestration checkpoint
                if task_id % CLAUDE_ORCHESTRATION_INTERVAL == 0:
                    await self.claude_orchestration_checkpoint()

                # Progress update
                if (batch + 1) % 10 == 0:
                    self.print_stats()

                # Small delay between batches
                await asyncio.sleep(BATCH_DELAY)

        finally:
            await self.close_session()

        self.print_stats()

        # Save final stats
        output_file = OUTPUT_DIR / f"stats_500k_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump({
                "completed": self.stats["completed"],
                "failed": self.stats["failed"],
                "tokens_used": self.stats["tokens_used"],
                "cost_usd": self.stats["cost_usd"],
                "estimated_revenue_eur": self.stats["estimated_revenue"],
                "roi": self.stats["estimated_revenue"] / max(self.stats["cost_usd"], 0.01),
                "by_type": self.stats["by_type"],
                "duration_sec": time.time() - self.stats["start_time"],
                "claude_orchestrations": self.stats["claude_orchestrations"]
            }, f, indent=2)

        print(f"\n{'='*60}")
        print(f"✅ SWARM COMPLETE - MAURICE'S AI EMPIRE")
        print(f"{'='*60}")
        print(f"Stats saved:     {output_file}")
        print(f"Total Revenue:   €{self.stats['estimated_revenue']:,.0f}")
        print(f"Total Cost:      ${self.stats['cost_usd']:.2f}")
        print(f"ROI:             {(self.stats['estimated_revenue'] / max(self.stats['cost_usd'], 0.01)):.0f}x")
        print(f"\nResults in:")
        print(f"  Leads:         {LEADS_DIR}")
        print(f"  Content:       {CONTENT_DIR}")
        print(f"  Competitors:   {COMPETITORS_DIR}")
        print(f"  Gold Nuggets:  {NUGGETS_DIR}")
        print(f"  Revenue Ops:   {REVENUE_OPS_DIR}")
        print(f"  Claude:        {CLAUDE_INSIGHTS_DIR}")
        print(f"{'='*60}\n")

        return self.stats


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="500K KIMI Swarm with Claude Orchestration")
    parser.add_argument("-n", "--tasks", type=int, default=10000, help="Number of tasks (default: 10000, max: 500000)")
    parser.add_argument("--test", action="store_true", help="Test mode (100 tasks)")
    parser.add_argument("--full", action="store_true", help="Full 500K mode (WARNING: expensive!)")
    args = parser.parse_args()

    if args.test:
        num_tasks = 100
    elif args.full:
        num_tasks = TOTAL_AGENTS
        print(f"⚠️  WARNING: Running FULL 500K agents (~${BUDGET_USD} cost)")
        print(f"⚠️  Press Ctrl+C within 5 seconds to cancel...")
        await asyncio.sleep(5)
    else:
        num_tasks = min(args.tasks, TOTAL_AGENTS)

    swarm = KimiSwarm500K()
    await swarm.run_swarm(total_tasks=num_tasks)


if __name__ == "__main__":
    asyncio.run(main())
