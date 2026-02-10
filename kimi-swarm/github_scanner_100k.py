#!/usr/bin/env python3
"""
100K KIMI AGENTS - GITHUB SCANNER
Scannt GitHub nach den besten AI-Repos und Gold Nuggets
"""

import asyncio
import json
import os
from datetime import datetime

import aiohttp

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
MAX_CONCURRENT = 100

# GitHub Topics to scan
GITHUB_TOPICS = [
    "ai-agents",
    "llm",
    "langchain",
    "autogpt",
    "claude",
    "gpt-4",
    "automation",
    "chatgpt",
    "openai",
    "anthropic",
    "rag",
    "vector-database",
    "embeddings",
    "fine-tuning",
    "prompt-engineering",
    "ai-automation",
    "no-code-ai",
    "crewai",
    "autogen",
    "langraph",
    "llama",
    "ollama",
    "mistral",
    "agent-framework",
    "mcp",
    "model-context-protocol",
    "ai-tools",
    "ai-workflow",
    "business-automation",
    "saas",
    "indie-hacker",
    "build-in-public",
]

# Search queries for gold nuggets
GOLD_QUERIES = [
    "AI agent framework stars:>1000",
    "automation tool stars:>500",
    "LLM wrapper stars:>1000",
    "claude integration",
    "chatgpt api wrapper",
    "business automation python",
    "no-code AI builder",
    "AI SaaS template",
    "lead generation AI",
    "content automation",
]


class GitHubScanner:
    def __init__(self):
        self.results = []
        self.gold_nuggets = []
        self.stats = {
            "repos_scanned": 0,
            "nuggets_found": 0,
            "tokens_used": 0,
            "cost_usd": 0.0,
        }
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def analyze_repo(self, repo_info: str) -> dict:
        """Use Kimi to analyze a repo for gold nuggets."""
        async with self.semaphore:
            prompt = f"""Analyze this GitHub repo for business value:

{repo_info}

Questions:
1. What problem does it solve?
2. Can Maurice monetize this? How?
3. Is it production-ready or experimental?
4. Gold Nugget rating (1-10)
5. Recommended action (clone/study/ignore/monetize)

Return as JSON: {{problem, monetization, readiness, rating, action, reason}}"""

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        "https://api.moonshot.ai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "moonshot-v1-8k",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.5,
                            "max_tokens": 500,
                        },
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = data["choices"][0]["message"]["content"]
                            tokens = data.get("usage", {}).get("total_tokens", 300)
                            self.stats["tokens_used"] += tokens
                            self.stats["cost_usd"] += (tokens / 1000) * 0.0005
                            self.stats["repos_scanned"] += 1
                            return {"status": "success", "analysis": content}
                except Exception as e:
                    return {"status": "error", "error": str(e)}
            return {"status": "error", "error": "Unknown"}

    async def search_github(self, query: str) -> list:
        """Search GitHub API for repos."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=10",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("items", [])
            except Exception:
                pass
        return []

    async def scan_topics(self):
        """Scan all GitHub topics."""
        print("🔍 Scanning GitHub topics...")

        for topic in GITHUB_TOPICS[:10]:  # First 10 topics
            print(f"  📂 Topic: {topic}")
            repos = await self.search_github(f"topic:{topic}")

            for repo in repos[:5]:  # Top 5 per topic
                repo_info = f"""
Repo: {repo["full_name"]}
Stars: {repo["stargazers_count"]}
Description: {repo["description"]}
Language: {repo["language"]}
URL: {repo["html_url"]}
"""
                result = await self.analyze_repo(repo_info)
                if result["status"] == "success":
                    self.results.append(
                        {
                            "repo": repo["full_name"],
                            "stars": repo["stargazers_count"],
                            "url": repo["html_url"],
                            "analysis": result["analysis"],
                        }
                    )

                    # Check if it's a gold nugget
                    try:
                        analysis = json.loads(result["analysis"])
                        if analysis.get("rating", 0) >= 7:
                            self.gold_nuggets.append(
                                {
                                    "repo": repo["full_name"],
                                    "rating": analysis.get("rating"),
                                    "action": analysis.get("action"),
                                    "reason": analysis.get("reason"),
                                }
                            )
                            self.stats["nuggets_found"] += 1
                            print(f"    💰 GOLD: {repo['full_name']} (Rating: {analysis.get('rating')})")
                    except Exception:
                        pass

            print(f"    Scanned: {len(repos[:5])} repos")

    async def run(self):
        """Run the full scan."""
        print("=" * 60)
        print("100K KIMI AGENTS - GITHUB SCANNER")
        print("=" * 60)
        print()

        await self.scan_topics()

        # Save results
        output_file = f"github_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "stats": self.stats,
                    "gold_nuggets": self.gold_nuggets,
                    "all_results": self.results,
                },
                f,
                indent=2,
            )

        # Save gold nuggets separately
        if self.gold_nuggets:
            nuggets_file = "GITHUB_GOLD_NUGGETS.md"
            with open(nuggets_file, "w") as f:
                f.write("# 💰 GITHUB GOLD NUGGETS\n\n")
                f.write(f"Scanned: {datetime.now().isoformat()}\n")
                f.write(f"Repos analyzed: {self.stats['repos_scanned']}\n")
                f.write(f"Gold found: {self.stats['nuggets_found']}\n\n")
                f.write("---\n\n")

                for nugget in sorted(self.gold_nuggets, key=lambda x: x.get("rating", 0), reverse=True):
                    f.write(f"## {nugget['repo']}\n")
                    f.write(f"**Rating:** {nugget.get('rating')}/10\n")
                    f.write(f"**Action:** {nugget.get('action')}\n")
                    f.write(f"**Reason:** {nugget.get('reason')}\n\n")

            print(f"\n💰 Gold Nuggets saved: {nuggets_file}")

        # Print summary
        print("\n" + "=" * 60)
        print("SCAN COMPLETE")
        print("=" * 60)
        print(f"Repos Scanned:  {self.stats['repos_scanned']}")
        print(f"Gold Nuggets:   {self.stats['nuggets_found']}")
        print(f"Tokens Used:    {self.stats['tokens_used']:,}")
        print(f"Cost:           ${self.stats['cost_usd']:.4f}")
        print(f"Results:        {output_file}")


if __name__ == "__main__":
    scanner = GitHubScanner()
    asyncio.run(scanner.run())
