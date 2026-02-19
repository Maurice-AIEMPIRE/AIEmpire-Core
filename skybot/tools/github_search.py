"""
GitHub Search Tool
==================
Search GitHub repositories, trending repos, and user profiles.
Uses GitHub API (with optional token for higher rate limits).
"""

import aiohttp

from skybot.tools.base import BaseTool
from skybot.config import GITHUB_TOKEN, WEB_TIMEOUT


class GitHubSearchTool(BaseTool):
    name = "github_search"
    description = "Search GitHub for repositories, code, trending projects, or user profiles."

    def definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'AI agent framework', 'telegram bot python').",
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["repositories", "code", "users", "trending"],
                        "description": "What to search for. Default: 'repositories'.",
                    },
                    "language": {
                        "type": "string",
                        "description": "Filter by programming language (e.g., 'python', 'javascript').",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["stars", "forks", "updated", "best-match"],
                        "description": "Sort order. Default: 'best-match'.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max results to return (1-20). Default: 5.",
                    },
                },
                "required": ["query"],
            },
        }

    async def execute(
        self,
        query: str,
        search_type: str = "repositories",
        language: str = "",
        sort: str = "best-match",
        max_results: int = 5,
        **kwargs,
    ) -> str:
        max_results = min(max_results, 20)

        if search_type == "trending":
            return await self._trending(language or "python")

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SkyBot-AIEmpire",
        }
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

        if search_type == "repositories":
            return await self._search_repos(query, language, sort, max_results, headers)
        elif search_type == "code":
            return await self._search_code(query, language, max_results, headers)
        elif search_type == "users":
            return await self._search_users(query, max_results, headers)
        else:
            return f"Unknown search type: {search_type}"

    async def _search_repos(self, query: str, language: str, sort: str, limit: int, headers: dict) -> str:
        q = query
        if language:
            q += f" language:{language}"

        params = {"q": q, "sort": sort if sort != "best-match" else "", "per_page": limit}
        url = "https://api.github.com/search/repositories"

        try:
            timeout = aiohttp.ClientTimeout(total=WEB_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        return f"GitHub API error: HTTP {resp.status}"
                    data = await resp.json()
        except Exception as e:
            return f"GitHub request error: {e}"

        items = data.get("items", [])
        if not items:
            return f"No repositories found for: {query}"

        results = [f"GitHub repositories for '{query}' ({data.get('total_count', 0)} total):\n"]
        for i, repo in enumerate(items[:limit]):
            results.append(
                f"[{i+1}] {repo['full_name']}\n"
                f"    Stars: {repo['stargazers_count']:,} | Forks: {repo['forks_count']:,}\n"
                f"    Language: {repo.get('language', 'N/A')}\n"
                f"    Description: {repo.get('description', 'N/A')}\n"
                f"    URL: {repo['html_url']}"
            )

        return "\n\n".join(results)

    async def _search_code(self, query: str, language: str, limit: int, headers: dict) -> str:
        q = query
        if language:
            q += f" language:{language}"

        params = {"q": q, "per_page": limit}
        url = "https://api.github.com/search/code"

        try:
            timeout = aiohttp.ClientTimeout(total=WEB_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        return f"GitHub API error: HTTP {resp.status}"
                    data = await resp.json()
        except Exception as e:
            return f"GitHub request error: {e}"

        items = data.get("items", [])
        if not items:
            return f"No code found for: {query}"

        results = [f"GitHub code search for '{query}':\n"]
        for i, item in enumerate(items[:limit]):
            results.append(
                f"[{i+1}] {item['repository']['full_name']}/{item['path']}\n"
                f"    URL: {item['html_url']}"
            )

        return "\n\n".join(results)

    async def _search_users(self, query: str, limit: int, headers: dict) -> str:
        params = {"q": query, "per_page": limit}
        url = "https://api.github.com/search/users"

        try:
            timeout = aiohttp.ClientTimeout(total=WEB_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        return f"GitHub API error: HTTP {resp.status}"
                    data = await resp.json()
        except Exception as e:
            return f"GitHub request error: {e}"

        items = data.get("items", [])
        if not items:
            return f"No users found for: {query}"

        results = [f"GitHub users for '{query}':\n"]
        for i, user in enumerate(items[:limit]):
            results.append(
                f"[{i+1}] {user['login']}\n"
                f"    Profile: {user['html_url']}\n"
                f"    Type: {user.get('type', 'User')}"
            )

        return "\n\n".join(results)

    async def _trending(self, language: str) -> str:
        """Scrape GitHub trending page (no API needed)."""
        url = f"https://github.com/trending/{language}?since=daily"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=WEB_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        return f"Trending page error: HTTP {resp.status}"
                    html = await resp.text()
        except Exception as e:
            return f"Trending request error: {e}"

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        repos = soup.select("article.Box-row")
        if not repos:
            return f"No trending repos found for: {language}"

        results = [f"Trending {language} repositories (today):\n"]
        for i, repo in enumerate(repos[:10]):
            name_el = repo.select_one("h2 a")
            desc_el = repo.select_one("p")
            stars_el = repo.select_one("span.d-inline-block.float-sm-right")

            name = name_el.get_text(strip=True).replace("\n", "").replace(" ", "") if name_el else "?"
            desc = desc_el.get_text(strip=True) if desc_el else "No description"
            stars = stars_el.get_text(strip=True) if stars_el else ""

            results.append(f"[{i+1}] {name}\n    {desc}\n    {stars}")

        return "\n\n".join(results)
