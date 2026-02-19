"""
Soul Spawner - Dynamic Sub-Agent Selection System

The 4 Core Agents (Architect, Builder, MoneyMaker, Operator) use this
to spawn specialists from the pre-defined library.

Key Principle: Values inherit, identity does not.
- Sub-agents get: role, standards, scope, task
- Sub-agents never get: core agent identity or soul

Based on research:
- "Lost in the Middle" - soul goes first in context, always
- NAACL 2024 Role-Play Prompting - experiential > imperative
- EMNLP 2024 Multi-Expert Prompting - multiple viewpoints + debate
- "Persona is a Double-edged Sword" - miscalibrated persona degrades output
- Google DeepMind - accuracy saturates past 4 concurrent agents
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


SOULS_DIR = Path(__file__).parent
CORE_DIR = SOULS_DIR / "core"
SPECIALISTS_DIR = SOULS_DIR / "specialists"
TEAMS_DIR = SOULS_DIR / "teams"

MAX_CONCURRENT_AGENTS = 4  # DeepMind research: coordination tax past 4


@dataclass
class Specialist:
    """A pre-defined specialist template from the library."""
    name: str
    domain: str
    spawn_context: str
    values: list
    model_preference: str
    category: str  # engineering, revenue, operations, research, content


@dataclass
class SpawnedAgent:
    """A specialist instance with task-specific context injected."""
    specialist: Specialist
    task: str
    business_context: str
    spawned_by: str  # which core agent spawned this
    system_prompt: str = ""

    def __post_init__(self):
        self.system_prompt = self._build_prompt()

    def _build_prompt(self) -> str:
        """Build the system prompt with soul-first architecture.

        Structure (based on Lost in the Middle research):
        1. FIRST: Identity/Role (highest attention weight)
        2. MIDDLE: Standards and values (lower attention, but structured)
        3. LAST: Specific task (high attention weight)
        """
        values_str = "\n".join(f"- {v}" for v in self.specialist.values)

        return f"""{self.specialist.spawn_context}

## Values (inherited from {self.spawned_by})
{values_str}

## Business Context
{self.business_context}

## Your Task
{self.task}

