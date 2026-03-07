"""
Context Continuity Manager — Handles Claude Context Limits
===========================================================
When Claude reaches context limit, seamlessly switches to:
  1. Ollama (offline, free, unlimited context)
  2. Saved context snapshots
  3. Summarized conversation history
  4. Async task queue

Ensures work continues uninterrupted even when:
  - Claude context limit reached (200K tokens)
  - Network issues
  - API rate limits hit
  - Cost optimization needed

Pattern:
  Online Claude → 180K tokens used → Save snapshot
  → Switch to Ollama → Resume from snapshot
  → Ollama completes task → Optional: resume Claude
"""

import json
import time
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Dict, List

from antigravity.config import PROJECT_ROOT


class ContextProvider(str, Enum):
    """Current context provider."""
    CLAUDE = "claude"
    OLLAMA = "ollama"
    HYBRID = "hybrid"


@dataclass
class ContextSnapshot:
    """Snapshot of conversation for continuation."""
    snapshot_id: str
    timestamp: float
    provider: str
    conversation_summary: str
    key_decisions: List[str]
    pending_tasks: List[str]
    context_tokens_used: int
    total_session_tokens: int
    files_created: List[str]
    files_modified: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


class ContextContinuityManager:
    """
    Manages context usage and seamless continuation.

    Usage:
        manager = ContextContinuityManager()

        # Start with Claude
        await manager.set_provider(ContextProvider.CLAUDE)

        # Check context usage
        if manager.should_switch_provider(tokens_used=190000):
            await manager.switch_to_offline()

        # Save snapshot when needed
        manager.save_snapshot(
            conversation_summary="...",
            key_decisions=[...],
            pending_tasks=[...]
        )
    """

    SNAPSHOTS_DIR = Path(PROJECT_ROOT) / "antigravity" / "_context_snapshots"
    CONTINUITY_LOG = SNAPSHOTS_DIR / "continuity.jsonl"

    # Thresholds for switching providers
    CONTEXT_LIMITS = {
        ContextProvider.CLAUDE: 200000,  # 200K tokens
        ContextProvider.OLLAMA: 32000,   # 32K tokens
    }

    SWITCH_THRESHOLD = 0.90  # Switch to Ollama at 90% of limit

    def __init__(self):
        self.current_provider = ContextProvider.CLAUDE
        self.context_usage = 0
        self.session_start = time.time()
        self.session_id = self._generate_session_id()
        self.snapshots: List[ContextSnapshot] = []
        self.conversation_history: List[Dict[str, Any]] = []

        self._ensure_directories()
        self._load_history()

    def _ensure_directories(self) -> None:
        """Create snapshot directories."""
        self.SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return f"ctx_{int(time.time())}_{id(self)}"

    def _load_history(self) -> None:
        """Load conversation history from disk."""
        try:
            if self.CONTINUITY_LOG.exists():
                with open(self.CONTINUITY_LOG) as f:
                    for line in f:
                        data = json.loads(line)
                        self.snapshots.append(ContextSnapshot(**data))
        except Exception as e:
            print(f"⚠️  Error loading history: {e}")

    def add_tokens(self, count: int) -> None:
        """Track token usage."""
        self.context_usage += count

    def get_context_usage_percent(self) -> float:
        """Get current context usage as percentage."""
        limit = self.CONTEXT_LIMITS[self.current_provider]
        return (self.context_usage / limit) * 100

    def should_switch_provider(self, tokens_used: Optional[int] = None) -> bool:
        """Check if should switch to offline mode."""
        if tokens_used:
            self.context_usage = tokens_used

        self.CONTEXT_LIMITS[self.current_provider]
        usage_percent = self.get_context_usage_percent()

        if self.current_provider == ContextProvider.CLAUDE:
            # Switch to Ollama at 90% of Claude limit
            return usage_percent > (100 * self.SWITCH_THRESHOLD)

        return False

    async def switch_to_offline(self) -> Dict[str, Any]:
        """
        Switch from Claude to Ollama (offline).

        Saves snapshot and prepares Ollama context.
        """
        if self.current_provider == ContextProvider.OLLAMA:
            return {"status": "already offline", "provider": "ollama"}

        print("🔄 Switching to offline mode...")

        # Save snapshot
        snapshot = self.save_snapshot(
            conversation_summary=self._summarize_conversation(),
            key_decisions=self._extract_key_decisions(),
            pending_tasks=self._get_pending_tasks(),
        )

        # Update provider
        self.current_provider = ContextProvider.OLLAMA

        # Reset context usage (Ollama has its own limit)
        self.context_usage = 0

        print("✓ Switched to Ollama")
        print(f"  Snapshot: {snapshot.snapshot_id}")
        print(f"  Previous tokens: {snapshot.context_tokens_used}")

        return {
            "status": "switched",
            "provider": self.current_provider.value,
            "snapshot_id": snapshot.snapshot_id,
            "resume_context": self._get_resume_context(snapshot),
        }

    def save_snapshot(
        self,
        conversation_summary: str,
        key_decisions: List[str],
        pending_tasks: List[str],
    ) -> ContextSnapshot:
        """Save context snapshot for continuation."""
        snapshot = ContextSnapshot(
            snapshot_id=f"snap_{int(time.time())}",
            timestamp=time.time(),
            provider=self.current_provider.value,
            conversation_summary=conversation_summary,
            key_decisions=key_decisions,
            pending_tasks=pending_tasks,
            context_tokens_used=self.context_usage,
            total_session_tokens=self._count_total_tokens(),
            files_created=[],  # Would be populated from state
            files_modified=[],
        )

        self.snapshots.append(snapshot)

        # Save to disk
        try:
            with open(self.CONTINUITY_LOG, "a") as f:
                f.write(json.dumps(snapshot.to_dict()) + "\n")

            # Also save as individual file for easy access
            snapshot_file = (
                self.SNAPSHOTS_DIR / f"{snapshot.snapshot_id}.json"
            )
            with open(snapshot_file, "w") as f:
                json.dump(snapshot.to_dict(), f, indent=2)

        except Exception as e:
            print(f"❌ Error saving snapshot: {e}")

        return snapshot

    def get_resume_context(self, snapshot_id: str) -> str:
        """Get context string to resume from snapshot."""
        for snapshot in self.snapshots:
            if snapshot.snapshot_id == snapshot_id:
                return self._get_resume_context(snapshot)

        return ""

    def _get_resume_context(self, snapshot: ContextSnapshot) -> str:
        """Build resume context for Ollama."""
        return f"""## Context Resume from Claude Session

**Session ID:** {self.session_id}
**Snapshot ID:** {snapshot.snapshot_id}
**Provider:** {snapshot.provider} → {self.current_provider.value}
**Context Tokens Used:** {snapshot.context_tokens_used}

### Summary
{snapshot.conversation_summary}

### Key Decisions Made
{chr(10).join(f'- {d}' for d in snapshot.key_decisions)}

### Pending Tasks
{chr(10).join(f'- {t}' for t in snapshot.pending_tasks)}

### Resuming Now...
Continue with the same context and objectives. Use Ollama to complete pending tasks.
"""

    def _summarize_conversation(self, max_length: int = 1000) -> str:
        """Summarize conversation for snapshot."""
        # In real usage, would use Claude to summarize
        # For now, extract key parts
        if not self.conversation_history:
            return "No conversation history"

        summary = "Conversation history:\n"
        for msg in self.conversation_history[-5:]:  # Last 5 messages
            if "user" in msg:
                summary += f"- User: {msg['user'][:100]}...\n"

        return summary[:max_length]

    def _extract_key_decisions(self) -> List[str]:
        """Extract key decisions from conversation."""
        decisions = []

        # In real usage, would analyze messages for decisions
        # For now, return placeholder
        if self.conversation_history:
            decisions.append("System switch from Claude to Ollama")
            decisions.append("Continue with local model execution")

        return decisions

    def _get_pending_tasks(self) -> List[str]:
        """Get list of pending tasks."""
        # Would pull from task queue
        return ["Complete current workflow", "Test Ollama compatibility"]

    def _count_total_tokens(self) -> int:
        """Rough estimate of total tokens used."""
        # Count tokens from conversation history
        total = 0
        for msg in self.conversation_history:
            if "content" in msg:
                # Rough: 1 token ≈ 4 characters
                total += len(str(msg["content"])) // 4

        return total

    def add_conversation_turn(
        self,
        role: str,
        content: str,
        tokens: int,
    ) -> None:
        """Add conversation turn."""
        self.conversation_history.append({
            "timestamp": time.time(),
            "role": role,
            "content": content,
            "tokens": tokens,
        })
        self.add_tokens(tokens)

    def get_status(self) -> dict:
        """Get continuity manager status."""
        return {
            "session_id": self.session_id,
            "provider": self.current_provider.value,
            "context_usage": {
                "tokens_used": self.context_usage,
                "limit": self.CONTEXT_LIMITS[self.current_provider],
                "percent": self.get_context_usage_percent(),
                "should_switch": self.should_switch_provider(),
            },
            "snapshots": len(self.snapshots),
            "total_conversation_length": len(self.conversation_history),
        }


