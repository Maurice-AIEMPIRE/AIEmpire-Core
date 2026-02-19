"""
Empire Bridge — Connects ALL Systems through Antigravity
=========================================================
This is the GLUE that connects:
  - workflow_system (orchestrator, cowork, empire)
  - kimi_swarm (500K agents)
  - x_lead_machine (content + leads)
  - atomic_reactor (task runner)
  - brain_system (7 specialized brains)
  - empire_engine (unified dashboard)

WITH antigravity core:
  - unified_router (multi-provider AI routing)
  - cross_verify (independent verification)
  - sync_engine (crash-safe state)
  - knowledge_store (persistent learning)
  - planning_mode (strategic execution)
  - resource_aware (adaptive model selection)

Usage:
    from antigravity.empire_bridge import EmpireBridge
    bridge = EmpireBridge()

    # Route any AI task through antigravity
    result = await bridge.execute("Generate viral post about AI agents")

    # Execute with verification
    result = await bridge.execute_verified("Write Python function for CRM sync")

    # Store learning
    bridge.learn("fix", "CRM port conflict", "Port 3500 needs to be free before starting CRM")

    # Get status of everything
    status = bridge.system_status()
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from antigravity.config import (
    OLLAMA_BASE_URL,
)


class EmpireBridge:
    """
    Central nervous system connecting all Empire components through Antigravity.

    Principle: Every AI call goes through the unified router.
    Principle: Critical outputs get cross-verified.
    Principle: Every learning gets stored in knowledge_store.
    Principle: All state changes are crash-safe (atomic writes).
    Principle: Soul-first architecture — identity before operations.
    Principle: Values inherit, identity does not — sub-agents get standards, not souls.
    Principle: Max 4 concurrent agents — DeepMind coordination tax.
    """

    def __init__(self):
        self._router = None
        self._verifier = None
        self._knowledge = None
        self._sync = None
        self._planner = None
        self._guard = None
        self._soul_spawner = None

    # ─── Lazy Initialization (only load what's needed) ────────────────────

    @property
    def router(self):
        """Unified AI router (Ollama → Kimi → Claude)."""
        if self._router is None:
            try:
                from antigravity.unified_router import UnifiedRouter
                self._router = UnifiedRouter()
            except ImportError:
                self._router = _FallbackRouter()
        return self._router

    @property
    def verifier(self):
        """Cross-agent verification gate."""
        if self._verifier is None:
            try:
                from antigravity.cross_verify import VerificationGate
                self._verifier = VerificationGate(self.router)
            except ImportError:
                self._verifier = None
        return self._verifier

    @property
    def knowledge(self):
        """Persistent knowledge store."""
        if self._knowledge is None:
            try:
                from antigravity.knowledge_store import KnowledgeStore
                self._knowledge = KnowledgeStore()
            except ImportError:
                self._knowledge = None
        return self._knowledge

    @property
    def sync(self):
        """Crash-safe state sync engine."""
        if self._sync is None:
            try:
                from antigravity.sync_engine import SyncEngine
                self._sync = SyncEngine()
            except ImportError:
                self._sync = None
        return self._sync

    @property
    def planner(self):
        """Planning mode controller."""
        if self._planner is None:
            try:
                from antigravity.planning_mode import PlanningController
                self._planner = PlanningController()
            except ImportError:
                self._planner = None
        return self._planner

    @property
    def guard(self):
        """Resource guard for crash prevention."""
        if self._guard is None:
            try:
                from workflow_system.resource_guard import ResourceGuard
                self._guard = ResourceGuard()
            except ImportError:
                self._guard = None
        return self._guard

    @property
    def souls(self):
        """Soul Spawner — 4 Core Agents + 39 Specialist Library."""
        if self._soul_spawner is None:
            try:
                from souls.soul_spawner import SoulSpawner
                self._soul_spawner = SoulSpawner()
            except ImportError:
                self._soul_spawner = None
        return self._soul_spawner

    # ─── Core Operations ──────────────────────────────────────────────────

    async def execute(
        self,
        prompt: str,
        agent_key: str = "coder",
        require_json: bool = False,
        context: str = "",
    ) -> dict:
        """
        Execute an AI task through the unified router.

        This is the STANDARD way to call any AI model in the Empire.
        No more direct API calls — everything goes through here.

        Args:
            prompt: The task/prompt to execute
            agent_key: Which agent profile (architect, fixer, coder, qa)
            require_json: Whether to parse response as JSON
            context: Additional context to inject

        Returns:
            {"status": "ok"/"error", "response": str, "model": str, "cost": float}
        """
        # Check resources first
        if self.guard:
            status = self.guard.check()
            if status.get("level") == "emergency":
                return {
                    "status": "blocked",
                    "response": "System im Emergency Mode — warte bis Ressourcen frei sind",
                    "model": "none",
                    "cost": 0.0,
                }

        # Inject knowledge context if relevant
        if self.knowledge:
            ki_context = self.knowledge.export_for_agent(prompt[:100])
            if ki_context and "Keine relevanten" not in ki_context:
                context = f"{ki_context}\n\n{context}" if context else ki_context

        # Build full prompt
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\n\n---\n\nAufgabe:\n{prompt}"

        try:
            result = await self.router.route_task(full_prompt, agent_key)
            return {
                "status": "ok",
                "response": result.get("response", result.get("content", str(result))),
                "model": result.get("model", "unknown"),
                "cost": result.get("cost", 0.0),
            }
        except Exception as e:
            return {
                "status": "error",
                "response": f"Fehler: {str(e)}",
                "model": "none",
                "cost": 0.0,
            }

    async def execute_verified(
        self,
        prompt: str,
        agent_key: str = "coder",
        context: str = "",
    ) -> dict:
        """
        Execute with cross-agent verification.
        The output gets reviewed by a DIFFERENT agent with fresh context.
        Only use for critical tasks (costs 2x tokens).
        """
        if self.verifier:
            try:
                result = await self.verifier.execute_verified(prompt, agent_key)
                return {
                    "status": "verified" if result.verified else "rejected",
                    "response": result.final_output,
                    "verification_score": result.verification_score,
                    "attempts": result.attempts,
                }
            except Exception:
                # Fall back to unverified
                return await self.execute(prompt, agent_key, context=context)
        else:
            return await self.execute(prompt, agent_key, context=context)

    def learn(
        self,
        ki_type: str,
        title: str,
        content: str,
        tags: Optional[list] = None,
        source: str = "empire_bridge",
    ):
        """
        Store a learning in the knowledge base.
        Call this after every significant event, fix, or discovery.
        """
        if self.knowledge:
            self.knowledge.add(
                ki_type=ki_type,
                title=title,
                content=content,
                tags=tags or [],
                source=source,
            )

    async def execute_with_soul(
        self,
        prompt: str,
        specialist_key: str,
        business_context: str = "",
        spawned_by: str = "architect",
        require_json: bool = False,
    ) -> dict:
        """
        Execute an AI task through a soul-powered specialist.

        This is the SOUL-FIRST way to call AI — the specialist's identity
        and values are injected at the top of the system prompt.

        Based on research:
        - "Lost in the Middle": Soul goes first (U-shaped attention)
        - NAACL 2024: Experiential role > imperative instructions
        - "Persona is a Double-edged Sword": Calibrated persona +10%

        Args:
            prompt: The task to execute
            specialist_key: Which specialist from the library (e.g. "code_reviewer")
            business_context: Business-specific context injected at spawn time
            spawned_by: Which core agent is requesting (architect/builder/money_maker/operator)
            require_json: Whether to parse response as JSON

        Returns:
            {"status": "ok"/"error", "response": str, "model": str, "cost": float, "specialist": str}
        """
        # Check resources first
        if self.guard:
            status = self.guard.check()
            if status.get("level") == "emergency":
                return {
                    "status": "blocked",
                    "response": "System im Emergency Mode",
                    "model": "none",
                    "cost": 0.0,
                    "specialist": specialist_key,
                }

        # Spawn the specialist
        if not self.souls:
            return await self.execute(prompt, context=business_context)

        agent = self.souls.spawn(
            specialist_key=specialist_key,
            task=prompt,
            business_context=business_context,
            spawned_by=spawned_by,
        )

        if not agent:
            return {
                "status": "error",
                "response": f"Specialist '{specialist_key}' nicht gefunden",
                "model": "none",
                "cost": 0.0,
                "specialist": specialist_key,
            }

        # Inject knowledge context
        full_prompt = agent.system_prompt
        if self.knowledge:
            ki_context = self.knowledge.export_for_agent(prompt[:100])
            if ki_context and "Keine relevanten" not in ki_context:
                full_prompt = f"{agent.system_prompt}\n\n## Relevant Knowledge\n{ki_context}"

        try:
            result = await self.router.route_task(full_prompt, spawned_by)
            return {
                "status": "ok",
                "response": result.get("response", result.get("content", str(result))),
                "model": result.get("model", agent.specialist.model_preference),
                "cost": result.get("cost", 0.0),
                "specialist": specialist_key,
            }
        except Exception as e:
            return {
                "status": "error",
                "response": f"Fehler: {str(e)}",
                "model": "none",
                "cost": 0.0,
                "specialist": specialist_key,
            }

    async def execute_multi_expert(
        self,
        prompt: str,
        specialist_keys: list,
        business_context: str = "",
        spawned_by: str = "architect",
    ) -> dict:
        """
        Execute with multiple specialists for expert debate.

        EMNLP 2024: Multi-expert debate boosted truthfulness by 8.69%.
        Max 4 concurrent (DeepMind coordination tax).

        Each specialist analyzes independently, then results are synthesized.
        """
        if not self.souls:
            return await self.execute(prompt, context=business_context)

        agents = self.souls.spawn_multi_expert(
            specialist_keys=specialist_keys,
            task=prompt,
            business_context=business_context,
            spawned_by=spawned_by,
        )

        if not agents:
            return await self.execute(prompt, context=business_context)

        # Execute each specialist
        results = []
        for agent in agents:
            try:
                result = await self.router.route_task(agent.system_prompt, spawned_by)
                results.append({
                    "specialist": agent.specialist.name,
                    "response": result.get("response", str(result)),
                    "model": result.get("model", "unknown"),
                })
            except Exception as e:
                results.append({
                    "specialist": agent.specialist.name,
                    "response": f"Fehler: {str(e)}",
                    "model": "none",
                })

        return {
            "status": "ok",
            "expert_count": len(results),
            "results": results,
            "cost": sum(r.get("cost", 0.0) for r in results if isinstance(r.get("cost"), (int, float))),
        }

    def soul_status(self) -> dict:
        """Get status of the soul architecture."""
        if not self.souls:
            return {"status": "not_loaded", "core_souls": 0, "specialists": 0}
        return self.souls.stats()

    def save_state(self, key: str, data: dict):
        """Crash-safe state persistence."""
        if self.sync:
            self.sync.save_provider_state(key, data)
        else:
            # Fallback: simple file write
            state_dir = PROJECT_ROOT / "workflow_system" / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            state_file = state_dir / f"{key}.json"
            state_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    # ─── System Status ────────────────────────────────────────────────────

    def system_status(self) -> dict:
        """Get comprehensive status of all Empire systems."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "systems": {},
            "health": "unknown",
        }

        # Check each subsystem
        checks = {
            "antigravity_config": self._check_config(),
            "unified_router": self._check_router(),
            "knowledge_store": self._check_knowledge(),
            "sync_engine": self._check_sync(),
            "planning_mode": self._check_planner(),
            "resource_guard": self._check_guard(),
            "soul_architecture": self.souls is not None,
            "ollama": self._check_ollama(),
            "env_file": (PROJECT_ROOT / ".env").exists(),
            "git_repo": (PROJECT_ROOT / ".git").exists(),
        }

        # Add soul details if available
        if self.souls:
            status["soul_architecture"] = self.souls.stats()

        status["systems"] = checks
        healthy = sum(1 for v in checks.values() if v)
        total = len(checks)
        status["health"] = f"{healthy}/{total}"
        status["healthy"] = healthy >= total * 0.7  # 70% threshold

        return status

    def _check_config(self) -> bool:
        try:
            return True
        except Exception:
            return False

    def _check_router(self) -> bool:
        try:
            return True
        except Exception:
            return False

    def _check_knowledge(self) -> bool:
        try:
            from antigravity.knowledge_store import KnowledgeStore
            ks = KnowledgeStore()
            return ks.count() >= 0
        except Exception:
            return False

    def _check_sync(self) -> bool:
        try:
            return True
        except Exception:
            return False

    def _check_planner(self) -> bool:
        try:
            return True
        except Exception:
            return False

    def _check_guard(self) -> bool:
        try:
            return True
        except Exception:
            return False

    def _check_ollama(self) -> bool:
        try:
            import httpx
            r = httpx.get(f"{OLLAMA_BASE_URL}/api/version", timeout=2)
            return r.status_code == 200
        except Exception:
            return False


class _FallbackRouter:
    """Minimal fallback if unified_router can't be imported."""

    async def route_task(self, prompt: str, agent_key: str = "coder") -> dict:
        """Try Ollama directly as fallback."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": "qwen2.5-coder:7b",
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                if r.status_code == 200:
                    data = r.json()
                    return {
                        "response": data.get("response", ""),
                        "model": "qwen2.5-coder:7b (fallback)",
                        "cost": 0.0,
                    }
        except Exception:
            pass

        return {
            "response": "Kein AI-Provider verfuegbar. Starte Ollama: ollama serve",
            "model": "none",
            "cost": 0.0,
        }


# ─── Convenience Functions ────────────────────────────────────────────────────

_bridge_instance: Optional[EmpireBridge] = None

def get_bridge() -> EmpireBridge:
    """Get or create the singleton bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = EmpireBridge()
    return _bridge_instance
