"""
Web Search & Browse Tool
========================
Fetches web pages and extracts text content.
Uses aiohttp + BeautifulSoup for safe, read-only web access.
"""

import re
from urllib.parse import quote_plus

import aiohttp
from bs4 import BeautifulSoup

from skybot.tools.base import BaseTool
from skybot.config import WEB_TIMEOUT


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web or fetch a specific URL and extract text content."

    def definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (uses DuckDuckGo) OR a full URL to fetch directly.",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["search", "fetch"],
                        "description": "'search' for web search, 'fetch' to get a specific URL. Default: 'search'.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max number of search results to return (1-10). Default: 5.",
                    },
                },
                "required": ["query"],
            },
        }

    async def execute(self, query: str, mode: str = "search", max_results: int = 5, **kwargs) -> str:
        if mode == "fetch" or query.startswith("http"):
            return await self._fetch_url(query)
        return await self._search(query, min(max_results, 10))

    async def _search(self, query: str, max_results: int) -> str:
        """Search via DuckDuckGo HTML (no API key needed)."""
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=WEB_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        return f"Search failed: HTTP {resp.status}"
                    html = await resp.text()
        except Exception as e:
            return f"Search error: {e}"

        soup = BeautifulSoup(html, "html.parser")
        results = []

        for i, result in enumerate(soup.select(".result")):
            if i >= max_results:
                break
            title_el = result.select_one(".result__title")
            snippet_el = result.select_one(".result__snippet")
            link_el = result.select_one(".result__url")

            title = title_el.get_text(strip=True) if title_el else "No title"
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            link = link_el.get_text(strip=True) if link_el else ""

            results.append(f"[{i+1}] {title}\n    URL: {link}\n    {snippet}")

        if not results:
            return f"No results found for: {query}"

        return f"Search results for '{query}':\n\n" + "\n\n".join(results)

    async def _fetch_url(self, url: str) -> str:
        """Fetch a URL and extract readable text."""
        if not url.startswith("http"):
            url = "https://" + url

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=WEB_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers, allow_redirects=True) as resp:
                    if resp.status != 200:
                        return f"Fetch failed: HTTP {resp.status}"
                    content_type = resp.headers.get("Content-Type", "")
                    if "text/html" not in content_type and "text/plain" not in content_type:
                        return f"Non-text content: {content_type}"
                    html = await resp.text()
        except Exception as e:
            return f"Fetch error: {e}"

        soup = BeautifulSoup(html, "html.parser")

        # Remove script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Clean up multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return self._truncate(f"Content from {url}:\n\n{text}")
