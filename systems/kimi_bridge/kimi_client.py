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

        # iPad Compute Node (LLM Farm / Layla)
        # Default to a common local IP or localhost if bridged via USB
        self.ipad_url = os.getenv("IPAD_LLM_URL", "http://192.168.178.45:3000/v1")
        self.ipad_model = "default" # Most iPad apps ignore this or use loaded model

    async def _check_ipad(self) -> bool:
        """Check if iPad Compute Node is available."""
        if not self.ipad_url:
            return False
        try:
            # Short timeout for check
            timeout = aiohttp.ClientTimeout(total=2)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.ipad_url}/models") as resp:
                    if resp.status == 200:
                        logger.info("📱 iPad Compute Node DETECTED! Offloading task...")
                        return True
        except Exception:
            return False
        return False

    async def chat(self, messages: list, model: Optional[str] = None, temperature: float = 0.7, use_local: bool = True) -> Dict[str, Any]:
        """
        Unified chat method.
        Priority:
        1. iPad Compute Node (if available & use_local=True) - Saves Mac resources
        2. Local Mac Ollama (if use_local=True) - Backup local
        3. Moonshot Cloud API - High intel / Fallback
        """
        if use_local:
            # 1. Try iPad
            if await self._check_ipad():
                try:
                    response = await self._chat_ipad(messages, temperature)
                    if response:
                        return {
                            "content": response,
                            "source": "ipad_compute_node",
                            "model": "ipad-local"
                        }
                except Exception as e:
                    logger.warning(f"iPad inference failed: {e}. Falling back to Mac.")

            # 2. Try Local Mac Ollama
            try:
                # Try Local Ollama
                logger.info(f"Attempting Local Inference on Mac with {self.local_model}...")
                response = await self._chat_ollama(messages, temperature)
                if response:
                    return {
                        "content": response,
                        "source": "local_ollama",
                        "model": self.local_model
                    }
            except Exception as e:
                logger.warning(f"Local inference failed: {e}. Falling back to Cloud API.")

        # 3. Fallback to Cloud API
        if not self.api_key:
            raise ValueError("Local inference failed and no MOONSHOT_API_KEY provided for fallback.")

        logger.info(f"Attempting Cloud Inference with {self.api_model}...")
        response = await self._chat_api(messages, temperature)
        return {
            "content": response,
            "source": "moonshot_api",
            "model": self.api_model
        }

    async def _chat_ipad(self, messages: list, temperature: float) -> str:
        """Internal method to call iPad LLM Server (OpenAI compatible)."""
        # Apple Neural Engine can be slow on first token, give it 180s
        timeout = aiohttp.ClientTimeout(total=180)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            payload = {
                "model": self.ipad_model,
                "messages": messages,
                "temperature": temperature
            }
            # iPad apps usually expose /v1/chat/completions
            target_url = f"{self.ipad_url.rstrip('/v1')}/v1/chat/completions"

            try:
                async with session.post(target_url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        text = await resp.text()
                        raise Exception(f"iPad API Error: {resp.status} - {text}")
            except aiohttp.ClientConnectorError:
                raise Exception("iPad unreachable")

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
