"""
Memory Core - Persistent Memory Across Agents.

Provides a shared memory layer that agents can read/write to,
enabling knowledge transfer and context accumulation.

Storage hierarchy:
    1. Hot memory  - In-process dict (fastest, lost on restart)
    2. Warm memory - JSON files on disk (persistent, local)
    3. Cold memory - Future: Redis/PostgreSQL for distributed access

Usage:
    memory = MemoryCore()
    memory.store("legal", "timeline_v1", {"events": [...]})
    data = memory.recall("legal", "timeline_v1")
    results = memory.search("legal", query="contract dispute")
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

MEMORY_DIR = Path(__file__).parent.parent / "workflow-system" / "state" / "memory"


class MemoryCore:
    """Shared persistent memory for all agents."""

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_dir = memory_dir or MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._hot: Dict[str, Dict[str, Any]] = {}
        self._access_log: List[Dict] = []

    def store(self, namespace: str, key: str, value: Any, ttl_hours: Optional[float] = None) -> None:
        """Store a value in both hot and warm memory."""
        entry = {
            "key": key,
            "value": value,
            "stored_at": datetime.now().isoformat(),
            "expires_at": (
                datetime.fromtimestamp(time.time() + ttl_hours * 3600).isoformat()
                if ttl_hours else None
            ),
        }

        # Hot memory
        self._hot.setdefault(namespace, {})[key] = entry

        # Warm memory (disk)
        ns_dir = self.memory_dir / namespace
        ns_dir.mkdir(parents=True, exist_ok=True)
        file_path = ns_dir / f"{key}.json"
        file_path.write_text(json.dumps(entry, indent=2, ensure_ascii=False))

        self._log_access("store", namespace, key)

    def recall(self, namespace: str, key: str) -> Optional[Any]:
        """Retrieve a value. Checks hot memory first, then disk."""
        # Hot memory
        if namespace in self._hot and key in self._hot[namespace]:
            entry = self._hot[namespace][key]
            if not self._is_expired(entry):
                self._log_access("recall_hot", namespace, key)
                return entry["value"]

        # Warm memory (disk)
        file_path = self.memory_dir / namespace / f"{key}.json"
        if file_path.exists():
            try:
                entry = json.loads(file_path.read_text())
                if not self._is_expired(entry):
                    # Promote to hot
                    self._hot.setdefault(namespace, {})[key] = entry
                    self._log_access("recall_warm", namespace, key)
                    return entry["value"]
            except (json.JSONDecodeError, KeyError):
                pass

        self._log_access("recall_miss", namespace, key)
        return None

    def search(self, namespace: str, query: str) -> List[Dict]:
        """Search within a namespace for keys/values matching query."""
        results = []
        ns_dir = self.memory_dir / namespace
        if not ns_dir.exists():
            return results

        query_lower = query.lower()
        for file_path in ns_dir.glob("*.json"):
            try:
                entry = json.loads(file_path.read_text())
                key = entry.get("key", file_path.stem)
                value_str = json.dumps(entry.get("value", ""))
                if query_lower in key.lower() or query_lower in value_str.lower():
                    results.append({
                        "key": key,
                        "value": entry.get("value"),
                        "stored_at": entry.get("stored_at"),
                    })
            except (json.JSONDecodeError, KeyError):
                continue

        return results

    def list_namespaces(self) -> List[str]:
        """List all available namespaces."""
        if not self.memory_dir.exists():
            return []
        return [d.name for d in self.memory_dir.iterdir() if d.is_dir()]

    def list_keys(self, namespace: str) -> List[str]:
        """List all keys in a namespace."""
        ns_dir = self.memory_dir / namespace
        if not ns_dir.exists():
            return []
        return [f.stem for f in ns_dir.glob("*.json")]

    def delete(self, namespace: str, key: str) -> bool:
        """Delete a specific memory entry."""
        deleted = False

        # Hot memory
        if namespace in self._hot and key in self._hot[namespace]:
            del self._hot[namespace][key]
            deleted = True

        # Warm memory
        file_path = self.memory_dir / namespace / f"{key}.json"
        if file_path.exists():
            file_path.unlink()
            deleted = True

        return deleted

    def get_stats(self) -> Dict:
        """Return memory statistics."""
        namespaces = self.list_namespaces()
        total_keys = sum(len(self.list_keys(ns)) for ns in namespaces)
        return {
            "namespaces": len(namespaces),
            "total_keys": total_keys,
            "hot_entries": sum(len(v) for v in self._hot.values()),
            "access_log_size": len(self._access_log),
            "memory_dir": str(self.memory_dir),
        }

    def _is_expired(self, entry: Dict) -> bool:
        """Check if a memory entry has expired."""
        expires = entry.get("expires_at")
        if not expires:
            return False
        try:
            return datetime.fromisoformat(expires) < datetime.now()
        except (ValueError, TypeError):
            return False

    def _log_access(self, operation: str, namespace: str, key: str) -> None:
        """Log memory access for debugging."""
        self._access_log.append({
            "op": operation,
            "ns": namespace,
            "key": key,
            "ts": datetime.now().isoformat(),
        })
        # Keep only last 200 entries
        if len(self._access_log) > 200:
            self._access_log = self._access_log[-200:]
