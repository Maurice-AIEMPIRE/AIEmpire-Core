"""
Ollama Client
=============
Thin wrapper around Ollama's OpenAI-compatible API.
Used by all 4 Godmode Programmer agents to communicate with local models.
"""

import json
from antigravity.config import OLLAMA_API_V1, AgentConfig
from typing import Optional

import httpx


class OllamaClient:
    """Client for Ollama's OpenAI-compatible /v1/chat/completions endpoint."""

    def __init__(self, base_url: str = OLLAMA_API_V1, timeout: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(
        self,
        agent: AgentConfig,
        user_message: str,
        context: Optional[str] = None,
    ) -> dict:
        """
        Send a chat completion request to Ollama.

        Args:
            agent: The agent configuration (model, system prompt, etc.)
            user_message: The user/task message
            context: Optional additional context (file contents, error logs, etc.)

        Returns:
            dict with keys: content, model, usage, raw_response
        """
        messages = [
            {"role": "system", "content": agent.system_prompt},
        ]

        if context:
            messages.append({"role": "user", "content": f"KONTEXT:\n```\n{context}\n```"})

        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": agent.model,
            "messages": messages,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "stream": False,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. Is Ollama running? Start with: ollama serve"
            )
        except httpx.TimeoutException:
            raise TimeoutError(
                f"Ollama request timed out after {self.timeout}s for model {agent.model}. "
                "Try increasing timeout or using a smaller model."
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error {e.response.status_code}: {e.response.text[:200]}")

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            data_str = str(data)
            raise ValueError(f"Unexpected Ollama response format: {data_str[:300]}") from e

        usage = data.get("usage", {})

        return {
            "content": content,
            "model": data.get("model", agent.model),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "raw_response": data,
        }

    def chat_stream(
        self,
        agent: AgentConfig,
        user_message: str,
        context: Optional[str] = None,
    ):
        """
        Stream a chat completion from Ollama (yields chunks).

        Yields:
            str: Content chunks as they arrive
        """
        messages = [
            {"role": "system", "content": agent.system_prompt},
        ]

        if context:
            messages.append({"role": "user", "content": f"KONTEXT:\n```\n{context}\n```"})

        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": agent.model,
            "messages": messages,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "stream": True,
        }

        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data: "):
                        line = line[6:]
                    if line.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    def list_models(self) -> list[dict]:
        """List all available models from Ollama."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.base_url}/models")
                response.raise_for_status()
                return response.json().get("data", [])
        except (httpx.ConnectError, httpx.TimeoutException):
            return []
        except httpx.HTTPStatusError:
            return []

    def health_check(self) -> bool:
        """Check if Ollama is running and responsive."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/models")
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False


# ─── Singleton for convenience ──────────────────────────────────────
_default_client: Optional[OllamaClient] = None


def get_client() -> OllamaClient:
    """Get the default OllamaClient instance."""
    global _default_client
    if _default_client is None:
        _default_client = OllamaClient()
    return _default_client
