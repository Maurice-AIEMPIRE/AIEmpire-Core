#!/usr/bin/env python3
"""
Feed Scanner Agent — Analyzes feeds for knowledge + open source tools
=====================================================================
Scans multiple sources for:
  1. Latest AI/tech trends from your feeds
  2. Open source software that can be implemented
  3. Cloud-native tools for the empire system
  4. Competitive intelligence

Sources (no API keys needed):
  - Hacker News (API: free, no auth)
  - GitHub Trending (API: free, no auth)
  - DEV.to (API: free, no auth)
  - Reddit r/selfhosted, r/opensource (API: free)

Usage:
    python3 -m antigravity.feed_scanner scan     # Scan all feeds
    python3 -m antigravity.feed_scanner github   # GitHub trending only
    python3 -m antigravity.feed_scanner hn       # Hacker News only
    python3 -m antigravity.feed_scanner oss      # Open source tools search
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


class FeedScanner:
    """Scans public feeds for trends and open source tools."""

    def __init__(self):
        self.results_dir = ROOT / "empire_data" / "feed_scans"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def scan_hackernews(self, limit: int = 30) -> dict:
        """Scan Hacker News top stories (free API, no auth)."""
        import httpx
        print("  Scanning Hacker News...")
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Get top story IDs
                r = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
                story_ids = r.json()[:limit]

                stories = []
                for sid in story_ids[:15]:  # Top 15 for speed
                    r = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
                    item = r.json()
                    if item and item.get("title"):
                        stories.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "score": item.get("score", 0),
                            "comments": item.get("descendants", 0),
                            "type": item.get("type", ""),
                        })

            # Filter AI/tech/open source related
            keywords = ["ai", "llm", "open source", "agent", "automation",
                        "self-host", "cloud", "kubernetes", "docker",
                        "python", "rust", "api", "saas", "startup"]
            relevant = []
            for s in stories:
                title_lower = s["title"].lower()
                if any(kw in title_lower for kw in keywords):
                    relevant.append(s)

            return {
                "source": "hackernews",
                "total": len(stories),
                "relevant": len(relevant),
                "stories": stories,
                "ai_relevant": relevant,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"source": "hackernews", "error": str(e)}

    async def scan_github_trending(self) -> dict:
        """Scan GitHub trending repos (scrape-free API approach)."""
        import httpx
        print("  Scanning GitHub Trending...")
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Use GitHub search API (no auth needed, 10 req/min)
                queries = [
                    "stars:>100 pushed:>2026-01-01 topic:ai-agents",
                    "stars:>50 pushed:>2026-01-01 topic:self-hosted",
                    "stars:>100 pushed:>2026-01-01 topic:automation",
                    "stars:>50 pushed:>2026-01-01 topic:llm",
                ]
                all_repos = []
                for q in queries:
                    try:
                        r = await client.get(
                            "https://api.github.com/search/repositories",
                            params={"q": q, "sort": "stars", "per_page": 10},
                            headers={"Accept": "application/vnd.github.v3+json"},
                        )
                        if r.status_code == 200:
                            items = r.json().get("items", [])
                            for repo in items:
                                all_repos.append({
                                    "name": repo["full_name"],
                                    "description": (repo.get("description") or "")[:200],
                                    "stars": repo["stargazers_count"],
                                    "language": repo.get("language", ""),
                                    "url": repo["html_url"],
                                    "topics": repo.get("topics", [])[:5],
                                    "updated": repo.get("updated_at", ""),
                                })
                        await asyncio.sleep(1)  # Rate limit
                    except Exception:
                        continue

                # Deduplicate
                seen = set()
                unique = []
                for r in all_repos:
                    if r["name"] not in seen:
                        seen.add(r["name"])
                        unique.append(r)

                # Sort by stars
                unique.sort(key=lambda x: x["stars"], reverse=True)

            return {
                "source": "github_trending",
                "total": len(unique),
                "repos": unique[:20],
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"source": "github_trending", "error": str(e)}

    async def scan_open_source_tools(self) -> dict:
        """Scan for cloud-native open source tools to implement."""
        import httpx
        print("  Scanning for open source cloud tools...")
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Search for self-hostable, cloud-native tools
                searches = [
                    "stars:>500 topic:self-hosted language:python",
                    "stars:>200 topic:ai topic:self-hosted",
                    "stars:>100 topic:automation topic:cloud-native",
                    "stars:>500 topic:n8n OR topic:workflow",
                ]
                tools = []
                for q in searches:
                    try:
                        r = await client.get(
                            "https://api.github.com/search/repositories",
                            params={"q": q, "sort": "updated", "per_page": 5},
                            headers={"Accept": "application/vnd.github.v3+json"},
                        )
                        if r.status_code == 200:
                            for repo in r.json().get("items", []):
                                tools.append({
                                    "name": repo["full_name"],
                                    "description": (repo.get("description") or "")[:200],
                                    "stars": repo["stargazers_count"],
                                    "language": repo.get("language", ""),
                                    "url": repo["html_url"],
                                    "license": (repo.get("license") or {}).get("spdx_id", "unknown"),
                                    "topics": repo.get("topics", [])[:5],
                                })
                        await asyncio.sleep(1.5)
                    except Exception:
                        continue

                # Deduplicate + sort
                seen = set()
                unique = []
                for t in tools:
                    if t["name"] not in seen:
                        seen.add(t["name"])
                        unique.append(t)
                unique.sort(key=lambda x: x["stars"], reverse=True)

            return {
                "source": "open_source_tools",
                "total": len(unique),
                "tools": unique[:15],
                "categories": {
                    "ai_agents": [t for t in unique if any(k in str(t.get("topics",[])) for k in ["ai","agent","llm"])],
                    "automation": [t for t in unique if any(k in str(t.get("topics",[])) for k in ["automation","workflow","n8n"])],
                    "self_hosted": [t for t in unique if "self-hosted" in str(t.get("topics",[]))],
                },
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"source": "open_source_tools", "error": str(e)}

    async def analyze_with_ai(self, scan_data: dict) -> dict:
        """Use local AI to analyze scan results."""
        try:
            from antigravity.provider_chain import get_chain
            chain = get_chain()

            summary_prompt = f"""Analysiere diese Feed-Daten und erstelle eine Zusammenfassung:

