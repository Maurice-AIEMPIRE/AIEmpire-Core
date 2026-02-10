"""
Gemini Client - Hybrid API Client fuer Google Gemini
Spiegelt das KimiClient Pattern: Local Ollama → Gemini Flash → Gemini Pro

Fallback-Kette:
1. Ollama (lokal, kostenlos)
2. Gemini Flash (schnell, guenstig)
3. Gemini Pro (stark, teurer)
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from config import (
    GEMINI_API_KEY,
    GEMINI_BASE_URL,
    GEMINI_MODELS,
    RESOURCE_LIMITS,
)

logger = logging.getLogger("gemini-client")


class CostTracker:
    """Verfolgt API-Kosten pro Tag und stoppt bei Limit."""

    def __init__(self, daily_limit: float = 10.0):
        self.daily_limit = daily_limit
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.today_cost = 0.0
        self.total_calls = 0
        self.total_tokens_in = 0
        self.total_tokens_out = 0

    def _reset_if_new_day(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.today:
            self.today = today
            self.today_cost = 0.0

    def add_cost(self, tokens_in: int, tokens_out: int, model: str):
        self._reset_if_new_day()
        if "flash" in model:
            cost = (tokens_in / 1000) * RESOURCE_LIMITS["cost_per_1k_input_flash"]
            cost += (tokens_out / 1000) * RESOURCE_LIMITS["cost_per_1k_output_flash"]
        else:
            cost = (tokens_in / 1000) * RESOURCE_LIMITS["cost_per_1k_input_pro"]
            cost += (tokens_out / 1000) * RESOURCE_LIMITS["cost_per_1k_output_pro"]
        self.today_cost += cost
        self.total_calls += 1
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
        return cost

    def can_spend(self) -> bool:
        self._reset_if_new_day()
        return self.today_cost < self.daily_limit

    def get_stats(self) -> Dict:
        return {
            "today_cost_usd": round(self.today_cost, 4),
            "daily_limit_usd": self.daily_limit,
            "budget_remaining": round(self.daily_limit - self.today_cost, 4),
            "total_calls": self.total_calls,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
        }


class GeminiClient:
    """
    Hybrid Client fuer Google Gemini API.
    Fallback: Ollama (lokal) → Gemini Flash → Gemini Pro
    Kompatibel mit dem KimiClient Interface.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
    ):
        self.api_key = api_key or GEMINI_API_KEY
        self.ollama_url = ollama_url
        self.local_model = "gemma2:9b"
        self.fallback_local = "qwen2.5-coder:7b"
        self.cost_tracker = CostTracker(
            daily_limit=RESOURCE_LIMITS["emergency_stop_daily_cost"]
        )
        self.semaphore = asyncio.Semaphore(
            RESOURCE_LIMITS["max_concurrent_gemini_calls"]
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "flash",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_local: bool = True,
        force_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Unified Chat-Interface.

        Args:
            messages: OpenAI-Format [{"role": "user", "content": "..."}]
            model: "flash", "pro", oder "thinking"
            temperature: 0.0-2.0
            max_tokens: Max Output-Tokens
            use_local: Zuerst Ollama versuchen
            force_provider: "ollama", "gemini" oder None (auto)

        Returns:
            {
                "content": str,
                "source": "local_ollama" | "gemini_flash" | "gemini_pro",
                "model": str,
                "tokens_in": int,
                "tokens_out": int,
                "cost_usd": float,
                "latency_ms": int,
            }
        """
        start_time = time.time()

        # Forced Provider
        if force_provider == "ollama":
            return await self._try_ollama(messages, temperature, start_time)
        if force_provider == "gemini":
            return await self._call_gemini(
                messages, model, temperature, max_tokens, start_time
            )

        # Auto-Routing: Ollama zuerst wenn aktiviert
        if use_local:
            try:
                result = await self._try_ollama(messages, temperature, start_time)
                if result.get("content"):
                    return result
            except Exception as e:
                logger.debug(f"Ollama nicht verfuegbar: {e}")

        # Gemini API
        return await self._call_gemini(
            messages, model, temperature, max_tokens, start_time
        )

    async def _try_ollama(
        self,
        messages: List[Dict],
        temperature: float,
        start_time: float,
    ) -> Dict[str, Any]:
        """Versucht lokales Ollama Model."""
        payload = {
            "model": self.local_model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status == 404:
                        # Fallback Model versuchen
                        payload["model"] = self.fallback_local
                        async with session.post(
                            f"{self.ollama_url}/api/chat",
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=120),
                        ) as resp2:
                            resp2.raise_for_status()
                            data = await resp2.json()
                    else:
                        resp.raise_for_status()
                        data = await resp.json()

            content = data.get("message", {}).get("content", "")
            latency = int((time.time() - start_time) * 1000)
            return {
                "content": content,
                "source": "local_ollama",
                "model": payload["model"],
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0.0,
                "latency_ms": latency,
            }
        except Exception as e:
            raise ConnectionError(f"Ollama Fehler: {e}")

    async def _call_gemini(
        self,
        messages: List[Dict],
        model: str,
        temperature: float,
        max_tokens: int,
        start_time: float,
    ) -> Dict[str, Any]:
        """Ruft Google Gemini API auf."""
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY nicht gesetzt! "
                "export GEMINI_API_KEY='dein-key'"
            )

        if not self.cost_tracker.can_spend():
            raise RuntimeError(
                f"Tages-Budget erreicht: "
                f"${self.cost_tracker.today_cost:.2f} / "
                f"${self.cost_tracker.daily_limit:.2f}"
            )

        model_id = GEMINI_MODELS.get(model, model)
        url = f"{GEMINI_BASE_URL}/models/{model_id}:generateContent?key={self.api_key}"

        # OpenAI-Format → Gemini-Format konvertieren
        gemini_contents = self._convert_messages(messages)

        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
            },
        }

        # System-Instruction extrahieren
        system_msg = next(
            (m["content"] for m in messages if m.get("role") == "system"), None
        )
        if system_msg:
            payload["systemInstruction"] = {
                "parts": [{"text": system_msg}]
            }

        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=180),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise RuntimeError(
                            f"Gemini API Fehler {resp.status}: {error_text[:500]}"
                        )
                    data = await resp.json()

        # Response parsen
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Keine Gemini-Antwort: {json.dumps(data)[:500]}")

        content = ""
        for part in candidates[0].get("content", {}).get("parts", []):
            content += part.get("text", "")

        # Token-Usage extrahieren
        usage = data.get("usageMetadata", {})
        tokens_in = usage.get("promptTokenCount", 0)
        tokens_out = usage.get("candidatesTokenCount", 0)
        cost = self.cost_tracker.add_cost(tokens_in, tokens_out, model_id)
        latency = int((time.time() - start_time) * 1000)

        source = f"gemini_{model}" if model in GEMINI_MODELS else f"gemini_{model_id}"

        return {
            "content": content,
            "source": source,
            "model": model_id,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": round(cost, 6),
            "latency_ms": latency,
        }

    def _convert_messages(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict]:
        """Konvertiert OpenAI-Format zu Gemini-Format."""
        gemini_contents = []
        for msg in messages:
            if msg.get("role") == "system":
                continue  # System wird separat behandelt
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}],
            })
        return gemini_contents

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        model: str = "flash",
        temperature: float = 0.5,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Chat mit erzwungenem JSON-Output.
        Parsed die Antwort automatisch.
        """
        result = await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            use_local=False,
            force_provider="gemini",
        )

        parsed = self._parse_json(result["content"])
        result["parsed"] = parsed
        result["parse_success"] = "parse_error" not in parsed
        return result

    @staticmethod
    def _parse_json(raw: str) -> Dict:
        """Robust JSON-Parser (wie im Hauptsystem)."""
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {"parse_error": True, "raw": raw[:2000]}

    def get_cost_stats(self) -> Dict:
        """Gibt aktuelle Kosten-Statistiken zurueck."""
        return self.cost_tracker.get_stats()


