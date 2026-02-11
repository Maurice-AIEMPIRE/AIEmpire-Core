"""
Gemini Client
=============
Client for Google's Gemini API (direct + Vertex AI).
Mirrors the OllamaClient interface so it can be used interchangeably
by the GodmodeRouter and all agents.

Supports:
- google-generativeai SDK (direct API key)
- Vertex AI (Google Cloud project + region)
- Streaming responses
- Model listing & health checks
"""

import json
from typing import Any, Optional

import httpx

from antigravity.config import (
    AgentConfig,
    GEMINI_API_KEY,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_CLOUD_REGION,
    VERTEX_AI_ENABLED,
)

# ─── Configuration ──────────────────────────────────────────────────
# Endpoints
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
VERTEX_AI_BASE = (
    f"https://{GOOGLE_CLOUD_REGION}-aiplatform.googleapis.com/v1/projects"
    f"/{GOOGLE_CLOUD_PROJECT}/locations/{GOOGLE_CLOUD_REGION}/publishers/google"
)

# Default models
GEMINI_FLASH = "gemini-2.0-flash"
GEMINI_PRO = "gemini-2.0-pro"
GEMINI_FLASH_THINKING = "gemini-2.0-flash-thinking"


class GeminiClient:
    """
    Client for Google Gemini API.

    Can use either:
    1. Direct API key (simpler, for dev/testing)
    2. Vertex AI (production, Google Cloud integration)
    """

    def __init__(
        self,
        api_key: str = GEMINI_API_KEY,
        project: str = GOOGLE_CLOUD_PROJECT,
        region: str = GOOGLE_CLOUD_REGION,
        timeout: float = 120.0,
        use_vertex: bool = VERTEX_AI_ENABLED,
    ):
        self.api_key = api_key
        self.project = project
        self.region = region
        self.timeout = timeout
        if use_vertex and not project:
            # If Vertex is desired but project is unset, fall back to direct API
            # only if an API key is configured. Otherwise, fail fast with a
            # clear error message.
            if not api_key:
                raise ValueError(
                    "Vertex AI is enabled but no Google Cloud project is configured. "
                    "Set GOOGLE_CLOUD_PROJECT (or run: gcloud config set project <id>) "
                    "or set GEMINI_API_KEY to use the direct API."
                )
            use_vertex = False

        # Force disable Vertex AI if no project configured
        self.use_vertex = use_vertex and bool(project) and project != ""

        if self.use_vertex:
            self.base_url = (
                f"https://{region}-aiplatform.googleapis.com/v1/projects"
                f"/{project}/locations/{region}/publishers/google/models"
            )
        else:
            self.base_url = GEMINI_API_BASE

    def _get_model_name(self, agent: AgentConfig) -> str:
        """Map agent config model to Gemini model if needed."""
        model = agent.model

        # If agent already specifies a Gemini model, use it directly
        if model.startswith("gemini-"):
            return model

        # Map local model types to Gemini equivalents
        model_map = {
            "architect": GEMINI_PRO,         # Best reasoning for architecture
            "fixer": GEMINI_FLASH,            # Fast for bug fixes
            "coder": GEMINI_FLASH,            # Fast for code generation
            "qa": GEMINI_FLASH_THINKING,      # Thinking model for deep review
        }

        return model_map.get(agent.role, GEMINI_FLASH)

    def _build_url(self, model: str, stream: bool = False) -> str:
        """Build the API URL for the request."""
        if self.use_vertex:
            action = "streamGenerateContent" if stream else "generateContent"
            return f"{self.base_url}/{model}:{action}"
        else:
            action = "streamGenerateContent" if stream else "generateContent"
            return f"{self.base_url}/models/{model}:{action}?key={self.api_key}"

    def _build_payload(
        self,
        agent: AgentConfig,
        user_message: str,
        context: Optional[str] = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Build the Gemini API request payload."""
        parts: list[dict[str, str]] = []

        if context:
            parts.append({"text": f"KONTEXT:\n```\n{context}\n```\n\n"})

        parts.append({"text": user_message})

        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": parts,
                }
            ],
            "systemInstruction": {
                "parts": [{"text": agent.system_prompt}]
            },
            "generationConfig": {
                "temperature": agent.temperature,
                "maxOutputTokens": agent.max_tokens,
                "topP": 0.95,
            },
        }

        return payload

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}

        if self.use_vertex:
            # For Vertex AI, use gcloud auth token
            import subprocess

            try:
                result = subprocess.run(
                    ["gcloud", "auth", "print-access-token"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    token = result.stdout.strip()
                    headers["Authorization"] = f"Bearer {token}"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                raise ConnectionError(
                    "Cannot get gcloud access token. Run: gcloud auth login"
                )

        return headers

    def chat(
        self,
        agent: AgentConfig,
        user_message: str,
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Send a chat request to Gemini.

        Args:
            agent: The agent configuration
            user_message: The user/task message
            context: Optional additional context

        Returns:
            dict with keys: content, model, usage, raw_response
        """
        model = self._get_model_name(agent)
        url = self._build_url(model, stream=False)
        payload = self._build_payload(agent, user_message, context)
        headers = self._get_headers()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                # Nur Vertex AI verwenden, wenn Projekt und Region korrekt gesetzt sind
                if use_vertex and project and region and project.strip() and region.strip():
                    self.use_vertex = True
                    self.base_url = (
                        f"https://{region}-aiplatform.googleapis.com/v1/projects"
                        f"/{project}/locations/{region}/publishers/google/models"
                    )
                else:
                    self.use_vertex = False
                    self.base_url = GEMINI_API_BASE
                    if use_vertex and (not project or not project.strip()):
                        print("⚠️  Vertex AI aktiviert, aber GOOGLE_CLOUD_PROJECT ist nicht gesetzt. Fallback auf direkte Gemini API.")
                    if use_vertex and (not region or not region.strip()):
                        print("⚠️  Vertex AI aktiviert, aber GOOGLE_CLOUD_REGION ist nicht gesetzt. Fallback auf direkte Gemini API.")
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = exc.response.text[:500]
            if status == 403:
                raise PermissionError(
                    f"Gemini API access denied (403). Check GEMINI_API_KEY or "
                    f"Google Cloud permissions. Response: {body}"
                )
            if status == 429:
                raise RuntimeError(
                    f"Gemini API rate limit hit (429). Wait and retry. "
                    f"Response: {body}"
                )
            raise RuntimeError(
                f"Gemini API error {status}: {body}"
            )

        # Parse response
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates in Gemini response")

            content_parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in content_parts)
        except (KeyError, IndexError) as exc:
            data_str = str(data)
            raise ValueError(
                f"Unexpected Gemini response format: {data_str[:300]}"
            ) from exc

        usage_meta = data.get("usageMetadata", {})

        return {
            "content": content,
            "model": model,
            "usage": {
                "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                "total_tokens": usage_meta.get("totalTokenCount", 0),
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
        Stream a chat response from Gemini (yields chunks).

        Yields:
            str: Content chunks as they arrive
        """
        model = self._get_model_name(agent)
        url = self._build_url(model, stream=True)
        # Add alt=sse for streaming in direct API mode
        if not self.use_vertex and "?" in url:
            url += "&alt=sse"
        payload = self._build_payload(agent, user_message, context, stream=True)
        headers = self._get_headers()

        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST", url, json=payload, headers=headers
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
                        candidates = chunk.get("candidates", [])
                        if candidates:
                            parts = (
                                candidates[0]
                                .get("content", {})
                                .get("parts", [])
                            )
                            for part in parts:
                                text = part.get("text", "")
                                if text:
                                    yield text
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    def list_models(self) -> list[dict[str, Any]]:
        """List available Gemini models."""
        try:
            # Safety: Never use Vertex if project is empty
            if self.use_vertex and not self.project:
                return []

            if self.use_vertex:
                # Vertex AI model listing
                url = (
                    f"https://{self.region}-aiplatform.googleapis.com/v1/"
                    f"projects/{self.project}/locations/{self.region}/"
                    f"publishers/google/models"
                )
            else:
                url = f"{self.base_url}/models?key={self.api_key}"

            headers = self._get_headers()

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("models", [])
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError):
            return []

    def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            if not self.api_key and not self.use_vertex:
                return False

            # Safety: Never use Vertex if project is empty
            if self.use_vertex and not self.project:
                return False

            if self.use_vertex:
                url = (
                    f"https://{self.region}-aiplatform.googleapis.com/v1/"
                    f"projects/{self.project}/locations/{self.region}/"
                    f"publishers/google/models"
                )
            else:
                url = f"{self.base_url}/models?key={self.api_key}"

            headers = self._get_headers()

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False


# ─── Singleton for convenience ──────────────────────────────────────
_default_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get the default GeminiClient instance."""
    global _default_client
    if _default_client is None:
        _default_client = GeminiClient()
    return _default_client
