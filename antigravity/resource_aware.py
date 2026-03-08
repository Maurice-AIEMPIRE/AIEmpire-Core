"""
Resource-Aware Execution — Adaptive Model Selection
===================================================
Implements Google Antigravity pattern: select models and concurrency
based on current system resources.

Instead of crashing on overload:
  - Choose lighter models when RAM is constrained
  - Reduce concurrency as memory pressure increases
  - Defer non-critical tasks
  - Auto-scale back up as resources free

Resource Tiers:
  ABUNDANT  (>75% free): Use Gemini Pro + 5 concurrent agents
  HEALTHY   (50-75%): Use Gemini Flash + 3 concurrent agents
  TIGHT     (25-50%): Use Ollama only + 1 concurrent agent
  CRITICAL  (<25%): Pause all, emergency shutdown
"""

import json
import psutil
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any


# ─── Resource Tiers ─────────────────────────────────────────────────────────

class ResourceTier(str, Enum):
    """Current system resource availability."""
    ABUNDANT = "abundant"   # >75% free
    HEALTHY = "healthy"     # 50-75% free
    TIGHT = "tight"         # 25-50% free
    CRITICAL = "critical"   # <25% free


@dataclass
class ResourceProfile:
    """Resource requirements and limits for a task."""
    task_id: str
    task_type: str  # "reasoning", "code", "review", etc.
    required_memory_mb: int
    preferred_model: str
    fallback_models: List[str]
    max_concurrent: int = 1
    timeout_seconds: int = 300
    priority: int = 5  # 1-10, higher = more important


@dataclass
class SystemResources:
    """Current system resource state."""
    tier: ResourceTier
    free_memory_percent: float
    free_memory_mb: int
    total_memory_mb: int
    cpu_percent: float
    available_concurrency: int
    recommended_model: str
    throttled: bool = False


# ─── Resource Manager ──────────────────────────────────────────────────────

