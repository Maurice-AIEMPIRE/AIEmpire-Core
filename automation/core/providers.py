from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from automation.utils.files import env_or_default


class ProviderError(RuntimeError):
    pass


@dataclass
class ProviderConfig:
    name: str
    type: str
    base_url: str
    api_key_env: str
    headers_env: Optional[Dict[str, str]] = None
    auth_header: str = "Authorization"
    auth_prefix: str = "Bearer"


class OpenAICompatProvider:
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def _build_headers(self) -> Dict[str, str]:
        api_key = env_or_default(self.config.api_key_env)
        if not api_key and self.config.name.lower() == "ollama":
            api_key = "local"
        if not api_key:
            raise ProviderError(
                f"Missing API key env: {self.config.api_key_env} for provider {self.config.name}"
            )
        headers = {
            "Content-Type": "application/json",
            self.config.auth_header: f"{self.config.auth_prefix} {api_key}",
        }
        if self.config.headers_env:
            for header, env_key in self.config.headers_env.items():
                value = env_or_default(env_key)
                if value:
                    headers[header] = value
        return headers

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.6,
        max_output_tokens: Optional[int] = None,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}, *messages]
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_output_tokens:
            payload["max_tokens"] = max_output_tokens

        endpoint = self.config.base_url.rstrip("/") + "/chat/completions"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers=self._build_headers(),
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8") if exc.fp else str(exc)
            raise ProviderError(f"Provider {self.config.name} error: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"Provider {self.config.name} connection error: {exc}") from exc

        data = json.loads(body)
        choices = data.get("choices") or []
        content: str = ""
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content") or ""
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part) for part in content
                )
        usage = data.get("usage") or {}
        return {"text": content, "usage": usage, "raw": data}


class AnthropicMessagesProvider:
    def __init__(self, name: str, base_url: str, api_key_env: str, version: str = "2023-06-01") -> None:
        self.name = name
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.version = version

    def _endpoint(self) -> str:
        if self.base_url.rstrip("/").endswith("/messages"):
            return self.base_url.rstrip("/")
        return self.base_url.rstrip("/") + "/messages"

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.6,
        max_output_tokens: Optional[int] = None,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        api_key = env_or_default(self.api_key_env)
        if not api_key:
            raise ProviderError(f"Missing API key env: {self.api_key_env} for provider {self.name}")

        payload: Dict[str, Any] = {
            "model": model,
            "max_tokens": int(max_output_tokens or 1024),
            "messages": messages,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": self.version,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self._endpoint(), data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8") if exc.fp else str(exc)
            raise ProviderError(f"Provider {self.name} error: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"Provider {self.name} connection error: {exc}") from exc

        data = json.loads(body)
        content_blocks = data.get("content") or []
        text = ""
        if isinstance(content_blocks, list):
            for block in content_blocks:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += str(block.get("text") or "")
        usage = data.get("usage") or {}
        return {"text": text, "usage": usage, "raw": data}


def provider_from_dict(name: str, data: Dict[str, Any]):
    provider_type = data.get("type", "openai_compat")
    if provider_type == "openai_compat":
        config = ProviderConfig(
            name=name,
            type=provider_type,
            base_url=data.get("base_url", "").strip(),
            api_key_env=data.get("api_key_env", "").strip(),
            headers_env=data.get("headers_env"),
            auth_header=data.get("auth_header", "Authorization"),
            auth_prefix=data.get("auth_prefix", "Bearer"),
        )
        if not config.base_url:
            raise ProviderError(f"Provider {name} missing base_url")
        if not config.api_key_env:
            raise ProviderError(f"Provider {name} missing api_key_env")
        return OpenAICompatProvider(config)

    if provider_type == "anthropic_messages":
        base_url = str(data.get("base_url", "")).strip()
        api_key_env = str(data.get("api_key_env", "")).strip()
        version = str(data.get("anthropic_version", "2023-06-01")).strip() or "2023-06-01"
        if not base_url:
            raise ProviderError(f"Provider {name} missing base_url")
        if not api_key_env:
            raise ProviderError(f"Provider {name} missing api_key_env")
        return AnthropicMessagesProvider(name=name, base_url=base_url, api_key_env=api_key_env, version=version)

    raise ProviderError(f"Unsupported provider type: {provider_type}")
