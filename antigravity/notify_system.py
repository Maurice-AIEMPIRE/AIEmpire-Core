"""
Notify/Communication System
=============================
Structured agent-to-user and agent-to-agent messaging.
Central notification hub for all AI Empire agents.

Inspired by Google Antigravity's notify_user pattern where
in-task communication goes through a structured notification system.

Usage:
    notify = NotifySystem()
    notify.send("fixer", "Fixed auth bug in empire_api/auth.py", priority="high")
    notify.send("architect", "New API design ready for review")
    unread = notify.get_unread()
    notify.broadcast("System maintenance in 5 minutes", source="system")
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).parent.parent
NOTIFY_DIR = PROJECT_ROOT / "antigravity" / "_notifications"
NOTIFY_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Notification:
    """A single notification message."""
    notif_id: str
    source: str  # Which agent/system sent this
    message: str
    priority: str = "normal"  # low, normal, high, critical
    category: str = "info"  # info, success, warning, error, task, review
    timestamp: str = ""
    read: bool = False
    target: str = ""  # Specific target agent/user, empty = broadcast
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")


class NotifySystem:
    """Central notification hub for agent communication."""

    def __init__(self, notify_dir: Optional[Path] = None):
        self.notify_dir = notify_dir or NOTIFY_DIR
        self.notify_dir.mkdir(parents=True, exist_ok=True)
        self._counter = self._load_counter()

    def send(
        self,
        source: str,
        message: str,
        priority: str = "normal",
        category: str = "info",
        target: str = "",
        metadata: Optional[dict] = None,
    ) -> Notification:
        """Send a notification."""
        self._counter += 1
        notif_id = f"N-{self._counter:04d}"

        notif = Notification(
            notif_id=notif_id,
            source=source,
            message=message,
            priority=priority,
            category=category,
            target=target,
            metadata=metadata or {},
        )

        self._save_notification(notif)
        self._save_counter()

        # Print critical/high notifications immediately
        if priority in ("critical", "high"):
            icon = {"critical": "🚨", "high": "⚠️"}.get(priority, "📢")
            print(f"{icon} [{source}] {message}")

        return notif

    def broadcast(
        self,
        message: str,
        source: str = "system",
        priority: str = "normal",
    ) -> Notification:
        """Send a broadcast notification to all agents."""
        return self.send(
            source=source,
            message=message,
            priority=priority,
            category="info",
            target="*",
        )

    def get_unread(self, target: Optional[str] = None) -> list[Notification]:
        """Get all unread notifications, optionally for a specific target."""
        notifications = self._load_all()
        unread = [n for n in notifications if not n.read]

        if target:
            unread = [
                n for n in unread
                if n.target in ("", "*", target)
            ]

        # Sort by priority then timestamp
        priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        unread.sort(key=lambda n: (priority_order.get(n.priority, 2), n.timestamp))

        return unread

    def get_recent(self, count: int = 20) -> list[Notification]:
        """Get most recent notifications."""
        notifications = self._load_all()
        notifications.sort(key=lambda n: n.timestamp, reverse=True)
        return notifications[:count]

    def mark_read(self, notif_id: str) -> bool:
        """Mark a notification as read."""
        notif = self._load_notification(notif_id)
        if not notif:
            return False
        notif.read = True
        self._save_notification(notif)
        return True

    def mark_all_read(self, target: Optional[str] = None) -> int:
        """Mark all notifications as read. Returns count marked."""
        notifications = self._load_all()
        count = 0
        for notif in notifications:
            if not notif.read:
                if target is None or notif.target in ("", "*", target):
                    notif.read = True
                    self._save_notification(notif)
                    count += 1
        return count

    def get_by_source(self, source: str, limit: int = 10) -> list[Notification]:
        """Get notifications from a specific source."""
        notifications = self._load_all()
        filtered = [n for n in notifications if n.source == source]
        filtered.sort(key=lambda n: n.timestamp, reverse=True)
        return filtered[:limit]

    def get_by_category(self, category: str, limit: int = 10) -> list[Notification]:
        """Get notifications by category."""
        notifications = self._load_all()
        filtered = [n for n in notifications if n.category == category]
        filtered.sort(key=lambda n: n.timestamp, reverse=True)
        return filtered[:limit]

    def cleanup(self, days: int = 7) -> int:
        """Remove old read notifications. Returns count removed."""
        cutoff = time.time() - (days * 86400)
        count = 0

        for path in self.notify_dir.glob("N-*.json"):
            with open(path) as f:
                data = json.load(f)

            if data.get("read"):
                try:
                    ts = time.mktime(time.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S"))
                    if ts < cutoff:
                        path.unlink()
                        count += 1
                except (ValueError, KeyError):
                    continue

        return count

    def status_report(self) -> str:
        """Get formatted notification status."""
        all_notifs = self._load_all()
        unread = [n for n in all_notifs if not n.read]

        lines = [
            "=" * 60,
            "NOTIFICATION SYSTEM STATUS",
            "=" * 60,
        ]

        if unread:
            lines.append(f"\n  Unread ({len(unread)}):")
            for n in unread[:10]:
                icon = {
                    "critical": "🚨", "high": "⚠️",
                    "normal": "📢", "low": "💬",
                }.get(n.priority, "📢")
                lines.append(
                    f"    {icon} [{n.source:10s}] {n.message[:50]}"
                )
        else:
            lines.append("  No unread notifications.")

        # Stats
        sources = {}
        for n in all_notifs:
            sources[n.source] = sources.get(n.source, 0) + 1

        if sources:
            lines.append("\n  Sources:")
            for src, count in sorted(sources.items(), key=lambda x: -x[1]):
                lines.append(f"    {src}: {count}")

        lines.append(f"\n  Total: {len(all_notifs)} | Unread: {len(unread)}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _load_all(self) -> list[Notification]:
        """Load all notifications from disk."""
        notifications = []
        for path in self.notify_dir.glob("N-*.json"):
            with open(path) as f:
                data = json.load(f)
            notifications.append(Notification(**data))
        return notifications

    def _load_notification(self, notif_id: str) -> Optional[Notification]:
        """Load a single notification."""
        path = self.notify_dir / f"{notif_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return Notification(**data)

    def _save_notification(self, notif: Notification) -> None:
        """Save a notification to disk."""
        path = self.notify_dir / f"{notif.notif_id}.json"
        with open(path, "w") as f:
            json.dump(asdict(notif), f, indent=2)

    def _load_counter(self) -> int:
        """Load the notification counter."""
        counter_path = self.notify_dir / "_counter.json"
        if counter_path.exists():
            with open(counter_path) as f:
                return json.load(f).get("counter", 0)
        return 0

    def _save_counter(self) -> None:
        """Save the notification counter."""
        counter_path = self.notify_dir / "_counter.json"
        with open(counter_path, "w") as f:
            json.dump({"counter": self._counter}, f)
