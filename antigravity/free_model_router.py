#!/usr/bin/env python3
"""
🆓 FREE MODEL ROUTER
Intelligentes Routing zu kostenlosen LLM Services + Ollama

Kostenlose Optionen (Priorität):
  1. Ollama (lokal, 100% kostenlos) → Mistral, Llama2, Neural Chat
  2. OpenRouter (Free tier, up to 200k tokens/mo) → Mistral 7B, Llama 2
  3. Together.ai (Free tier, 1M tokens/mo) → LLama 2, Mistral
  4. HuggingFace Inference (Free tier) → Auf Transformern basierende Modelle
  5. Claude/Gemini (Fallback für kritische Operationen, kostenpflichtig)

Strategie:
  • 90% auf Ollama lokal
  • 8% auf Free Tier Services (bei Überlastung)
  • 2% auf Claude (nur für Verification + High-Quality Output)

Maurice's Kosten-Ziel: €0 wenn möglich, <€50/Monat maximum für Upgrades
"""

import os
import json
import logging
from typing import Optional, Dict, List
from enum import Enum
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

# ============================================================================
# MODELS
# ============================================================================

class ModelProvider(Enum):
    OLLAMA = "ollama"  # Local, free
    OPENROUTER = "openrouter"  # Free tier available
    TOGETHER = "together"  # Free tier available
    HUGGINGFACE = "huggingface"  # Free tier available
    CLAUDE = "claude"  # Paid, only for critical ops
    GEMINI = "gemini"  # Paid, fallback

class ModelSize(Enum):
    TINY = "tiny"  # 1-3B (fast, local) - Phi
    SMALL = "small"  # 7B (good balance) - Mistral, Llama2
    MEDIUM = "medium"  # 13-14B (better quality) - Neural Chat
    LARGE = "large"  # 70B (best quality) - Llama 70B
    XLARGE = "xlarge"  # 100B+ (expert) - Llama 200B

# ============================================================================
# OLLAMA MODELS (100% Free, Local)
# ============================================================================

OLLAMA_MODELS = {
    ModelSize.TINY: ["phi"],  # Microsoft Phi - tiny but effective
    ModelSize.SMALL: ["mistral", "neural-chat"],  # Best for local
    ModelSize.MEDIUM: ["llama2", "dolphin-mixtral"],
    ModelSize.LARGE: ["mixtral"],
}

# ============================================================================
# FREE TIER SERVICES
# ============================================================================

FREE_SERVICES = {
    "openrouter": {
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "free_models": {
            ModelSize.SMALL: ["mistralai/mistral-7b-instruct", "meta-llama/llama-2-7b-chat"],
            ModelSize.MEDIUM: ["mistralai/mixtral-8x7b-instruct"],
        },
        "monthly_limit": 200_000,  # tokens
        "key_env": "OPENROUTER_API_KEY",
    },
    "together": {
        "endpoint": "https://api.together.xyz/inference",
        "free_models": {
            ModelSize.SMALL: ["mistralai/Mistral-7B-Instruct-v0.1", "meta-llama/Llama-2-7b-chat-hf"],
            ModelSize.MEDIUM: ["mistralai/Mixtral-8x7B-Instruct-v0.1"],
        },
        "monthly_limit": 1_000_000,
        "key_env": "TOGETHER_API_KEY",
    },
}

# ============================================================================
# FREE MODEL ROUTER
# ============================================================================