# === Convenience-Funktionen ===

_default_client: Optional[GeminiClient] = None


def get_client() -> GeminiClient:
    """Singleton-Instanz des GeminiClient."""
    global _default_client
    if _default_client is None:
        _default_client = GeminiClient()
    return _default_client


async def quick_gemini(
    prompt: str,
    system: str = "",
    model: str = "flash",
    temperature: float = 0.7,
) -> str:
    """Schneller Gemini-Aufruf fuer einfache Prompts."""
    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    result = await client.chat(messages, model=model, temperature=temperature)
    return result["content"]


async def quick_gemini_json(
    prompt: str,
    system: str = "Antworte NUR mit validem JSON.",
    model: str = "flash",
) -> Dict:
    """Schneller Gemini-Aufruf mit JSON-Output."""
    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    result = await client.chat_json(messages, model=model)
    return result.get("parsed", {})


# === Mirror-Kompatibilitaets-Layer ===
# Die mirror_daemon/vision_discovery/evolution Modules nutzen ein
# vereinfachtes Interface: chat(prompt, tier="flash")
# Dieser Wrapper macht beides kompatibel.

class MirrorGeminiClient(GeminiClient):
    """
    Extended GeminiClient with simplified interface for Mirror modules.

    Supports both:
    - chat(messages=[...], model="flash")  (original)
    - chat(prompt="...", tier="flash")     (mirror shorthand)
    """

    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key)
        self.total_tokens = 0
        self.total_cost_usd = 0.0
        self.call_count = 0

    async def chat(
        self,
        prompt_or_messages=None,
        tier: str = "flash",
        system_instruction: str = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        json_mode: bool = False,
        # Original interface params
        messages: List = None,
        model: str = None,
        use_local: bool = True,
        force_provider: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Unified interface: accepts both prompt string and message list."""

        # Detect which interface is being used
        if messages is not None:
            # Original interface: chat(messages=[...], model="flash")
            result = await super().chat(
                messages=messages,
                model=model or tier,
                temperature=temperature,
                max_tokens=max_tokens,
                use_local=use_local,
                force_provider=force_provider,
            )
            self._track(result)
            return result

        # Mirror interface: chat(prompt="...", tier="flash")
        prompt = prompt_or_messages
        if isinstance(prompt, list):
            # It's actually a message list passed as first arg
            result = await super().chat(
                messages=prompt,
                model=model or tier,
                temperature=temperature,
                max_tokens=max_tokens,
                use_local=use_local,
            )
            self._track(result)
            return result

        # String prompt → convert to messages
        msgs = []
        if system_instruction:
            msgs.append({"role": "system", "content": system_instruction})
        msgs.append({"role": "user", "content": str(prompt)})

        result = await super().chat(
            messages=msgs,
            model=model or tier,
            temperature=temperature,
            max_tokens=max_tokens,
            use_local=False,
            force_provider="gemini",
        )

        # Map to mirror-expected output format
        self._track(result)
        result["text"] = result.get("content", "")
        result["tier"] = tier
        return result

    async def chat_json(
        self,
        prompt_or_messages=None,
        tier: str = "flash",
        messages: List = None,
        model: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """JSON chat: accepts both prompt string and message list."""

        if messages is not None:
            result = await super().chat_json(
                messages=messages, model=model or tier, **kwargs
            )
            self._track(result)
            return result

        prompt = prompt_or_messages
        if isinstance(prompt, list):
            result = await super().chat_json(messages=prompt, model=model or tier, **kwargs)
            self._track(result)
            return result

        # String prompt
        msgs = [{"role": "user", "content": str(prompt)}]
        result = await super().chat_json(messages=msgs, model=model or tier, **kwargs)
        self._track(result)
        result["text"] = result.get("content", "")
        return result

    async def multi_chat(
        self, prompts: List[str], tier: str = "flash", concurrency: int = 5, **kwargs
    ) -> List[Dict]:
        """Send multiple prompts concurrently."""
        semaphore = asyncio.Semaphore(concurrency)

        async def limited_chat(prompt):
            async with semaphore:
                return await self.chat(prompt, tier=tier, **kwargs)

        return await asyncio.gather(*[limited_chat(p) for p in prompts])

    def _track(self, result: Dict):
        """Track usage statistics."""
        self.total_tokens += result.get("tokens_in", 0) + result.get("tokens_out", 0)
        self.total_cost_usd += result.get("cost_usd", 0)
        self.call_count += 1

    def stats(self) -> Dict:
        """Return usage statistics (mirror interface)."""
        base_stats = self.get_cost_stats()
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "avg_tokens_per_call": (
                self.total_tokens // self.call_count if self.call_count else 0
            ),
            **base_stats,
        }
