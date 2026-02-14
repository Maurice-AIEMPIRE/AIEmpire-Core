import os
import asyncio
import aiohttp
import logging
from typing import Dict, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kimi_client")

class KimiClient:
    """
    Hybrid Client for 'Kimi' Intelligence.
    Prioritizes Local Ollama (cost-saving) and fails over to Moonshot API (high-intelligence).
    """

    def __init__(self, ollama_url: str = "http://localhost:11434", api_key: Optional[str] = None):
        self.ollama_url = ollama_url
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        # Preferred local model - adapt based on what's available
        self.local_model = "glm-4.7-flash:latest" 
        self.fallback_local_model = "qwen2.5-coder:7b"
        self.api_model = "moonshot-v1-8k"

    async def chat(self, messages: list, model: Optional[str] = None, temperature: float = 0.7, use_local: bool = True) -> Dict[str, Any]:
        """
        Unified chat method.
        If use_local is True, tries Ollama first. If it fails or use_local is False, tries Moonshot API.
        """
        if use_local:
            try:
                # Try Local Ollama
                logger.info(f"Attempting Local Inference with {self.local_model}...")
                response = await self._chat_ollama(messages, temperature)
                if response:
                    return {
                        "content": response,
                        "source": "local_ollama",
                        "model": self.local_model
                    }
            except Exception as e:
                logger.warning(f"Local inference failed: {e}. Falling back to Cloud API.")

        # Fallback to Cloud API
        if not self.api_key:
            raise ValueError("Local inference failed and no MOONSHOT_API_KEY provided for fallback.")

        logger.info(f"Attempting Cloud Inference with {self.api_model}...")
        response = await self._chat_api(messages, temperature)
        return {
            "content": response,
            "source": "moonshot_api",
            "model": self.api_model
        }

    async def _chat_ollama(self, messages: list, temperature: float) -> str:
        """Internal method to call Ollama. Uses 120s timeout for large models like glm-4.7-flash (19GB)."""
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            payload = {
                "model": self.local_model,
                "messages": messages,
                "temperature": temperature,
                "stream": False
            }
            try:
                async with session.post(f"{self.ollama_url}/api/chat", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["message"]["content"]
                    elif resp.status == 404:
                        # Try fallback model (smaller, faster)
                        logger.info(f"Model {self.local_model} not found, trying {self.fallback_local_model}")
                        payload["model"] = self.fallback_local_model
                        async with session.post(f"{self.ollama_url}/api/chat", json=payload) as resp_fallback:
                            if resp_fallback.status == 200:
                                data = await resp_fallback.json()
                                self.local_model = self.fallback_local_model  # Cache for next calls
                                return data["message"]["content"]
                    else:
                        text = await resp.text()
                        raise Exception(f"Ollama HTTP {resp.status}: {text[:200]}")
            except asyncio.TimeoutError:
                logger.warning(f"Ollama timeout after 120s (model: {self.local_model})")
                raise
            except aiohttp.ClientConnectorError:
                logger.error("Could not connect to Ollama. Is it running?")
                raise

        raise Exception("Ollama execution failed")

    async def _chat_api(self, messages: list, temperature: float) -> str:
        """Internal method to call Moonshot API."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.api_model,
                "messages": messages,
                "temperature": temperature
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            async with session.post("https://api.moonshot.ai/v1/chat/completions", json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    text = await resp.text()
                    raise Exception(f"Moonshot API Error: {resp.status} - {text}")
