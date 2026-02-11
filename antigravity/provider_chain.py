#!/usr/bin/env python3
"""
Provider Chain — Smart Multi-AI Routing
=========================================
The brain of the AI Empire: Routes every AI request through
the optimal provider chain with automatic failover.

Chain: Ollama (free, local) → Kimi (free tier) → Gemini (Google) → OpenRouter (free)

Each provider has:
  - Health check
  - Async query
  - Error tracking
  - Cost tracking
  - Latency tracking

Usage:
    from antigravity.provider_chain import ProviderChain
    chain = ProviderChain()

    # Simple query (auto-routes)
    result = await chain.query("Erklaere Machine Learning")

    # Prefer specific provider
    result = await chain.query("Complex reasoning task", prefer="gemini")

    # Force local only
    result = await chain.query("Quick code fix", prefer="ollama")

    # Get status
    status = await chain.health_check()
"""

import asyncio
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# Ensure project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


@dataclass
class ProviderStats:
    """Track performance of a single provider."""
    name: str
    available: bool = False
    total_requests: int = 0
    total_tokens: int = 0
    total_errors: int = 0
    avg_latency_ms: float = 0.0
    last_error: str = ""
    last_check: float = 0.0


class ProviderChain:
    """
    Intelligent multi-provider AI chain with automatic failover.

    Priority (configurable):
      1. Ollama  — Free, local, fast for simple tasks
      2. Kimi    — Free tier, good for complex tasks
      3. Gemini  — Google, fast, good for reasoning
      4. OpenRouter — Free models available as last resort
    """

    def __init__(self):
        self.stats = {
            "ollama": ProviderStats("ollama"),
            "kimi": ProviderStats("kimi"),
            "gemini": ProviderStats("gemini"),
            "openrouter": ProviderStats("openrouter"),
        }
        self._default_chain = ["ollama", "kimi", "gemini", "openrouter"]

    # ─── Provider Implementations ────────────────────────────

    async def _query_ollama(self, prompt: str, system: str = "",
                             model: str = "", timeout: float = 120) -> dict:
        """Query Ollama local AI."""
        import httpx
        url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        if not model:
            model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

        payload = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{url}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            return {
                "content": data.get("response", ""),
                "model": model,
                "provider": "ollama",
                "tokens": data.get("eval_count", 0),
                "cost": 0.0,
            }

    async def _query_kimi(self, prompt: str, system: str = "",
                           model: str = "", timeout: float = 60) -> dict:
        """Query Kimi/Moonshot API."""
        import httpx
        api_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY", "")
        if not api_key:
            raise ConnectionError("No Kimi API key configured")
        if not model:
            model = "moonshot-v1-8k"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "messages": messages},
            )
            r.raise_for_status()
            data = r.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": model,
                "provider": "kimi",
                "tokens": data.get("usage", {}).get("total_tokens", 0),
                "cost": 0.0,  # Free tier
            }

    async def _query_gemini(self, prompt: str, system: str = "",
                             model: str = "", timeout: float = 60) -> dict:
        """Query Google Gemini via REST (no SDK needed)."""
        import httpx
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or len(api_key) < 10:
            raise ConnectionError("No Gemini API key configured")
        if not model:
            model = "gemini-2.0-flash"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        text = f"[System]: {system}\n\n{prompt}" if system else prompt
        payload = {"contents": [{"parts": [{"text": text}]}]}

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return {
                "content": content,
                "model": model,
                "provider": "gemini",
                "tokens": data.get("usageMetadata", {}).get("totalTokenCount", 0),
                "cost": 0.0,  # Flash is free for low volume
            }

    async def _query_openrouter(self, prompt: str, system: str = "",
                                 model: str = "", timeout: float = 60) -> dict:
        """Query OpenRouter (free models)."""
        import httpx
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ConnectionError("No OpenRouter API key configured")
        if not model:
            model = "meta-llama/llama-3.1-8b-instruct:free"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "messages": messages},
            )
            r.raise_for_status()
            data = r.json()
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": model,
                "provider": "openrouter",
                "tokens": data.get("usage", {}).get("total_tokens", 0),
                "cost": 0.0,
            }

    # ─── Smart Query with Failover ───────────────────────────

    async def query(self, prompt: str, system: str = "",
                    prefer: str = "auto", model: str = "",
                    timeout: float = 120) -> dict:
        """
        Smart query with automatic failover chain.

        Args:
            prompt: The task/question
            system: System prompt for agent personality
            prefer: Provider preference ("auto", "ollama", "kimi", "gemini", "openrouter", "cloud")
            model: Specific model override
            timeout: Max seconds per attempt
        """
        query_map = {
            "ollama": self._query_ollama,
            "kimi": self._query_kimi,
            "gemini": self._query_gemini,
            "openrouter": self._query_openrouter,
        }

        # Build chain based on preference
        if prefer == "auto":
            chain = list(self._default_chain)
        elif prefer == "cloud":
            chain = ["kimi", "gemini", "openrouter", "ollama"]
        elif prefer in query_map:
            chain = [prefer] + [p for p in self._default_chain if p != prefer]
        else:
            chain = list(self._default_chain)

        errors = []
        for provider_name in chain:
            query_fn = query_map.get(provider_name)
            if not query_fn:
                continue

            try:
                start = time.time()
                result = await query_fn(prompt=prompt, system=system,
                                         model=model, timeout=timeout)
                elapsed = (time.time() - start) * 1000

                # Update stats
                stats = self.stats[provider_name]
                stats.available = True
                stats.total_requests += 1
                stats.total_tokens += result.get("tokens", 0)
                stats.avg_latency_ms = (
                    (stats.avg_latency_ms * (stats.total_requests - 1) + elapsed)
                    / stats.total_requests
                )

                result["latency_ms"] = round(elapsed, 1)
                result["success"] = True
                return result

            except Exception as e:
                error_msg = f"{provider_name}: {type(e).__name__}: {str(e)[:100]}"
                errors.append(error_msg)
                self.stats[provider_name].total_errors += 1
                self.stats[provider_name].last_error = str(e)[:200]

        # All providers failed
        return {
            "content": f"Alle Provider fehlgeschlagen: {'; '.join(errors)}",
            "model": "none",
            "provider": "none",
            "tokens": 0,
            "cost": 0.0,
            "success": False,
            "errors": errors,
        }

    # ─── Health Check ────────────────────────────────────────

    async def health_check(self) -> dict:
        """Check all providers and return status."""
        import httpx

        results = {}

        # Ollama
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/tags")
                self.stats["ollama"].available = r.status_code == 200
                models = [m["name"] for m in r.json().get("models", [])] if r.status_code == 200 else []
                results["ollama"] = {"available": r.status_code == 200, "models": models}
        except Exception:
            self.stats["ollama"].available = False
            results["ollama"] = {"available": False, "models": []}

        # Kimi
        key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY", "")
        self.stats["kimi"].available = bool(key)
        results["kimi"] = {"available": bool(key), "key_set": bool(key)}

        # Gemini
        key = os.getenv("GEMINI_API_KEY", "")
        has_key = bool(key) and len(key) > 10
        self.stats["gemini"].available = has_key
        results["gemini"] = {"available": has_key, "key_set": has_key}

        # OpenRouter
        key = os.getenv("OPENROUTER_API_KEY", "")
        self.stats["openrouter"].available = bool(key)
        results["openrouter"] = {"available": bool(key), "key_set": bool(key)}

        return results

    def get_status(self) -> dict:
        """Get formatted status of all providers."""
        return {
            name: {
                "available": s.available,
                "requests": s.total_requests,
                "tokens": s.total_tokens,
                "errors": s.total_errors,
                "avg_latency_ms": round(s.avg_latency_ms, 1),
                "last_error": s.last_error,
            }
            for name, s in self.stats.items()
        }


# ─── Module-level singleton ──────────────────────────────────
_chain: Optional[ProviderChain] = None

def get_chain() -> ProviderChain:
    """Get the singleton ProviderChain instance."""
    global _chain
    if _chain is None:
        _chain = ProviderChain()
    return _chain


# ─── CLI Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    async def _test():
        chain = ProviderChain()
        print("Checking providers...")
        status = await chain.health_check()
        for name, info in status.items():
            avail = "✓" if info["available"] else "✗"
            print(f"  {avail} {name}: {info}")

        print("\nQuerying...")
        result = await chain.query("Sage 'Hallo Empire!' in einem Satz.")
        print(f"  Provider: {result.get('provider')}")
        print(f"  Model: {result.get('model')}")
        print(f"  Response: {result.get('content', '')[:200]}")

    asyncio.run(_test())
