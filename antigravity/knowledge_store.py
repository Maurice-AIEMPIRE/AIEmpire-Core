"""
Knowledge Store — Persistent Knowledge Items (KI)
===================================================
Inspired by Google Antigravity's Knowledge Items system.

Stores distilled knowledge snapshots from past conversations,
agent outputs, and system events. Enables:
  - Cross-session learning (agents remember past decisions)
  - Error pattern recognition (same bug won't happen twice)
  - Skill accumulation (agents get better over time)
  - Decision audit trail (why was X done?)

Knowledge Items (KI) are tagged, timestamped, and searchable.
Stored as JSONL for append-only durability (crash-safe).

Usage:
    from antigravity.knowledge_store import KnowledgeStore
    ks = KnowledgeStore()

    # Store knowledge
    ks.add("fix", "gemini_client env var fix",
           content="gemini_client.py must import from config.py, never os.getenv directly",
           tags=["bugfix", "config", "gemini"])

    # Search knowledge
    results = ks.search("gemini config")
    results = ks.search_by_tag("bugfix")

    # Get recent knowledge
    recent = ks.recent(limit=10)
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from antigravity.config import PROJECT_ROOT


# ─── Knowledge Item ───────────────────────────────────────────────────────────

@dataclass
class KnowledgeItem:
    """A single piece of distilled knowledge."""
    ki_type: str          # fix, decision, pattern, learning, error, optimization, architecture
    title: str            # Short descriptive title
    content: str          # Full knowledge content
    tags: list = field(default_factory=list)
    source: str = ""      # Where this knowledge came from (agent, human, auto-repair)
    confidence: float = 1.0  # 0.0 to 1.0
    references: list = field(default_factory=list)  # File paths, URLs, commit hashes
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ki_id: str = ""       # Auto-generated

    def __post_init__(self):
        if not self.ki_id:
            # Generate compact ID from timestamp
            self.ki_id = f"ki_{int(time.time() * 1000)}"

    def to_dict(self) -> dict:
        return {
            "id": self.ki_id,
            "type": self.ki_type,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "source": self.source,
            "confidence": self.confidence,
            "references": self.references,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeItem":
        return cls(
            ki_id=data.get("id", ""),
            ki_type=data.get("type", "learning"),
            title=data.get("title", ""),
            content=data.get("content", ""),
            tags=data.get("tags", []),
            source=data.get("source", ""),
            confidence=data.get("confidence", 1.0),
            references=data.get("references", []),
            created_at=data.get("created_at", ""),
        )

    def matches_query(self, query: str) -> bool:
        """Simple text matching for search."""
        q = query.lower()
        return (
            q in self.title.lower()
            or q in self.content.lower()
            or any(q in tag.lower() for tag in self.tags)
            or q in self.ki_type.lower()
        )


# ─── Knowledge Store ──────────────────────────────────────────────────────────

class KnowledgeStore:
    """
    Persistent, crash-safe knowledge storage.
    Uses JSONL (one JSON per line) for append-only writes.
    """

    STORE_DIR = Path(PROJECT_ROOT) / "antigravity" / "_knowledge"
    STORE_FILE = STORE_DIR / "knowledge_items.jsonl"
    INDEX_FILE = STORE_DIR / "knowledge_index.json"

    def __init__(self):
        self.STORE_DIR.mkdir(parents=True, exist_ok=True)
        self._items: list[KnowledgeItem] = []
        self._load()

    def _load(self):
        """Load all knowledge items from JSONL file."""
        self._items = []
        if not self.STORE_FILE.exists():
            return

        try:
            for line in self.STORE_FILE.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self._items.append(KnowledgeItem.from_dict(data))
                except json.JSONDecodeError:
                    continue  # Skip corrupt lines
        except Exception:
            pass

    def add(
        self,
        ki_type: str,
        title: str,
        content: str,
        tags: Optional[list] = None,
        source: str = "",
        confidence: float = 1.0,
        references: Optional[list] = None,
    ) -> KnowledgeItem:
        """Add a new knowledge item. Returns the created item."""
        ki = KnowledgeItem(
            ki_type=ki_type,
            title=title,
            content=content,
            tags=tags or [],
            source=source,
            confidence=confidence,
            references=references or [],
        )

        # Append to JSONL (crash-safe: one line at a time)
        try:
            with open(self.STORE_FILE, "a") as f:
                f.write(json.dumps(ki.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            raise IOError(f"Failed to write knowledge item: {e}")

        self._items.append(ki)
        self._update_index()
        return ki

    def search(self, query: str, limit: int = 20) -> list[KnowledgeItem]:
        """Search knowledge items by text query."""
        results = [ki for ki in self._items if ki.matches_query(query)]
        # Sort by relevance (newer = more relevant for now)
        results.sort(key=lambda ki: ki.created_at, reverse=True)
        return results[:limit]

    def search_by_tag(self, tag: str) -> list[KnowledgeItem]:
        """Find all items with a specific tag."""
        tag_lower = tag.lower()
        return [ki for ki in self._items if any(tag_lower == t.lower() for t in ki.tags)]

    def search_by_type(self, ki_type: str) -> list[KnowledgeItem]:
        """Find all items of a specific type."""
        return [ki for ki in self._items if ki.ki_type == ki_type]

    def recent(self, limit: int = 10) -> list[KnowledgeItem]:
        """Get most recent knowledge items."""
        sorted_items = sorted(self._items, key=lambda ki: ki.created_at, reverse=True)
        return sorted_items[:limit]

    def get(self, ki_id: str) -> Optional[KnowledgeItem]:
        """Get a specific knowledge item by ID."""
        for ki in self._items:
            if ki.ki_id == ki_id:
                return ki
        return None

    def count(self) -> int:
        """Total number of knowledge items."""
        return len(self._items)

    def stats(self) -> dict:
        """Get statistics about stored knowledge."""
        type_counts: dict[str, int] = {}
        tag_counts: dict[str, int] = {}
        source_counts: dict[str, int] = {}

        for ki in self._items:
            type_counts[ki.ki_type] = type_counts.get(ki.ki_type, 0) + 1
            for tag in ki.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            if ki.source:
                source_counts[ki.source] = source_counts.get(ki.source, 0) + 1

        return {
            "total_items": len(self._items),
            "by_type": type_counts,
            "top_tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
            "by_source": source_counts,
        }

    def export_for_agent(self, query: str = "", limit: int = 10) -> str:
        """
        Export relevant knowledge as a formatted string for agent context injection.
        This is the key integration point — agents get relevant past knowledge
        injected into their prompts automatically.
        """
        items = self.search(query, limit) if query else self.recent(limit)

        if not items:
            return "Keine relevanten Knowledge Items gefunden."

        lines = ["=== KNOWLEDGE CONTEXT (aus vorherigen Sessions) ===", ""]
        for ki in items:
            lines.append(f"[{ki.ki_type.upper()}] {ki.title}")
            lines.append(f"  {ki.content}")
            if ki.tags:
                lines.append(f"  Tags: {', '.join(ki.tags)}")
            lines.append("")

        return "\n".join(lines)

    def _update_index(self):
        """Update the search index file."""
        try:
            index = self.stats()
            index["last_updated"] = datetime.now().isoformat()
            # Atomic write
            tmp = self.INDEX_FILE.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(index, indent=2, ensure_ascii=False))
            tmp.rename(self.INDEX_FILE)
        except Exception:
            pass


# ─── Pre-seed with crash knowledge ────────────────────────────────────────────

def seed_initial_knowledge():
    """
    Seed the knowledge store with lessons learned from the system crash.
    Call this once to bootstrap the knowledge base.
    """
    ks = KnowledgeStore()

    # Only seed if empty
    if ks.count() > 0:
        return

    seeds = [
        {
            "type": "fix",
            "title": "gemini_client.py env var crash",
            "content": (
                "gemini_client.py darf NIEMALS os.getenv() direkt aufrufen. "
                "Alle Config MUSS durch antigravity.config importiert werden, "
                "weil config.py die .env Datei automatisch laedt. "
                "Direktes os.getenv() fuehrt nach Crash zu leeren Werten "
                "-> HTTP 400 'Invalid project resource name projects/'"
            ),
            "tags": ["bugfix", "config", "gemini", "crash", "critical"],
            "source": "crash-repair-2025",
            "references": ["antigravity/gemini_client.py", "antigravity/config.py"],
        },
        {
            "type": "pattern",
            "title": "Atomic Writes fuer crash-sichere Dateien",
            "content": (
                "Jeder Datei-Write der kritisch ist (State, Config, JSON) "
                "MUSS als Atomic Write implementiert werden: "
                "1) Schreibe in .tmp Datei, 2) os.rename() zum Ziel. "
                "os.rename() ist atomar auf POSIX. Kein Datenverlust bei Crash."
            ),
            "tags": ["pattern", "crash-safety", "atomic-write"],
            "source": "crash-repair-2025",
            "references": ["antigravity/sync_engine.py"],
        },
        {
            "type": "architecture",
            "title": "Cross-Agent Verification Prinzip",
            "content": (
                "Ein Agent darf NIEMALS seine eigene Arbeit bewerten. "
                "Verifikation muss immer durch einen ANDEREN Agent mit "
                "FRISCHEM Kontext erfolgen. Der Verifier sieht nur Aufgabe "
                "und Output, nicht den Prozess. Basiert auf Ryan Carson's Prinzip."
            ),
            "tags": ["architecture", "verification", "quality", "agents"],
            "source": "twitter-ryan-carson",
            "references": ["antigravity/cross_verify.py"],
        },
        {
            "type": "architecture",
            "title": "Resource Guard Predictive Throttling",
            "content": (
                "Reaktives Monitoring reicht NICHT. Resource Guard muss "
                "1) Preemptive Checks vor Model-Start (can_launch), "
                "2) Trend-basierte Vorhersage (steigt CPU/RAM?), "
                "3) Signal Handling (SIGTERM/SIGINT sauberes Shutdown), "
                "4) Crash Detection beim Start (Safe Mode). "
                "Ollama Models automatisch stoppen bei RAM-Krise."
            ),
            "tags": ["architecture", "resource-management", "crash-prevention"],
            "source": "crash-repair-2025",
            "references": ["workflow_system/resource_guard.py"],
        },
        {
            "type": "learning",
            "title": "Model Routing Strategie",
            "content": (
                "Ollama (lokal, kostenlos) fuer 95% der Tasks. "
                "Kimi K2.5 fuer komplexe Tasks (4%). "
                "Claude nur fuer kritische Entscheidungen (1%). "
                "NIEMALS ein grosses Model starten ohne vorher "
                "can_launch() vom Resource Guard abzufragen."
            ),
            "tags": ["cost", "routing", "models", "optimization"],
            "source": "system-design",
        },
        {
            "type": "pattern",
            "title": "Planning Mode Workflow",
            "content": (
                "Inspiriert von Google Antigravity: "
                "RESEARCH -> PLAN -> APPROVE -> EXECUTE -> VERIFY. "
                "Kein Code ohne Plan. Kein Execute ohne Approval. "
                "Changes klassifiziert als [NEW], [MODIFY], [DELETE], [CONFIG]. "
                "Implementation Plan als Markdown vor jeder Aenderung."
            ),
            "tags": ["workflow", "planning", "antigravity", "best-practice"],
            "source": "google-antigravity",
            "references": ["antigravity/planning_mode.py"],
        },
    ]

    for s in seeds:
        ks.add(
            ki_type=s["type"],
            title=s["title"],
            content=s["content"],
            tags=s.get("tags", []),
            source=s.get("source", ""),
            references=s.get("references", []),
        )

    return ks
