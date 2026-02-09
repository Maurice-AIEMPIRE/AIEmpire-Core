#!/usr/bin/env python3
"""
OLLAMA ENGINE - Lokale AI Power fuer das Empire.
Zero Cost. Zero Latency. Maximale Kontrolle.

Modelle: qwen2.5-coder:7b, glm-4.7-flash, deepseek-r1:8b
API: Ollama REST (http://localhost:11434)

Usage:
    from ollama_engine import OllamaEngine, LLMResponse

    engine = OllamaEngine()
    response = await engine.chat([{"role": "user", "content": "Hello"}])
    print(response.content)
"""

import os
import json
import asyncio
import aiohttp
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, AsyncIterator


# Configuration via Environment
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))


@dataclass
class LLMResponse:
    """Strukturierte Antwort von jedem LLM - lokal oder cloud."""
    content: str
    model: str
    tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_ms: float = 0.0
    cost: float = 0.0  # Immer 0.0 fuer lokale Modelle
    provider: str = "ollama"
    success: bool = True
    error: str = ""


class OllamaEngine:
    """Async Ollama Client - das lokale Gehirn des Empire."""

    def __init__(
        self,
        host: str = OLLAMA_HOST,
        model: str = OLLAMA_MODEL,
        temperature: float = OLLAMA_TEMPERATURE,
        timeout: int = OLLAMA_TIMEOUT,
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self._stats = {"calls": 0, "tokens": 0, "errors": 0, "total_ms": 0}

    # ── Health & Discovery ──────────────────────────────────

    async def health_check(self) -> bool:
        """Prueft ob Ollama laeuft."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.host}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    return resp.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def list_models(self) -> List[str]:
        """Listet alle verfuegbaren Modelle."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.host}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [m["name"] for m in data.get("models", [])]
                    return []
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return []

    async def pull_model(self, name: str) -> bool:
        """Laedt ein Modell herunter."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.host}/api/pull",
                    json={"name": name},
                    timeout=aiohttp.ClientTimeout(total=600),
                ) as resp:
                    if resp.status == 200:
                        async for line in resp.content:
                            data = json.loads(line)
                            status = data.get("status", "")
                            if "pulling" in status:
                                total = data.get("total", 0)
                                completed = data.get("completed", 0)
                                if total > 0:
                                    pct = (completed / total) * 100
                                    print(f"\r  Pulling {name}: {pct:.0f}%", end="", flush=True)
                        print()
                        return True
                    return False
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    # ── Core LLM Calls ──────────────────────────────────────

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Chat Completion - wie OpenAI/Claude aber lokal."""
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        start = time.monotonic()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.host}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    elapsed = (time.monotonic() - start) * 1000

                    if resp.status == 200:
                        data = await resp.json()
                        content = data.get("message", {}).get("content", "")
                        prompt_tokens = data.get("prompt_eval_count", 0)
                        completion_tokens = data.get("eval_count", 0)
                        total_tokens = prompt_tokens + completion_tokens

                        self._stats["calls"] += 1
                        self._stats["tokens"] += total_tokens
                        self._stats["total_ms"] += elapsed

                        return LLMResponse(
                            content=content,
                            model=model,
                            tokens=total_tokens,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            duration_ms=elapsed,
                            cost=0.0,
                            provider="ollama",
                        )
                    else:
                        text = await resp.text()
                        self._stats["errors"] += 1
                        return LLMResponse(
                            content="",
                            model=model,
                            duration_ms=elapsed,
                            success=False,
                            error=f"HTTP {resp.status}: {text[:200]}",
                        )

        except asyncio.TimeoutError:
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=model, success=False,
                error=f"Timeout nach {self.timeout}s",
                duration_ms=(time.monotonic() - start) * 1000,
            )
        except aiohttp.ClientError as e:
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=model, success=False,
                error=f"Connection error: {e}",
                duration_ms=(time.monotonic() - start) * 1000,
            )

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """Raw Text Generation - fuer einfache Prompts."""
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        start = time.monotonic()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.host}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    elapsed = (time.monotonic() - start) * 1000

                    if resp.status == 200:
                        data = await resp.json()
                        content = data.get("response", "")
                        prompt_tokens = data.get("prompt_eval_count", 0)
                        completion_tokens = data.get("eval_count", 0)
                        total_tokens = prompt_tokens + completion_tokens

                        self._stats["calls"] += 1
                        self._stats["tokens"] += total_tokens
                        self._stats["total_ms"] += elapsed

                        return LLMResponse(
                            content=content,
                            model=model,
                            tokens=total_tokens,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            duration_ms=elapsed,
                            cost=0.0,
                            provider="ollama",
                        )
                    else:
                        text = await resp.text()
                        self._stats["errors"] += 1
                        return LLMResponse(
                            content="", model=model, success=False,
                            error=f"HTTP {resp.status}: {text[:200]}",
                            duration_ms=elapsed,
                        )

        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            self._stats["errors"] += 1
            return LLMResponse(
                content="", model=model, success=False,
                error=str(e),
                duration_ms=(time.monotonic() - start) * 1000,
            )

    # ── Streaming ───────────────────────────────────────────

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """Streaming Chat - Token fuer Token."""
        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature},
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as resp:
                async for line in resp.content:
                    if line:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if data.get("done"):
                            break

    # ── Stats & Utility ─────────────────────────────────────

    def get_stats(self) -> dict:
        """Gibt Engine-Statistiken zurueck."""
        avg_ms = self._stats["total_ms"] / max(self._stats["calls"], 1)
        return {
            **self._stats,
            "avg_latency_ms": round(avg_ms, 1),
            "model": self.model,
            "host": self.host,
            "cost_total": 0.0,
        }

    def format_stats(self) -> str:
        """Formatierte Stats fuer Ausgabe."""
        s = self.get_stats()
        return (
            f"Ollama [{s['model']}] | "
            f"Calls: {s['calls']} | "
            f"Tokens: {s['tokens']:,} | "
            f"Avg: {s['avg_latency_ms']:.0f}ms | "
            f"Errors: {s['errors']} | "
            f"Cost: $0.00"
        )

    def __repr__(self) -> str:
        return f"OllamaEngine(host={self.host}, model={self.model})"


# ── Standalone Test ─────────────────────────────────────────

async def _test():
    engine = OllamaEngine()

    print("=" * 60)
    print("  OLLAMA ENGINE - Test")
    print("=" * 60)

    # Health Check
    healthy = await engine.health_check()
    print(f"\n  Health: {'OK' if healthy else 'OFFLINE'}")

    if not healthy:
        print("  Ollama ist nicht erreichbar.")
        print(f"  Host: {engine.host}")
        print("  Starte mit: ollama serve")
        return

    # List Models
    models = await engine.list_models()
    print(f"  Models: {', '.join(models) if models else 'keine'}")

    # Chat Test
    print(f"\n  Chat Test ({engine.model})...")
    resp = await engine.chat([
        {"role": "system", "content": "Du bist ein hilfreicher Assistent. Antworte kurz."},
        {"role": "user", "content": "Was ist 2+2? Antworte in einem Satz."},
    ])

    if resp.success:
        print(f"  Antwort: {resp.content[:200]}")
        print(f"  Tokens: {resp.tokens} | {resp.duration_ms:.0f}ms | ${resp.cost}")
    else:
        print(f"  Fehler: {resp.error}")

    print(f"\n  Stats: {engine.format_stats()}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(_test())
