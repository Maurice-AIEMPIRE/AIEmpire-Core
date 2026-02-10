"""
Gemini API Client - Dual interface for the Mirror System.

Supports:
- gemini-2.0-flash (fast, cheap, 90% of calls)
- gemini-2.5-pro (deep thinking, 10% of calls)
- gemini-2.0-flash-thinking (experimental/creative)

Cost tracking on every call. Automatic fallback chain.
"""

import os
import json
import time
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime


class GeminiClient:
    """Async Gemini API client with cost tracking and rate limiting."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    MODELS = {
        "flash": "gemini-2.0-flash",
        "pro": "gemini-2.5-pro",
        "thinking": "gemini-2.0-flash-thinking",
    }

    # Approximate cost per 1M tokens (USD)
    COST_PER_1M = {
        "flash": {"input": 0.10, "output": 0.40},
        "pro": {"input": 1.25, "output": 10.00},
        "thinking": {"input": 0.10, "output": 0.40},
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set. Export it or pass to constructor.")

        self.total_tokens = 0
        self.total_cost_usd = 0.0
        self.call_count = 0
        self._rate_timestamps = []
        self._rate_limit_rpm = 60

    async def chat(
        self,
        prompt: str,
        tier: str = "flash",
        system_instruction: str = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        json_mode: bool = False,
    ) -> dict:
        """
        Send a chat request to Gemini.

        Args:
            prompt: The user message
            tier: "flash", "pro", or "thinking"
            system_instruction: Optional system prompt
            temperature: Creativity (0.0 - 2.0)
            max_tokens: Max output tokens
            json_mode: If True, request JSON output

        Returns:
            dict with keys: text, tokens, cost_usd, model, latency_ms
        """
        await self._rate_limit()

        model = self.MODELS.get(tier, self.MODELS["flash"])
        url = f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}"

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"

        start = time.time()

        async with aiohttp.ClientSession() as session:
            # Retry with exponential backoff
            for attempt in range(4):
                try:
                    async with session.post(
                        url,
                        json=body,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=120),
                    ) as resp:
                        if resp.status == 429:
                            wait = 2 ** (attempt + 1)
                            print(f"[GEMINI] Rate limited. Waiting {wait}s...")
                            await asyncio.sleep(wait)
                            continue

                        if resp.status != 200:
                            error_text = await resp.text()
                            return {
                                "text": "",
                                "error": f"HTTP {resp.status}: {error_text}",
                                "tokens": 0,
                                "cost_usd": 0,
                                "model": model,
                                "latency_ms": 0,
                            }

                        data = await resp.json()
                        break
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < 3:
                        wait = 2 ** (attempt + 1)
                        print(f"[GEMINI] Network error: {e}. Retry in {wait}s...")
                        await asyncio.sleep(wait)
                    else:
                        return {
                            "text": "",
                            "error": str(e),
                            "tokens": 0,
                            "cost_usd": 0,
                            "model": model,
                            "latency_ms": 0,
                        }

        latency_ms = int((time.time() - start) * 1000)

        # Extract response text
        text = ""
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            text = json.dumps(data, indent=2)

        # Token counting
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)
        total = input_tokens + output_tokens

        # Cost calculation
        costs = self.COST_PER_1M.get(tier, self.COST_PER_1M["flash"])
        cost = (input_tokens / 1_000_000) * costs["input"] + \
               (output_tokens / 1_000_000) * costs["output"]

        # Track totals
        self.total_tokens += total
        self.total_cost_usd += cost
        self.call_count += 1

        return {
            "text": text,
            "tokens": total,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "model": model,
            "latency_ms": latency_ms,
            "tier": tier,
        }

    async def chat_json(self, prompt: str, tier: str = "flash", **kwargs) -> dict:
        """Chat with JSON output mode. Returns parsed JSON or raw text on failure."""
        result = await self.chat(prompt, tier=tier, json_mode=True, **kwargs)
        try:
            result["parsed"] = json.loads(result["text"])
        except (json.JSONDecodeError, TypeError):
            result["parsed"] = None
        return result

    async def multi_chat(
        self, prompts: list[str], tier: str = "flash", concurrency: int = 5, **kwargs
    ) -> list[dict]:
        """Send multiple prompts concurrently with controlled concurrency."""
        semaphore = asyncio.Semaphore(concurrency)

        async def limited_chat(prompt):
            async with semaphore:
                return await self.chat(prompt, tier=tier, **kwargs)

        return await asyncio.gather(*[limited_chat(p) for p in prompts])

    async def _rate_limit(self):
        """Simple rate limiter: max N requests per minute."""
        now = time.time()
        self._rate_timestamps = [t for t in self._rate_timestamps if now - t < 60]
        if len(self._rate_timestamps) >= self._rate_limit_rpm:
            wait = 60 - (now - self._rate_timestamps[0])
            if wait > 0:
                print(f"[GEMINI] Rate limit. Waiting {wait:.1f}s...")
                await asyncio.sleep(wait)
        self._rate_timestamps.append(time.time())

    def stats(self) -> dict:
        """Return usage statistics."""
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "avg_tokens_per_call": (
                self.total_tokens // self.call_count if self.call_count else 0
            ),
        }
