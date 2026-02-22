"""
Unified AI Router — Multi-Muscle Architecture
==============================================
Routes tasks to SPECIALIZED models per task type:
  Brain (planning/decisions) → Gemini Pro
  Coding (implementation)    → Qwen 14B (local, free)
  Research (deep analysis)   → Kimi K2.5 (256K context)
  Creative (content/writing) → Gemini Flash
  Reasoning (review/QA)      → DeepSeek R1 (local)
  Fast (quick iterations)    → Qwen 7B (local)
  Vibe Code (prototyping)    → Code Llama (local)

Each "muscle" has its own fallback chain.
Saves money, parallelizes tasks, and uses the best model for each job.
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from antigravity.config import AGENTS, AgentConfig


# ─── Multi-Muscle Task Categories ──────────────────────────────────
MUSCLE_MAP = {
    # Brain muscle: planning, architecture, complex decisions
    "brain": {
        "keywords": ["plan", "architect", "design", "strategy", "decision", "refactor"],
        "provider_priority": ["gemini", "moonshot", "ollama"],
        "gemini_model": "gemini-2.0-pro",
        "ollama_model": "qwen2.5-coder:14b",
    },
    # Coding muscle: implementation, features, bug fixes
    "coding": {
        "keywords": ["code", "implement", "feature", "function", "class", "module", "fix", "bug"],
        "provider_priority": ["ollama", "gemini", "moonshot"],
        "gemini_model": "gemini-2.0-flash",
        "ollama_model": "qwen2.5-coder:14b",
    },
    # Research muscle: analysis, trends, deep investigation
    "research": {
        "keywords": ["research", "analyze", "scan", "trend", "investigate", "compare", "study"],
        "provider_priority": ["moonshot", "gemini", "ollama"],
        "gemini_model": "gemini-2.0-pro",
        "ollama_model": "qwen2.5-coder:14b",
    },
    # Creative muscle: content, writing, marketing
    "creative": {
        "keywords": ["write", "content", "post", "tweet", "script", "copy", "headline", "story"],
        "provider_priority": ["gemini", "moonshot", "ollama"],
        "gemini_model": "gemini-2.0-flash",
        "ollama_model": "qwen2.5-coder:7b",
    },
    # Reasoning muscle: review, QA, verification
    "reasoning": {
        "keywords": ["review", "test", "qa", "verify", "check", "lint", "audit", "security"],
        "provider_priority": ["ollama", "gemini", "moonshot"],
        "gemini_model": "gemini-2.0-flash-thinking",
        "ollama_model": "deepseek-r1:7b",
    },
    # Fast muscle: quick iterations, simple tasks
    "fast": {
        "keywords": ["quick", "simple", "translate", "format", "convert", "list"],
        "provider_priority": ["ollama", "gemini", "moonshot"],
        "gemini_model": "gemini-2.0-flash",
        "ollama_model": "qwen2.5-coder:7b",
    },
}


# ─── Provider Status ────────────────────────────────────────────────
@dataclass
class ProviderStatus:
    """Track health/availability of each provider."""
    name: str
    available: bool = False
    last_check: float = 0.0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    total_requests: int = 0
    total_tokens: int = 0


@dataclass
class RouterConfig:
    """Configuration for the unified router."""
    # Provider priority (first available wins)
    provider_priority: list[str] = field(
        default_factory=lambda: ["gemini", "ollama", "moonshot"]
    )
    # Task-specific overrides (legacy, kept for backwards compat)
    task_routing: dict[str, str] = field(
        default_factory=lambda: {
            "architecture": "gemini",
            "review": "gemini",
            "code": "ollama",
            "fix": "ollama",
            "qa": "ollama",
            "research": "moonshot",
            "creative": "gemini",
            "fast": "ollama",
        }
    )
    # Force offline (only Ollama)
    offline_mode: bool = False
    # Max retries per provider
    max_retries: int = 2
    # Health check interval (seconds)
    health_check_interval: float = 300.0


class UnifiedRouter:
    """
    Multi-Muscle AI Router: Routes tasks to specialized models.

    Instead of sending everything to one model, each task type
    gets routed to the model that's best at it:

    - Brain tasks (planning) → Gemini Pro (smart, expensive)
    - Coding tasks → Qwen 14B local (free, fast for code)
    - Research → Kimi K2.5 (256K context, free)
    - Creative → Gemini Flash (fast, good writing)
    - Reasoning → DeepSeek R1 local (free, thinks deep)
    - Quick tasks → Qwen 7B local (fastest, free)

    Usage:
        router = UnifiedRouter()
        await router.check_providers()
        result = await router.execute("Fix this bug", agent_key="fixer")
        result = await router.execute_muscle("research", "Analyze market trends")
    """

    def __init__(self, config: Optional[RouterConfig] = None):
        self.config = config or RouterConfig()
        self.providers: dict[str, ProviderStatus] = {
            "gemini": ProviderStatus(name="gemini"),
            "ollama": ProviderStatus(name="ollama"),
            "moonshot": ProviderStatus(name="moonshot"),
        }
        self._gemini_client = None
        self._ollama_client = None

        # Track muscle usage for reporting
        self._muscle_stats: dict[str, dict[str, int]] = {
            m: {"calls": 0, "tokens": 0} for m in MUSCLE_MAP
        }

        # Check for offline mode env var
        if os.getenv("OFFLINE_MODE", "").lower() in ("1", "true", "yes"):
            self.config.offline_mode = True
            self.config.provider_priority = ["ollama"]

    def _get_gemini_client(self):
        """Lazy-load Gemini client."""
        if self._gemini_client is None:
            from antigravity.gemini_client import GeminiClient
            self._gemini_client = GeminiClient()
        return self._gemini_client

    def _get_ollama_client(self):
        """Lazy-load Ollama client."""
        if self._ollama_client is None:
            from antigravity.ollama_client import OllamaClient
            self._ollama_client = OllamaClient()
        return self._ollama_client

    async def check_providers(self) -> dict[str, bool]:
        """Check health of all providers."""
        results: dict[str, bool] = {}

        # Check Gemini
        if not self.config.offline_mode:
            try:
                client = self._get_gemini_client()
                available = await asyncio.to_thread(client.health_check)
                self.providers["gemini"].available = available
                self.providers["gemini"].last_check = time.time()
                results["gemini"] = available
            except Exception:
                self.providers["gemini"].available = False
                results["gemini"] = False

        # Check Ollama
        try:
            client = self._get_ollama_client()
            available = await asyncio.to_thread(client.health_check)
            self.providers["ollama"].available = available
            self.providers["ollama"].last_check = time.time()
            results["ollama"] = available
        except Exception:
            self.providers["ollama"].available = False
            results["ollama"] = False

        # Check Moonshot (simple HTTP check)
        if not self.config.offline_mode:
            moonshot_key = os.getenv("MOONSHOT_API_KEY", "")
            self.providers["moonshot"].available = bool(moonshot_key)
            results["moonshot"] = bool(moonshot_key)

        return results

    def detect_muscle(self, prompt: str, task_type: str = "") -> str:
        """Detect which muscle to use based on prompt content and task type."""
        text = f"{task_type} {prompt}".lower()

        scores: dict[str, int] = {}
        for muscle, config in MUSCLE_MAP.items():
            score = sum(1 for kw in config["keywords"] if kw in text)
            if score > 0:
                scores[muscle] = score

        if scores:
            return max(scores, key=scores.get)

        # Default based on agent role mapping
        role_to_muscle = {
            "architect": "brain",
            "fixer": "coding",
            "coder": "coding",
            "qa": "reasoning",
        }
        return role_to_muscle.get(task_type, "coding")

    def _select_provider(self, task_type: str = "code") -> str:
        """Select the best available provider for a task using multi-muscle routing."""
        if self.config.offline_mode:
            return "ollama"

        # Use muscle-specific provider priority
        muscle = self.detect_muscle("", task_type)
        muscle_config = MUSCLE_MAP.get(muscle, MUSCLE_MAP["coding"])

        for provider in muscle_config["provider_priority"]:
            if self.providers.get(provider, ProviderStatus(name="")).available:
                return provider

        # Fall through global priority list
        for provider in self.config.provider_priority:
            if self.providers.get(provider, ProviderStatus(name="")).available:
                return provider

        return "ollama"

    def _route_to_agent(self, task: dict[str, Any]) -> str:
        """Route task to the appropriate agent role."""
        task_type = task.get("type", "code").lower()
        prompt = task.get("prompt", "").lower()

        if any(kw in task_type or kw in prompt
               for kw in ["architecture", "refactor", "design", "structure"]):
            return "architect"
        elif any(kw in task_type or kw in prompt
                 for kw in ["bug", "error", "fix", "import", "traceback"]):
            return "fixer"
        elif any(kw in task_type or kw in prompt
                 for kw in ["test", "qa", "review", "lint", "check"]):
            return "qa"
        elif any(kw in task_type or kw in prompt
                 for kw in ["research", "analyze", "scan", "trend"]):
            return "architect"  # Research uses architect agent with research muscle
        elif any(kw in task_type or kw in prompt
                 for kw in ["write", "content", "post", "tweet", "script"]):
            return "coder"  # Creative uses coder agent with creative muscle
        else:
            return "coder"

    async def execute(
        self,
        prompt: str,
        agent_key: str = "coder",
        context: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute a task using the best available provider and muscle.

        Args:
            prompt: The task prompt
            agent_key: Agent role (architect, fixer, coder, qa)
            context: Optional context (file contents, errors, etc.)
            task_type: Optional task type for routing (overrides agent_key)

        Returns:
            dict with: content, model, provider, muscle, usage, success
        """
        agent = AGENTS.get(agent_key)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_key}. Available: {list(AGENTS.keys())}")

        effective_type = task_type or agent.role
        muscle = self.detect_muscle(prompt, effective_type)
        provider = self._select_provider(effective_type)

        print(f"🔀 Router → {provider.upper()} | Muscle: {muscle} | Agent: {agent.name} | Task: {effective_type}")

        # Try with retries and failover
        errors: list[str] = []
        tried_providers: list[str] = []

        # Get muscle-specific fallback chain
        muscle_config = MUSCLE_MAP.get(muscle, MUSCLE_MAP["coding"])
        fallback_chain = muscle_config["provider_priority"]

        for attempt in range(self.config.max_retries + 1):
            if provider in tried_providers and attempt > 0:
                # Use muscle-specific fallback chain
                for next_p in fallback_chain:
                    if next_p not in tried_providers and self.providers.get(next_p, ProviderStatus(name="")).available:
                        provider = next_p
                        break
                else:
                    break  # No more providers

            tried_providers.append(provider)

            try:
                start = time.time()

                if provider == "gemini":
                    result = await self._execute_gemini(agent, prompt, context)
                elif provider == "ollama":
                    result = await self._execute_ollama(agent, prompt, context)
                elif provider == "moonshot":
                    result = await self._execute_moonshot(agent, prompt, context)
                else:
                    raise ValueError(f"Unknown provider: {provider}")

                elapsed = (time.time() - start) * 1000
                status = self.providers[provider]
                status.total_requests += 1
                status.total_tokens += result.get("usage", {}).get("total_tokens", 0)
                status.avg_latency_ms = (
                    (status.avg_latency_ms * (status.total_requests - 1) + elapsed)
                    / status.total_requests
                )

                # Track muscle usage
                self._muscle_stats[muscle]["calls"] += 1
                self._muscle_stats[muscle]["tokens"] += result.get("usage", {}).get("total_tokens", 0)

                result["provider"] = provider
                result["muscle"] = muscle
                result["latency_ms"] = round(elapsed, 1)
                result["success"] = True
                return result

            except (ConnectionError, TimeoutError, PermissionError) as exc:
                error_msg = f"{provider}: {exc}"
                errors.append(error_msg)
                print(f"⚠️  {error_msg}")
                self.providers[provider].error_count += 1
                self.providers[provider].available = False
                continue

            except Exception as exc:
                error_msg = f"{provider}: {exc}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                break

        return {
            "content": "",
            "model": "",
            "provider": "none",
            "muscle": muscle,
            "usage": {},
            "success": False,
            "errors": errors,
        }

    async def execute_muscle(
        self,
        muscle: str,
        prompt: str,
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute a task targeting a specific muscle directly.

        This bypasses agent routing and sends directly to the best
        provider for the specified muscle type.

        Args:
            muscle: One of brain, coding, research, creative, reasoning, fast
            prompt: The task prompt
            context: Optional context

        Returns:
            dict with: content, model, provider, muscle, usage, success
        """
        muscle_config = MUSCLE_MAP.get(muscle)
        if not muscle_config:
            raise ValueError(f"Unknown muscle: {muscle}. Available: {list(MUSCLE_MAP.keys())}")

        # Map muscle to best agent
        muscle_to_agent = {
            "brain": "architect",
            "coding": "coder",
            "research": "architect",
            "creative": "coder",
            "reasoning": "qa",
            "fast": "coder",
        }
        agent_key = muscle_to_agent.get(muscle, "coder")

        return await self.execute(
            prompt=prompt,
            agent_key=agent_key,
            context=context,
            task_type=muscle,
        )

    async def _execute_gemini(
        self, agent: AgentConfig, prompt: str, context: Optional[str]
    ) -> dict[str, Any]:
        """Execute via Gemini API."""
        client = self._get_gemini_client()
        return await asyncio.to_thread(client.chat, agent, prompt, context)

    async def _execute_ollama(
        self, agent: AgentConfig, prompt: str, context: Optional[str]
    ) -> dict[str, Any]:
        """Execute via local Ollama."""
        client = self._get_ollama_client()
        return await asyncio.to_thread(client.chat, agent, prompt, context)

    async def _execute_moonshot(
        self, agent: AgentConfig, prompt: str, context: Optional[str]
    ) -> dict[str, Any]:
        """Execute via Moonshot/Kimi API (OpenAI-compatible)."""
        import httpx

        api_key = os.getenv("MOONSHOT_API_KEY", "")
        if not api_key:
            raise ConnectionError("MOONSHOT_API_KEY not set")

        messages = [
            {"role": "system", "content": agent.system_prompt},
        ]
        if context:
            messages.append({"role": "user", "content": f"KONTEXT:\n```\n{context}\n```"})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "kimi-k2.5",
            "messages": messages,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.moonshot.ai/v1/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return {
            "content": content,
            "model": "kimi-k2.5",
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "raw_response": data,
        }

    async def run_swarm(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run multiple tasks in parallel across providers, each using optimal muscle."""
        print(f"\n🚀 Multi-Muscle Swarm: {len(tasks)} tasks across specialized models...")

        async def process(task: dict[str, Any]) -> dict[str, Any]:
            agent_key = self._route_to_agent(task)
            return await self.execute(
                prompt=str(task["prompt"]),
                agent_key=agent_key,
                context=task.get("context"),
                task_type=task.get("type"),
            )

        results = list(await asyncio.gather(*[process(t) for t in tasks]))

        # Summary
        success = sum(1 for r in results if r.get("success"))
        providers_used = set(r.get("provider", "?") for r in results)
        muscles_used = set(r.get("muscle", "?") for r in results)
        total_tokens = sum(r.get("usage", {}).get("total_tokens", 0) for r in results)

        print(f"\n✅ Swarm Complete: {success}/{len(results)} succeeded")
        print(f"   Providers: {', '.join(providers_used)}")
        print(f"   Muscles:   {', '.join(muscles_used)}")
        print(f"   Total tokens: {total_tokens:,}")

        return results

    def status_report(self) -> str:
        """Get a formatted status report of all providers and muscles."""
        lines = ["═" * 60, "🔀 MULTI-MUSCLE ROUTER STATUS", "═" * 60]

        lines.append("\n  PROVIDERS:")
        for name, status in self.providers.items():
            icon = "🟢" if status.available else "🔴"
            lines.append(
                f"    {icon} {name:12s} | "
                f"Requests: {status.total_requests:4d} | "
                f"Errors: {status.error_count:2d} | "
                f"Avg: {status.avg_latency_ms:.0f}ms | "
                f"Tokens: {status.total_tokens:,}"
            )

        lines.append("\n  MUSCLES:")
        for muscle, stats in self._muscle_stats.items():
            if stats["calls"] > 0:
                muscle_config = MUSCLE_MAP[muscle]
                lines.append(
                    f"    🦾 {muscle:12s} | "
                    f"Calls: {stats['calls']:4d} | "
                    f"Tokens: {stats['tokens']:,} | "
                    f"Primary: {muscle_config['provider_priority'][0]}"
                )

        mode = "🔒 OFFLINE" if self.config.offline_mode else "🌐 ONLINE"
        lines.append(f"\n  Mode: {mode}")
        lines.append(f"  Priority: {' → '.join(self.config.provider_priority)}")
        lines.append("═" * 60)
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# CLI Interface
# ═══════════════════════════════════════════════════════════════════

async def main() -> None:
    router = UnifiedRouter()

    if len(sys.argv) < 2:
        print("""
🔀 Multi-Muscle AI Router — Specialized Models for Every Task

Usage:
  python unified_router.py <command> [args...]

Commands:
  status              Check all provider health + muscle stats
  run <type> <prompt> Execute a task (auto-detects best muscle)
  muscle <name> <prompt>  Execute targeting specific muscle
  swarm <json_file>   Run multiple tasks from JSON
  test                Quick connectivity test

Muscles:
  brain     → Planning, architecture, complex decisions (Gemini Pro)
  coding    → Implementation, features, fixes (Qwen 14B local)
  research  → Analysis, trends, investigation (Kimi K2.5)
  creative  → Content, writing, marketing (Gemini Flash)
  reasoning → Review, QA, verification (DeepSeek R1 local)
  fast      → Quick iterations, simple tasks (Qwen 7B local)

Examples:
  python unified_router.py status
  python unified_router.py run fix "Fix import errors in config.py"
  python unified_router.py muscle research "Analyze AI agent market trends 2026"
  python unified_router.py muscle creative "Write viral tweet about AI agents"
  python unified_router.py test

Environment:
  GEMINI_API_KEY       → Google Gemini API key
  GOOGLE_CLOUD_PROJECT → Vertex AI project ID
  MOONSHOT_API_KEY     → Moonshot/Kimi API key
  OLLAMA_BASE_URL      → Ollama server (default: localhost:11434)
  OFFLINE_MODE=true    → Force local Ollama only
""")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        print("\n🔍 Checking providers...")
        results = await router.check_providers()
        print(router.status_report())
        for name, ok in results.items():
            status = "✅ ONLINE" if ok else "❌ OFFLINE"
            print(f"  {name}: {status}")

    elif command == "test":
        print("\n🧪 Running connectivity test...")
        results = await router.check_providers()

        for provider_name, available in results.items():
            if available:
                print(f"\n  Testing {provider_name}...")
                AGENTS["coder"]
                result = await router.execute(
                    "Respond with exactly: HELLO FROM {provider}. Nothing else.",
                    agent_key="coder",
                )
                if result["success"]:
                    print(f"  ✅ {provider_name}: {result['content'][:100]}")
                    print(f"     Model: {result.get('model', '?')}")
                    print(f"     Muscle: {result.get('muscle', '?')}")
                    print(f"     Latency: {result.get('latency_ms', '?')}ms")
                else:
                    print(f"  ❌ {provider_name}: Failed")

    elif command == "run":
        if len(sys.argv) < 4:
            print("Usage: unified_router.py run <type> <prompt>")
            sys.exit(1)

        task_type = sys.argv[2]
        prompt = " ".join(sys.argv[3:])

        await router.check_providers()
        agent_key = router._route_to_agent({"type": task_type, "prompt": prompt})
        result = await router.execute(prompt, agent_key=agent_key, task_type=task_type)

        print(f"\n{'=' * 60}")
        print(f"Provider: {result.get('provider', '?')}")
        print(f"Muscle:   {result.get('muscle', '?')}")
        print(f"Model:    {result.get('model', '?')}")
        print(f"Latency:  {result.get('latency_ms', '?')}ms")
        print(f"{'=' * 60}")
        print(result.get("content", ""))
        print(f"{'=' * 60}")

    elif command == "muscle":
        if len(sys.argv) < 4:
            print("Usage: unified_router.py muscle <muscle_name> <prompt>")
            print(f"Available muscles: {', '.join(MUSCLE_MAP.keys())}")
            sys.exit(1)

        muscle_name = sys.argv[2]
        prompt = " ".join(sys.argv[3:])

        await router.check_providers()
        result = await router.execute_muscle(muscle_name, prompt)

        print(f"\n{'=' * 60}")
        print(f"Muscle:   {result.get('muscle', '?')}")
        print(f"Provider: {result.get('provider', '?')}")
        print(f"Model:    {result.get('model', '?')}")
        print(f"Latency:  {result.get('latency_ms', '?')}ms")
        print(f"{'=' * 60}")
        print(result.get("content", ""))
        print(f"{'=' * 60}")

    elif command == "swarm":
        if len(sys.argv) < 3:
            print("Usage: unified_router.py swarm <tasks.json>")
            sys.exit(1)

        with open(sys.argv[2]) as fh:
            tasks = json.load(fh)

        await router.check_providers()
        results = await router.run_swarm(tasks)

        for i, result in enumerate(results):
            print(f"\n--- Task {i + 1} ({result.get('provider', '?')} / {result.get('muscle', '?')}) ---")
            print(result.get("content", "")[:500])

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