class ResourceAwareExecutor:
    """
    Manages task execution based on available resources.

    Pattern:
      1. Check system resources → determine tier
      2. For incoming task: select model based on tier
      3. Reduce concurrency if memory tight
      4. Queue deferred tasks for when resources improve
      5. Auto-scale back up when memory frees
    """

    # Concurrency limits per tier
    TIER_CONCURRENCY = {
        ResourceTier.ABUNDANT: 5,
        ResourceTier.HEALTHY: 3,
        ResourceTier.TIGHT: 1,
        ResourceTier.CRITICAL: 0,
    }

    # Model selection by tier
    TIER_MODELS = {
        ResourceTier.ABUNDANT: {
            "primary": "gemini-pro",
            "fallback": ["gemini-flash", "ollama"],
        },
        ResourceTier.HEALTHY: {
            "primary": "gemini-flash",
            "fallback": ["ollama"],
        },
        ResourceTier.TIGHT: {
            "primary": "ollama",
            "fallback": [],
        },
        ResourceTier.CRITICAL: {
            "primary": None,
            "fallback": [],
        },
    }

    # Memory requirements (MB)
    MODEL_MEMORY = {
        "gemini-pro": 0,  # Cloud, no local memory
        "gemini-flash": 0,
        "ollama": 600,  # phi:q4
        "moonshot": 0,
    }

    def __init__(self):
        self.current_tier = ResourceTier.HEALTHY
        self.deferred_tasks: List[ResourceProfile] = []
        self.active_tasks: Dict[str, ResourceProfile] = {}
        self.resource_history: List[SystemResources] = []
        self.throttle_threshold = 0.85  # Throttle at 85% RAM used

    def get_system_resources(self) -> SystemResources:
        """Snapshot current system resources."""
        try:
            # Memory
            mem = psutil.virtual_memory()
            free_percent = mem.available / mem.total * 100
            free_mb = mem.available // (1024 * 1024)
            total_mb = mem.total // (1024 * 1024)

            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Determine tier
            if free_percent > 75:
                tier = ResourceTier.ABUNDANT
            elif free_percent > 50:
                tier = ResourceTier.HEALTHY
            elif free_percent > 25:
                tier = ResourceTier.TIGHT
            else:
                tier = ResourceTier.CRITICAL

            # Get recommended model for tier
            recommended = self.TIER_MODELS[tier]["primary"]

            # Determine if throttled
            throttled = (mem.available / mem.total) < self.throttle_threshold

            resources = SystemResources(
                tier=tier,
                free_memory_percent=free_percent,
                free_memory_mb=free_mb,
                total_memory_mb=total_mb,
                cpu_percent=cpu_percent,
                available_concurrency=self.TIER_CONCURRENCY[tier],
                recommended_model=recommended,
                throttled=throttled,
            )

            self.current_tier = tier
            self.resource_history.append(resources)

            # Keep only last 1000 samples
            if len(self.resource_history) > 1000:
                self.resource_history = self.resource_history[-1000:]

            return resources

        except Exception as e:
            print(f"❌ Error getting resources: {e}")
            return SystemResources(
                tier=ResourceTier.HEALTHY,
                free_memory_percent=50.0,
                free_memory_mb=1024,
                total_memory_mb=2048,
                cpu_percent=50.0,
                available_concurrency=3,
                recommended_model="ollama",
            )

    def can_execute_task(self, profile: ResourceProfile) -> bool:
        """Check if task can be executed now."""
        resources = self.get_system_resources()

        if resources.tier == ResourceTier.CRITICAL:
            return False

        if len(self.active_tasks) >= resources.available_concurrency:
            return False

        # Check memory requirement
        required_mb = self.MODEL_MEMORY.get(profile.preferred_model, 0)
        if required_mb > resources.free_memory_mb:
            return False

        return True

    def select_model(self, profile: ResourceProfile) -> Optional[str]:
        """Select best model for task given current resources."""
        resources = self.get_system_resources()
        tier_models = self.TIER_MODELS[resources.tier]

        # If preferred model is available in this tier, use it
        preferred = profile.preferred_model
        if preferred in (tier_models.get("primary"), ) + tuple(
            tier_models.get("fallback", [])
        ):
            return preferred

        # Try fallbacks in order
        for model in tier_models.get("fallback", []):
            if model:
                return model

        # If nothing available, return primary (will be None if critical)
        return tier_models.get("primary")

    def execute(
        self,
        profile: ResourceProfile,
        execute_fn,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute task with resource awareness.

        Pattern:
          1. Check if can execute now
          2. If not, defer to queue
          3. Select appropriate model
          4. Execute with monitoring
          5. Move deferred tasks to active when resources free
        """
        if not self.can_execute_task(profile):
            # Defer task
            self.deferred_tasks.append(profile)
            print(f"📋 Task deferred: {profile.task_id} (will retry when resources free)")
            return {"deferred": True, "task_id": profile.task_id}

        try:
            # Mark as active
            self.active_tasks[profile.task_id] = profile

            # Select model
            model = self.select_model(profile)
            if model is None:
                return {"error": "No available models (system in CRITICAL state)"}

            print(f"🚀 Executing {profile.task_id} with {model}")

            # Execute
            result = execute_fn(*args, model=model, **kwargs)

            return result

        finally:
            # Remove from active
            if profile.task_id in self.active_tasks:
                del self.active_tasks[profile.task_id]

            # Try to execute deferred tasks
            self._process_deferred_queue()

    def _process_deferred_queue(self) -> None:
        """Process deferred tasks if resources available."""
        resources = self.get_system_resources()

        # Sort by priority (higher priority first)
        self.deferred_tasks.sort(key=lambda p: -p.priority)

        while self.deferred_tasks:
            if len(self.active_tasks) >= resources.available_concurrency:
                break

            task = self.deferred_tasks[0]

            if self.can_execute_task(task):
                self.deferred_tasks.pop(0)
                print(f"▶️  Resuming deferred task: {task.task_id}")
            else:
                break

    def throttle_if_needed(self) -> bool:
        """
        Check if system needs throttling.

        Returns: True if throttled
        """
        resources = self.get_system_resources()

        if resources.throttled:
            print(
                f"⚠️  THROTTLE: {resources.free_memory_percent:.1f}% "
                f"free, pausing new tasks"
            )
            return True

        return False

    def get_status(self) -> dict:
        """Get resource manager status."""
        resources = self.get_system_resources()

        return {
            "tier": resources.tier.value,
            "free_memory": {
                "percent": resources.free_memory_percent,
                "mb": resources.free_memory_mb,
                "total": resources.total_memory_mb,
            },
            "cpu": resources.cpu_percent,
            "active_tasks": len(self.active_tasks),
            "max_concurrency": resources.available_concurrency,
            "deferred_tasks": len(self.deferred_tasks),
            "recommended_model": resources.recommended_model,
            "throttled": resources.throttled,
        }


# ─── Global Executor ────────────────────────────────────────────────────────

_global_executor: Optional[ResourceAwareExecutor] = None


def get_executor() -> ResourceAwareExecutor:
    """Get or create global executor."""
    global _global_executor
    if _global_executor is None:
        _global_executor = ResourceAwareExecutor()
    return _global_executor


# ─── Health Check ──────────────────────────────────────────────────────────

def get_resource_status() -> dict:
    """Get current resource status."""
    executor = get_executor()
    return executor.get_status()


if __name__ == "__main__":
    # Test
    print("=== RESOURCE-AWARE EXECUTOR TEST ===\n")

    executor = ResourceAwareExecutor()

    # Get current resources
    resources = executor.get_system_resources()
    print(f"Tier: {resources.tier.value}")
    print(f"Free Memory: {resources.free_memory_percent:.1f}%")
    print(f"Available Concurrency: {resources.available_concurrency}\n")

    # Test task
    profile = ResourceProfile(
        task_id="test_001",
        task_type="reasoning",
        required_memory_mb=200,
        preferred_model="gemini-pro",
        fallback_models=["gemini-flash", "ollama"],
        max_concurrent=3,
    )

    can_run = executor.can_execute_task(profile)
    print(f"Can execute test_001: {can_run}")

    selected = executor.select_model(profile)
    print(f"Selected model: {selected}\n")

    # Status
    status = executor.get_status()
    print(f"Status: {json.dumps(status, indent=2)}")
