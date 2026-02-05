from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from automation.core.providers import ProviderError, provider_from_dict
from automation.core.router import ModelSpec, Router
from automation.utils.files import timestamp_id, write_json


@dataclass
class RunResult:
    task_type: str
    text: str
    provider: Optional[str] = None
    model: Optional[str] = None
    usage: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class Runner:
    def __init__(
        self,
        router: Router,
        execute: bool,
        run_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        log_path: Optional[str] = None,
    ) -> None:
        self.router = router
        self.execute = execute
        self.run_id = run_id or timestamp_id()
        self.system_prompt = system_prompt or (
            "Du bist ein praeziser, pragmatischer Operator fuer Content- und Business-Systeme."
        )
        self._providers: Dict[str, Any] = {}
        self._events: List[Dict[str, Any]] = []
        self.log_path = log_path

    def _get_provider(self, name: str):
        if name in self._providers:
            return self._providers[name]
        cfg = self.router.provider_config(name)
        provider = provider_from_dict(name, cfg)
        self._providers[name] = provider
        return provider

    def _record(self, data: Dict[str, Any]) -> None:
        self._events.append(data)

    def run_task(
        self,
        task_type: str,
        prompt: str,
        override_tier: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
    ) -> RunResult:
        candidates = self.router.select_models(task_type, override_tier=override_tier)
        if not candidates:
            return RunResult(task_type=task_type, text="", error="No models configured")

        if not self.execute:
            chosen = candidates[0]
            result = RunResult(
                task_type=task_type,
                text=f"[DRY RUN] {task_type} output placeholder.",
                provider=chosen.provider,
                model=chosen.model,
            )
            self._record(
                {
                    "task_type": task_type,
                    "provider": chosen.provider,
                    "model": chosen.model,
                    "dry_run": True,
                }
            )
            return result

        last_error: Optional[str] = None
        for spec in candidates:
            try:
                provider = self._get_provider(spec.provider)
                response = provider.chat(
                    model=spec.model,
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                    system_prompt=self.system_prompt,
                    temperature=temperature if temperature is not None else spec.temperature,
                    max_output_tokens=max_output_tokens or spec.max_output_tokens,
                )
                result = RunResult(
                    task_type=task_type,
                    text=response.get("text", ""),
                    provider=spec.provider,
                    model=spec.model,
                    usage=response.get("usage", {}),
                )
                self._record(
                    {
                        "task_type": task_type,
                        "provider": spec.provider,
                        "model": spec.model,
                        "usage": result.usage,
                    }
                )
                return result
            except ProviderError as exc:
                last_error = str(exc)
                self._record(
                    {
                        "task_type": task_type,
                        "provider": spec.provider,
                        "model": spec.model,
                        "error": last_error,
                    }
                )
                continue

        return RunResult(task_type=task_type, text="", error=last_error or "All providers failed")

    def write_log(self) -> Optional[str]:
        if not self.log_path:
            return None
        write_json(
            self.log_path,
            {
                "run_id": self.run_id,
                "events": self._events,
            },
        )
        return str(self.log_path)
