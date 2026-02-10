"""
Ollama Engine - Local LLM Interface.

Handles all communication with the local Ollama instance.
Falls back gracefully when Ollama is offline.

Usage:
    engine = OllamaEngine()
    response = await engine.generate("Explain quantum computing", model="qwen2.5-coder:7b")
    models = await engine.list_models()
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:7b"
DEFAULT_TIMEOUT = 120


@dataclass
class OllamaResponse:
    """Structured response from Ollama."""
    text: str
    model: str
    tokens: int = 0
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None


@dataclass
class ModelInfo:
    """Metadata about an available model."""
    name: str
    size: int = 0
    modified: str = ""


class OllamaEngine:
    """Interface to local Ollama LLM server."""

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL, default_model: str = DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self._available: Optional[bool] = None
        self._call_count = 0
        self._total_tokens = 0

    async def check_health(self) -> bool:
        """Check if Ollama is running and responsive."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    self._available = resp.status == 200
                    return self._available
        except (aiohttp.ClientError, asyncio.TimeoutError):
            self._available = False
            return False

    async def list_models(self) -> List[ModelInfo]:
        """List all available Ollama models."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return [
                        ModelInfo(
                            name=m.get("name", "unknown"),
                            size=m.get("size", 0),
                            modified=m.get("modified_at", ""),
                        )
                        for m in data.get("models", [])
                    ]
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return []

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> OllamaResponse:
        """Generate a completion from Ollama."""
        model = model or self.default_model

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

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        return OllamaResponse(
                            text="", model=model, success=False,
                            error=f"Ollama returned {resp.status}: {text[:200]}",
                        )
                    data = await resp.json()
                    self._call_count += 1
                    tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
                    self._total_tokens += tokens
                    return OllamaResponse(
                        text=data.get("response", ""),
                        model=model,
                        tokens=tokens,
                        duration_ms=data.get("total_duration", 0) / 1e6,
                    )
        except asyncio.TimeoutError:
            return OllamaResponse(
                text="", model=model, success=False,
                error=f"Ollama timed out after {timeout}s",
            )
        except aiohttp.ClientError as e:
            return OllamaResponse(
                text="", model=model, success=False,
                error=f"Ollama connection error: {e}",
            )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> OllamaResponse:
        """Chat-style completion with message history."""
        model = model or self.default_model

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": temperature},
                    },
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        return OllamaResponse(
                            text="", model=model, success=False,
                            error=f"Ollama chat {resp.status}: {text[:200]}",
                        )
                    data = await resp.json()
                    self._call_count += 1
                    tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
                    self._total_tokens += tokens
                    return OllamaResponse(
                        text=data.get("message", {}).get("content", ""),
                        model=model,
                        tokens=tokens,
                        duration_ms=data.get("total_duration", 0) / 1e6,
                    )
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            return OllamaResponse(
                text="", model=model, success=False,
                error=f"Ollama chat error: {e}",
            )

    def get_stats(self) -> Dict:
        """Return usage statistics."""
        return {
            "available": self._available,
            "call_count": self._call_count,
            "total_tokens": self._total_tokens,
            "base_url": self.base_url,
            "default_model": self.default_model,
        }
