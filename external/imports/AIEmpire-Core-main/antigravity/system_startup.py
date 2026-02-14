#!/usr/bin/env python3
"""
System Startup & Recovery Manager
==================================
Comprehensive startup sequence with:
  1. Crash detection & recovery
  2. Resource verification
  3. Service health checks
  4. Graceful degradation
  5. Ready state confirmation

Run before starting main system:
  python antigravity/system_startup.py
"""

import json
import os
import sys
import time
from pathlib import Path

from antigravity.state_recovery import check_recovery_status
from antigravity.resource_aware import get_executor
from antigravity.unified_router import UnifiedRouter
from antigravity.config import PROJECT_ROOT


# ─── Startup Phases ────────────────────────────────────────────────────────

class SystemStartup:
    """Multi-phase startup with comprehensive checks."""

    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
        self.startup_time = time.time()

    def run_all_checks(self) -> bool:
        """Run complete startup sequence."""
        print("\n" + "=" * 60)
        print("AIEmpire-Core System Startup")
        print("=" * 60 + "\n")

        phases = [
            ("Crash Recovery", self.check_crash_recovery),
            ("Resource Verification", self.check_resources),
            ("Provider Health", self.check_providers),
            ("State Integrity", self.check_state_integrity),
            ("Agent Configuration", self.check_agent_config),
            ("Knowledge Store", self.check_knowledge_store),
            ("Environment", self.check_environment),
        ]

        for phase_name, phase_fn in phases:
            print(f"\n▶️  {phase_name}...")
            try:
                phase_fn()
            except Exception as e:
                self.fail(f"Fatal error in {phase_name}: {e}")
                return False

        return self.print_summary()

    # ─── Phase Implementations ──────────────────────────────────────────────

    def check_crash_recovery(self) -> None:
        """Detect and recover from crashes."""
        recovery_status = check_recovery_status()

        if recovery_status["last_crash"]:
            self.warn(f"Last crash detected {recovery_status['recovery_count']} recoveries")

        if recovery_status["recoverable_tasks"] > 0:
            self.warn(
                f"Found {recovery_status['recoverable_tasks']} recoverable tasks"
            )
            print("  → Run: python antigravity/state_recovery.py --recover")

        self.pass_check(
            f"Recovery system ready ({recovery_status['total_checkpoints']} checkpoints)"
        )

    def check_resources(self) -> None:
        """Verify system resources are adequate."""
        executor = get_executor()
        resources = executor.get_system_resources()

        status_icons = {
            "abundant": "🟢",
            "healthy": "🟢",
            "tight": "🟡",
            "critical": "🔴",
        }

        icon = status_icons.get(resources.tier.value, "❓")

        print(
            f"  {icon} Tier: {resources.tier.value.upper()} "
            f"({resources.free_memory_percent:.1f}% free)"
        )

        if resources.tier.value == "critical":
            self.fail("System in CRITICAL resource state, refusing startup")
            print("  → Free up memory and try again")
            return

        if resources.tier.value == "tight":
            self.warn("System in TIGHT resource state, limiting concurrency")

        self.pass_check(
            f"Resources OK: {resources.free_memory_mb}MB free, "
            f"max {resources.available_concurrency} concurrent agents"
        )

    def check_providers(self) -> None:
        """Check AI provider availability."""
        router = UnifiedRouter()

        print("  Checking providers...")

        # Gemini
        gemini = router.providers["gemini"]
        if gemini.available:
            self.pass_check("Gemini API: ✓ AVAILABLE")
        else:
            self.warn("Gemini API: Unavailable (will use Ollama fallback)")

        # Ollama
        try:
            from antigravity.ollama_client import OllamaClient

            ollama = OllamaClient()
            models = ollama.list_models()
            if models:
                self.pass_check(f"Ollama: ✓ AVAILABLE ({len(models)} models)")
            else:
                self.warn(
                    "Ollama: No models loaded (start with: ollama serve)"
                )
        except Exception as e:
            self.warn(f"Ollama: {e} (Optional fallback provider)")

    def check_state_integrity(self) -> None:
        """Verify knowledge store and state files."""
        state_dir = Path(PROJECT_ROOT) / "antigravity" / "_state"

        if state_dir.exists():
            checkpoint_count = len(list(state_dir.rglob("*.json")))
            self.pass_check(f"State directory: {checkpoint_count} checkpoints")
        else:
            state_dir.mkdir(parents=True, exist_ok=True)
            self.warn("State directory created (first startup)")

    def check_agent_config(self) -> None:
        """Verify agent configuration."""
        from antigravity.config import AGENTS

        if not AGENTS:
            self.fail("No agents configured")
            return

        agent_count = len(AGENTS)
        print(f"  Found {agent_count} agents:")

        for agent_key, config in AGENTS.items():
            role = getattr(config, 'role', 'unknown')
            print(f"    - {agent_key} ({role}): {config.model}")

        self.pass_check(f"Agent configuration: {agent_count} agents ready")

    def check_knowledge_store(self) -> None:
        """Verify knowledge store."""
        try:
            from antigravity.knowledge_store import KnowledgeStore

            ks = KnowledgeStore()
            # Check if we can access the store
            if hasattr(ks, 'list_all'):
                item_count = len(ks.list_all())
            else:
                item_count = 0
            self.pass_check(f"Knowledge store: Ready ({item_count} items)")
        except Exception as e:
            self.warn(f"Knowledge store: {e} (will initialize on first use)")

    def check_environment(self) -> None:
        """Verify environment variables."""
        required_vars = [
            ("OLLAMA_BASE_URL", "Ollama"),
            ("GEMINI_API_KEY", "Gemini API (optional)"),
        ]

        missing = []
        for var, desc in required_vars:
            if not os.getenv(var):
                if "optional" not in desc:
                    missing.append(var)
                else:
                    self.warn(f"{desc}: Not set (will use fallback)")

        if missing:
            self.fail(f"Missing env vars: {', '.join(missing)}")
        else:
            self.pass_check("Environment variables: All required vars set")

    # ─── Utility Methods ────────────────────────────────────────────────────

    def pass_check(self, message: str) -> None:
        """Record passing check."""
        self.checks_passed.append(message)
        print(f"  ✓ {message}")

    def fail(self, message: str) -> None:
        """Record failing check."""
        self.checks_failed.append(message)
        print(f"  ✗ {message}")

    def warn(self, message: str) -> None:
        """Record warning."""
        self.warnings.append(message)
        print(f"  ⚠️  {message}")

    def print_summary(self) -> bool:
        """Print startup summary and return success."""
        duration = time.time() - self.startup_time

        print("\n" + "=" * 60)
        print("STARTUP SUMMARY")
        print("=" * 60)

        print(f"\n✓ Passed: {len(self.checks_passed)}")
        print(f"✗ Failed: {len(self.checks_failed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"⏱️  Duration: {duration:.1f}s")

        if self.checks_failed:
            print("\n❌ STARTUP FAILED")
            for msg in self.checks_failed:
                print(f"  - {msg}")
            return False

        if self.warnings:
            print("\n⚠️  STARTUP OK (with warnings)")
            for msg in self.warnings:
                print(f"  - {msg}")
            print("\nSystem is operational but check warnings above.")
        else:
            print("\n✅ STARTUP SUCCESSFUL")
            print("\nSystem is ready to run:")
            print("  python -m antigravity.swarm_run")
            print("  python workflow_system/empire.py workflow")

        # Save startup report
        self.save_report()

        return True

    def save_report(self) -> None:
        """Save startup report to file."""
        report = {
            "timestamp": time.time(),
            "duration_seconds": time.time() - self.startup_time,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
            "success": len(self.checks_failed) == 0,
        }

        report_file = Path(PROJECT_ROOT) / ".startup_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nReport saved: {report_file}")


# ─── Main Entry Point ──────────────────────────────────────────────────────


def main():
    """Run startup."""
    startup = SystemStartup()
    success = startup.run_all_checks()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