# ─── Integration with Antigravity ──────────────────────────────────────────

_continuity_manager: Optional[ContextContinuityManager] = None


def get_continuity_manager() -> ContextContinuityManager:
    """Get global continuity manager."""
    global _continuity_manager
    if _continuity_manager is None:
        _continuity_manager = ContextContinuityManager()
    return _continuity_manager


async def ensure_context_available(required_tokens: int = 10000) -> bool:
    """
    Ensure enough context is available.

    If not, switches to offline mode.
    """
    manager = get_continuity_manager()

    # Check if switching needed
    if manager.should_switch_provider():
        print(f"⚠️  Context limit approaching ({manager.get_context_usage_percent():.0f}%)")
        await manager.switch_to_offline()

    # Check if we have enough space for new request
    available = (
        manager.CONTEXT_LIMITS[manager.current_provider]
        - manager.context_usage
    )

    if available < required_tokens:
        print(
            f"⚠️  Not enough context available ({available} < {required_tokens})"
        )

        if manager.current_provider == ContextProvider.CLAUDE:
            await manager.switch_to_offline()
            return True

        # If already offline, task will be queued
        return False

    return True


if __name__ == "__main__":
    import asyncio

    async def test():
        print("=== CONTEXT CONTINUITY TEST ===\n")

        manager = ContextContinuityManager()

        # Simulate token usage
        print("Simulating token usage...\n")
        manager.add_tokens(50000)
        print(f"Used: {manager.context_usage} tokens")
        print(f"Usage: {manager.get_context_usage_percent():.1f}%\n")

        # Add some conversation
        manager.add_conversation_turn(
            role="user",
            content="Design a system for 100M users",
            tokens=100,
        )
        manager.add_conversation_turn(
            role="assistant",
            content="Here's a scalable architecture...",
            tokens=2000,
        )

        # Check if should switch
        print(f"Should switch: {manager.should_switch_provider()}\n")

        # Simulate approaching limit
        manager.context_usage = 180000
        print(f"Used: {manager.context_usage} tokens ({manager.get_context_usage_percent():.1f}%)")
        print(f"Should switch: {manager.should_switch_provider()}\n")

        # Test switch
        if manager.should_switch_provider():
            result = await manager.switch_to_offline()
            print(f"Switch result: {result}\n")

        # Show status
        status = manager.get_status()
        print(f"Status: {json.dumps(status, indent=2)}")

    asyncio.run(test())
