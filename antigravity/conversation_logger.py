"""
Conversation Logger
====================
Persistent conversation logging for agent interactions.
Stores raw conversations and distilled summaries for context persistence.

Inspired by Google Antigravity's dual memory system:
1. Raw conversation logs (complete history)
2. Distilled summaries (curated knowledge)

Usage:
    logger = ConversationLogger()
    conv = logger.start_conversation("api-fix-session")
    logger.log_message(conv, "user", "Fix the auth bug in empire_api")
    logger.log_message(conv, "assistant", "Found the issue in auth.py...")
    logger.end_conversation(conv, summary="Fixed JWT validation bug")

    # Search past conversations
    results = logger.search("auth bug")
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "antigravity" / "_conversations"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Message:
    """A single conversation message."""
    role: str  # user, assistant, system, agent
    content: str
    timestamp: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")


@dataclass
class Conversation:
    """A conversation session with messages and metadata."""
    conv_id: str
    title: str = ""
    messages: list[dict] = field(default_factory=list)
    started_at: str = ""
    ended_at: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    agent: str = ""  # Which agent ran this conversation
    status: str = "active"  # active, completed, archived
    token_count: int = 0

    def __post_init__(self):
        if not self.started_at:
            self.started_at = time.strftime("%Y-%m-%dT%H:%M:%S")


class ConversationLogger:
    """Persistent conversation storage and search."""

    def __init__(self, logs_dir: Optional[Path] = None):
        self.logs_dir = logs_dir or LOGS_DIR
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def start_conversation(
        self,
        conv_id: str,
        title: str = "",
        agent: str = "",
        tags: Optional[list[str]] = None,
    ) -> Conversation:
        """Start a new conversation session."""
        conv = Conversation(
            conv_id=conv_id,
            title=title or conv_id,
            agent=agent,
            tags=tags or [],
        )
        self._save_conversation(conv)
        return conv

    def log_message(
        self,
        conv_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Log a message to a conversation."""
        conv = self.get_conversation(conv_id)
        if not conv:
            conv = self.start_conversation(conv_id)

        msg = Message(role=role, content=content, metadata=metadata or {})
        conv.messages.append(asdict(msg))
        conv.token_count += len(content.split())  # Rough token estimate
        self._save_conversation(conv)

    def end_conversation(
        self,
        conv_id: str,
        summary: str = "",
    ) -> Optional[Conversation]:
        """End a conversation and save summary."""
        conv = self.get_conversation(conv_id)
        if not conv:
            return None

        conv.ended_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        conv.status = "completed"
        if summary:
            conv.summary = summary

        self._save_conversation(conv)

        # Also save distilled summary to separate index
        self._update_summary_index(conv)

        return conv

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        """Load a conversation by ID."""
        path = self.logs_dir / f"{conv_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return Conversation(**data)

    def get_recent_messages(
        self,
        conv_id: str,
        count: int = 10,
    ) -> list[dict]:
        """Get the most recent messages from a conversation."""
        conv = self.get_conversation(conv_id)
        if not conv:
            return []
        return conv.messages[-count:]

    def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search across all conversations."""
        results = []
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        for path in self.logs_dir.glob("*.json"):
            if path.name == "summary_index.json":
                continue

            with open(path) as f:
                data = json.load(f)

            # Search in title, summary, and tags
            searchable = f"{data.get('title', '')} {data.get('summary', '')} {' '.join(data.get('tags', []))}".lower()

            score = 0
            for term in query_terms:
                if term in searchable:
                    score += 2

            # Search in messages
            for msg in data.get("messages", []):
                content = msg.get("content", "").lower()
                for term in query_terms:
                    if term in content:
                        score += 1
                        break  # Only count once per message

            if score > 0:
                results.append({
                    "conv_id": data.get("conv_id", path.stem),
                    "title": data.get("title", ""),
                    "summary": data.get("summary", ""),
                    "agent": data.get("agent", ""),
                    "message_count": len(data.get("messages", [])),
                    "started_at": data.get("started_at", ""),
                    "score": score,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]

    def list_conversations(
        self,
        status: Optional[str] = None,
        agent: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List conversations, optionally filtered."""
        conversations = []

        for path in sorted(self.logs_dir.glob("*.json"), reverse=True):
            if path.name == "summary_index.json":
                continue

            with open(path) as f:
                data = json.load(f)

            if status and data.get("status") != status:
                continue
            if agent and data.get("agent") != agent:
                continue

            conversations.append({
                "conv_id": data.get("conv_id", path.stem),
                "title": data.get("title", ""),
                "status": data.get("status", "active"),
                "agent": data.get("agent", ""),
                "messages": len(data.get("messages", [])),
                "started_at": data.get("started_at", ""),
                "summary": data.get("summary", "")[:100],
            })

            if len(conversations) >= limit:
                break

        return conversations

    def get_summaries(self) -> list[dict[str, str]]:
        """Get all conversation summaries (distilled knowledge)."""
        index_path = self.logs_dir / "summary_index.json"
        if not index_path.exists():
            return []
        with open(index_path) as f:
            return json.load(f)

    def archive(self, conv_id: str) -> bool:
        """Archive a conversation."""
        conv = self.get_conversation(conv_id)
        if not conv:
            return False
        conv.status = "archived"
        self._save_conversation(conv)
        return True

    def status_report(self) -> str:
        """Get formatted conversation log status."""
        conversations = self.list_conversations(limit=100)
        if not conversations:
            return "No conversations logged yet."

        active = sum(1 for c in conversations if c["status"] == "active")
        completed = sum(1 for c in conversations if c["status"] == "completed")
        total_msgs = sum(c["messages"] for c in conversations)

        lines = [
            "=" * 60,
            "CONVERSATION LOGGER STATUS",
            "=" * 60,
        ]

        for c in conversations[:10]:
            status_icon = {"active": "🔵", "completed": "✅", "archived": "📦"}.get(c["status"], "?")
            lines.append(
                f"  {status_icon} {c['conv_id']:30s} | "
                f"{c['messages']:3d} msgs | {c['agent'] or '?':10s}"
            )

        if len(conversations) > 10:
            lines.append(f"  ... and {len(conversations) - 10} more")

        lines.append(f"\n  Active: {active} | Completed: {completed} | Messages: {total_msgs}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _save_conversation(self, conv: Conversation) -> None:
        """Save conversation to disk."""
        path = self.logs_dir / f"{conv.conv_id}.json"
        with open(path, "w") as f:
            json.dump(asdict(conv), f, indent=2)

    def _update_summary_index(self, conv: Conversation) -> None:
        """Update the distilled summary index."""
        index_path = self.logs_dir / "summary_index.json"
        summaries = []
        if index_path.exists():
            with open(index_path) as f:
                summaries = json.load(f)

        # Update or add
        existing = [s for s in summaries if s.get("conv_id") == conv.conv_id]
        entry = {
            "conv_id": conv.conv_id,
            "title": conv.title,
            "summary": conv.summary,
            "tags": conv.tags,
            "agent": conv.agent,
            "ended_at": conv.ended_at,
        }

        if existing:
            idx = summaries.index(existing[0])
            summaries[idx] = entry
        else:
            summaries.append(entry)

        with open(index_path, "w") as f:
            json.dump(summaries, f, indent=2)
