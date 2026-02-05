from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class ModelSpec:
    provider: str
    model: str
    max_output_tokens: Optional[int] = None
    temperature: float = 0.6


class Router:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.providers_cfg = config.get("providers", {})
        self.models_cfg = config.get("models", {})
        self.routing = config.get("routing", {})
        self.fallback_order = config.get("fallback_order", [])

    def _tier_sequence(self, primary: str) -> List[str]:
        tiers = [primary]
        for tier in self.fallback_order:
            if tier not in tiers:
                tiers.append(tier)
        return tiers

    def select_models(self, task_type: str, override_tier: Optional[str] = None) -> List[ModelSpec]:
        tier = override_tier or self.routing.get(task_type, "balanced")
        candidates: List[ModelSpec] = []
        for tier_name in self._tier_sequence(tier):
            models = self.models_cfg.get(tier_name, [])
            for item in models:
                candidates.append(
                    ModelSpec(
                        provider=item.get("provider", ""),
                        model=item.get("model", ""),
                        max_output_tokens=item.get("max_output_tokens"),
                        temperature=item.get("temperature", 0.6),
                    )
                )
        return [c for c in candidates if c.provider and c.model]

    def provider_config(self, provider_name: str) -> Dict[str, Any]:
        return self.providers_cfg.get(provider_name, {})

    def provider_names(self) -> Iterable[str]:
        return self.providers_cfg.keys()