class FreeModelRouter:
    """Routes requests to cheapest/fastest available model"""

    def __init__(self):
        self.ollama_base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.together_key = os.getenv("TOGETHER_API_KEY", "")
        self.claude_key = os.getenv("CLAUDE_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")

        self.usage = {
            "ollama": 0,
            "openrouter": 0,
            "together": 0,
            "claude": 0,
            "gemini": 0,
        }

    async def generate(
        self,
        prompt: str,
        model_size: ModelSize = ModelSize.SMALL,
        temperature: float = 0.7,
        max_tokens: int = 500,
        priority: str = "cost",  # "cost", "speed", "quality"
    ) -> str:
        """
        Generate text using cheapest available model

        Routing logic:
          1. Try Ollama first (local, 100% free)
          2. If Ollama overloaded, try free tier services
          3. Fallback to paid if absolutely necessary

        Args:
          prompt: Input prompt
          model_size: Size of model needed (affects quality/cost)
          temperature: Randomness (0-1)
          max_tokens: Max output length
          priority: Optimization target

        Returns:
          Generated text or error message
        """

        try:
            # Priority 1: Ollama (100% free, local)
            logger.debug(f"Attempting Ollama ({model_size.value})...")
            result = await self._call_ollama(
                prompt,
                model_size=model_size,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if result and len(result) > 0:
                self.usage["ollama"] += len(result.split())
                logger.debug(f"✅ Ollama succeeded ({len(result)} chars)")
                return result

        except Exception as e:
            logger.warning(f"Ollama failed: {e}")

        # Priority 2: Free tier services
        try:
            logger.debug("Trying free tier services...")

            # Try OpenRouter first (better quality)
            if self.openrouter_key:
                result = await self._call_openrouter(
                    prompt,
                    model_size=model_size,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                if result:
                    self.usage["openrouter"] += len(result.split())
                    logger.debug(f"✅ OpenRouter succeeded")
                    return result

            # Try Together.ai (more generous free tier)
            if self.together_key:
                result = await self._call_together(
                    prompt,
                    model_size=model_size,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                if result:
                    self.usage["together"] += len(result.split())
                    logger.debug(f"✅ Together.ai succeeded")
                    return result

        except Exception as e:
            logger.warning(f"Free services failed: {e}")

        # Priority 3: Claude (only for critical operations)
        if "CRITICAL" in priority or "VERIFY" in priority:
            try:
                logger.info("Using Claude for critical operation (paid)...")
                from anthropic import Anthropic
                client = Anthropic(api_key=self.claude_key)
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
                self.usage["claude"] += len(result.split())
                logger.info(f"✅ Claude succeeded (cost: ~€0.02)")
                return result
            except Exception as e:
                logger.error(f"Claude failed: {e}")

        # If all else fails
        logger.error(f"❌ All models failed for prompt: {prompt[:50]}...")
        return "(Model generation failed - check logs)"

    async def _call_ollama(
        self,
        prompt: str,
        model_size: ModelSize,
        temperature: float,
        max_tokens: int
    ) -> Optional[str]:
        """Call local Ollama (100% free)"""

        try:
            # Select best available model
            models = OLLAMA_MODELS.get(model_size, OLLAMA_MODELS[ModelSize.SMALL])
            if not models:
                return None

            model = models[0]  # Use first available

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("response", "").strip()
                    else:
                        logger.warning(f"Ollama {resp.status}: {await resp.text()}")
                        return None

        except Exception as e:
            logger.warning(f"Ollama error: {e}")
            return None

    async def _call_openrouter(
        self,
        prompt: str,
        model_size: ModelSize,
        temperature: float,
        max_tokens: int
    ) -> Optional[str]:
        """Call OpenRouter free tier"""

        if not self.openrouter_key:
            logger.warning("OpenRouter API key not set")
            return None

        try:
            # Get best model for size
            models = FREE_SERVICES["openrouter"]["free_models"].get(
                model_size,
                FREE_SERVICES["openrouter"]["free_models"][ModelSize.SMALL]
            )
            model = models[0]

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    FREE_SERVICES["openrouter"]["endpoint"],
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "HTTP-Referer": "https://github.com/mauricepfeifer/aiempire",
                        "X-Title": "AIEmpire",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"].strip()
                    else:
                        logger.warning(f"OpenRouter {resp.status}")
                        return None

        except Exception as e:
            logger.warning(f"OpenRouter error: {e}")
            return None

    async def _call_together(
        self,
        prompt: str,
        model_size: ModelSize,
        temperature: float,
        max_tokens: int
    ) -> Optional[str]:
        """Call Together.ai free tier"""

        if not self.together_key:
            logger.warning("Together API key not set")
            return None

        try:
            models = FREE_SERVICES["together"]["free_models"].get(
                model_size,
                FREE_SERVICES["together"]["free_models"][ModelSize.SMALL]
            )
            model = models[0]

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    FREE_SERVICES["together"]["endpoint"],
                    headers={"Authorization": f"Bearer {self.together_key}"},
                    json={
                        "model": model,
                        "prompt": prompt,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["output"]["choices"][0]["text"].strip()
                    else:
                        logger.warning(f"Together {resp.status}")
                        return None

        except Exception as e:
            logger.warning(f"Together error: {e}")
            return None

    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        total = sum(self.usage.values())
        return {
            **self.usage,
            "total_words": total,
            "cost_estimate": self._estimate_cost(),
        }

    def _estimate_cost(self) -> float:
        """Estimate monthly cost"""
        # Claude: ~€0.001 per word (input) + €0.003 per word (output)
        # Other services mostly free up to limits

        claude_words = self.usage["claude"]
        claude_cost = claude_words * 0.001  # Rough estimate

        return claude_cost

    def print_stats(self):
        """Print usage statistics"""
        stats = self.get_usage_stats()
        print("\n" + "="*50)
        print("🆓 MODEL USAGE STATISTICS")
        print("="*50)
        print(f"Ollama (free):     {stats['ollama']:>8} words")
        print(f"OpenRouter (free): {stats['openrouter']:>8} words")
        print(f"Together (free):   {stats['together']:>8} words")
        print(f"Claude (paid):     {stats['claude']:>8} words → €{stats['cost_estimate']:.2f}")
        print("="*50)
        print(f"Total words: {stats['total_words']}")
        print(f"Est. cost: €{stats['cost_estimate']:.2f}")
        print("="*50 + "\n")

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global router instance
_router = None

def get_router() -> FreeModelRouter:
    """Get global router instance"""
    global _router
    if _router is None:
        _router = FreeModelRouter()
    return _router

async def generate(
    prompt: str,
    model_size: ModelSize = ModelSize.SMALL,
    **kwargs
) -> str:
    """Convenience function to generate text"""
    router = get_router()
    return await router.generate(prompt, model_size=model_size, **kwargs)

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def example():
    """Test the router"""
    router = FreeModelRouter()

    # Test 1: Simple generation (Ollama)
    result1 = await router.generate(
        "Explain AI automation in one sentence"
    )
    print(f"Result 1:\n{result1}\n")

    # Test 2: Complex generation (might use Claude)
    result2 = await router.generate(
        "Create a 5-step content strategy for a new YouTube channel",
        model_size=ModelSize.MEDIUM
    )
    print(f"Result 2:\n{result2}\n")

    # Print usage stats
    router.print_stats()

if __name__ == "__main__":
    asyncio.run(example())