Deliver your output in structured JSON format.
"""


class SoulSpawner:
    """Loads specialist templates and spawns configured sub-agents.

    Usage:
        spawner = SoulSpawner()

        # List available specialists
        specialists = spawner.list_specialists()
        specialists = spawner.list_specialists(category="engineering")

        # Find the right specialist for a task
        specialist = spawner.find_specialist("code review for auth module")

        # Spawn a configured sub-agent
        agent = spawner.spawn(
            specialist_key="code_reviewer",
            task="Review the authentication module for security issues",
            business_context="BMA product backend, handles DIN 14675 data",
            spawned_by="builder"
        )

        # Use agent.system_prompt in your AI call
        result = await router.query(agent.system_prompt, model=agent.specialist.model_preference)
    """

    def __init__(self):
        self._specialists: dict[str, Specialist] = {}
        self._core_souls: dict[str, str] = {}
        self._load_specialists()
        self._load_core_souls()

    def _load_specialists(self):
        """Load all specialist templates from YAML files."""
        if not SPECIALISTS_DIR.exists():
            return

        for yaml_file in SPECIALISTS_DIR.glob("*.yaml"):
            category = yaml_file.stem
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            if not data:
                continue

            for key, spec in data.items():
                self._specialists[key] = Specialist(
                    name=spec.get("name", key),
                    domain=spec.get("domain", ""),
                    spawn_context=spec.get("spawn_context", "").strip(),
                    values=spec.get("values", []),
                    model_preference=spec.get("model_preference", "ollama/qwen2.5"),
                    category=category,
                )

    def _load_core_souls(self):
        """Load core soul files for reference."""
        if not CORE_DIR.exists():
            return

        for md_file in CORE_DIR.glob("*.md"):
            with open(md_file) as f:
                self._core_souls[md_file.stem] = f.read()

    def list_specialists(self, category: Optional[str] = None) -> dict[str, Specialist]:
        """List available specialists, optionally filtered by category."""
        if category:
            return {k: v for k, v in self._specialists.items() if v.category == category}
        return dict(self._specialists)

    def get_specialist(self, key: str) -> Optional[Specialist]:
        """Get a specific specialist by key."""
        return self._specialists.get(key)

    def find_specialist(self, task_description: str) -> list[tuple[str, Specialist]]:
        """Find specialists whose domain matches the task description.

        Returns a ranked list of (key, specialist) tuples.
        Simple keyword matching - for production use, route through
        the unified_router for semantic matching.
        """
        task_lower = task_description.lower()
        matches = []

        for key, spec in self._specialists.items():
            domain_lower = spec.domain.lower()
            name_lower = spec.name.lower()

            # Score based on word overlap
            task_words = set(task_lower.split())
            domain_words = set(domain_lower.split())
            name_words = set(name_lower.split())

            overlap = len(task_words & (domain_words | name_words))
            if overlap > 0:
                matches.append((key, spec, overlap))

        # Sort by overlap score descending
        matches.sort(key=lambda x: x[2], reverse=True)
        return [(k, s) for k, s, _ in matches]

    def spawn(
        self,
        specialist_key: str,
        task: str,
        business_context: str = "",
        spawned_by: str = "architect",
    ) -> Optional[SpawnedAgent]:
        """Spawn a specialist sub-agent with task-specific context.

        Args:
            specialist_key: Key from the specialist library
            task: The specific task to accomplish
            business_context: Business-specific context injected at spawn time
            spawned_by: Which core agent is spawning this specialist

        Returns:
            SpawnedAgent with a ready-to-use system_prompt, or None if key not found
        """
        specialist = self._specialists.get(specialist_key)
        if not specialist:
            return None

        return SpawnedAgent(
            specialist=specialist,
            task=task,
            business_context=business_context,
            spawned_by=spawned_by,
        )

    def spawn_multi_expert(
        self,
        specialist_keys: list[str],
        task: str,
        business_context: str = "",
        spawned_by: str = "architect",
    ) -> list[SpawnedAgent]:
        """Spawn multiple specialists for multi-expert debate.

        Based on EMNLP 2024 research: simulating multiple expert viewpoints
        then having them debate boosted truthfulness by 8.69%.

        Enforces MAX_CONCURRENT_AGENTS limit (DeepMind coordination tax).
        """
        keys = specialist_keys[:MAX_CONCURRENT_AGENTS]
        agents = []

        for key in keys:
            agent = self.spawn(key, task, business_context, spawned_by)
            if agent:
                agents.append(agent)

        return agents

    def get_core_soul(self, role: str) -> Optional[str]:
        """Get a core soul file content by role name.

        Args:
            role: One of 'architect', 'builder', 'money_maker', 'operator'
        """
        return self._core_souls.get(role)

    def get_spawn_catalog(self) -> dict:
        """Get a structured catalog of all available specialists.

        Useful for core agents to understand what's available.
        """
        catalog = {}
        for key, spec in self._specialists.items():
            if spec.category not in catalog:
                catalog[spec.category] = []
            catalog[spec.category].append({
                "key": key,
                "name": spec.name,
                "domain": spec.domain,
                "model": spec.model_preference,
            })
        return catalog

    def stats(self) -> dict:
        """Return stats about the soul system."""
        categories = {}
        for spec in self._specialists.values():
            categories[spec.category] = categories.get(spec.category, 0) + 1

        return {
            "core_souls": len(self._core_souls),
            "total_specialists": len(self._specialists),
            "categories": categories,
            "max_concurrent": MAX_CONCURRENT_AGENTS,
        }


# Convenience function
def get_spawner() -> SoulSpawner:
    """Get a configured SoulSpawner instance."""
    return SoulSpawner()


if __name__ == "__main__":
    import json

    spawner = get_spawner()

    print("=" * 60)
    print("  SOUL SPAWNER - Agent Design System")
    print("=" * 60)
    print()

    # Stats
    stats = spawner.stats()
    print(f"  Core Souls:       {stats['core_souls']}")
    print(f"  Specialists:      {stats['total_specialists']}")
    print(f"  Max Concurrent:   {stats['max_concurrent']}")
    print()

    # Categories
    print("  Specialist Library:")
    for cat, count in stats["categories"].items():
        print(f"    {cat}: {count} specialists")
    print()

    # Full catalog
    catalog = spawner.get_spawn_catalog()
    for category, specialists in catalog.items():
        print(f"  [{category.upper()}]")
        for s in specialists:
            print(f"    - {s['key']}: {s['name']} ({s['model']})")
        print()

    # Demo spawn
    print("  Demo: Spawning code_reviewer for auth module review")
    print("-" * 60)
    agent = spawner.spawn(
        specialist_key="code_reviewer",
        task="Review the authentication module in crm/auth.js for security vulnerabilities",
        business_context="BMA product CRM handling customer data, GDPR relevant",
        spawned_by="builder",
    )
    if agent:
        print(agent.system_prompt)
    print("=" * 60)