DATEN:
{json.dumps(scan_data, indent=2, ensure_ascii=False, default=str)[:3000]}

Erstelle eine strukturierte Analyse:
1. Top 3 Trends die JETZT relevant sind
2. Top 3 Open Source Tools die man SOFORT implementieren sollte
3. Top 3 Opportunities fuer Revenue

Antworte auf Deutsch. Kurz und actionable."""

            result = await chain.query(
                prompt=summary_prompt,
                system="Du bist ein Tech-Analyst der Trends und Tools bewertet. Fokus: Praktisch umsetzbar.",
                prefer="ollama",
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def full_scan(self) -> dict:
        """Run complete scan of all sources."""
        print("\n=== FULL FEED SCAN ===\n")

        results = {}

        # Parallel scans
        hn_task = self.scan_hackernews()
        gh_task = self.scan_github_trending()
        oss_task = self.scan_open_source_tools()

        results["hackernews"], results["github"], results["open_source"] = \
            await asyncio.gather(hn_task, gh_task, oss_task)

        # Save raw results
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.results_dir / f"scan_{ts}.json"
        path.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        print(f"\n  Saved to: {path}")

        # AI Analysis (optional, needs Ollama)
        print("\n  AI-Analyse laeuft...")
        analysis = await self.analyze_with_ai(results)
        results["ai_analysis"] = analysis

        # Summary
        print(f"\n=== SCAN ERGEBNIS ===")
        print(f"  Hacker News: {results['hackernews'].get('total', 0)} stories, {results['hackernews'].get('relevant', 0)} AI-relevant")
        print(f"  GitHub: {results['github'].get('total', 0)} trending repos")
        print(f"  Open Source: {results['open_source'].get('total', 0)} tools gefunden")

        if analysis.get("success"):
            print(f"\n  AI Analyse:\n{analysis.get('content', '')[:500]}")

        return results

    def _save(self, name: str, data: dict):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.results_dir / f"{name}_{ts}.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))


# ─── CLI ──────────────────────────────────────────────────────

async def _main():
    import argparse
    parser = argparse.ArgumentParser(description="Feed Scanner")
    parser.add_argument("command", nargs="?", default="scan",
                        choices=["scan", "hn", "github", "oss"])
    args = parser.parse_args()

    scanner = FeedScanner()

    if args.command == "scan":
        await scanner.full_scan()
    elif args.command == "hn":
        r = await scanner.scan_hackernews()
        print(json.dumps(r, indent=2, ensure_ascii=False)[:2000])
    elif args.command == "github":
        r = await scanner.scan_github_trending()
        print(json.dumps(r, indent=2, ensure_ascii=False)[:2000])
    elif args.command == "oss":
        r = await scanner.scan_open_source_tools()
        print(json.dumps(r, indent=2, ensure_ascii=False)[:2000])


if __name__ == "__main__":
    asyncio.run(_main())
