"""
Digital Memory System - Persistent knowledge graph for Maurice's vision.

This is the shared brain between Claude and Gemini.
Everything both systems learn about Maurice, his goals, preferences,
decisions, and patterns is stored here permanently.

Features:
- Categorized memory with confidence scores
- Memory reinforcement (repeated info = higher confidence)
- Memory decay (old unreinforced memories lose weight)
- Cross-referencing between memory entries
- Full-text search across all memories
- Export for both systems to consume
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional


STATE_DIR = Path(__file__).parent / "state"
MEMORY_FILE = STATE_DIR / "memory.json"
MEMORY_LOG = STATE_DIR / "memory_changelog.json"

CATEGORIES = {
    "vision": "Maurice's ultimate vision and goals",
    "preferences": "Personal preferences and working style",
    "decisions": "Key decisions made and reasoning",
    "patterns": "Recurring patterns in behavior and business",
    "strengths": "Identified strengths and unique advantages",
    "lessons": "Lessons learned from successes and failures",
    "relationships": "Key people, partners, and networks",
    "technical": "Technical preferences and stack decisions",
    "financial": "Financial targets, budgets, and strategies",
    "emotional": "Motivations, fears, and driving forces",
    "context": "Background information and life context",
    "rules": "Personal rules and principles",
}


class MemoryEntry:
    """A single memory with metadata."""

    def __init__(
        self,
        category: str,
        key: str,
        value: str,
        confidence: float = 0.7,
        source: str = "unknown",
    ):
        self.id = f"mem_{int(time.time() * 1000)}_{hash(key) % 10000}"
        self.category = category
        self.key = key
        self.value = value
        self.confidence = min(1.0, max(0.0, confidence))
        self.source = source
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.reinforced_count = 0
        self.tags = []
        self.related_ids = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "reinforced_count": self.reinforced_count,
            "tags": self.tags,
            "related_ids": self.related_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        entry = cls(
            category=data["category"],
            key=data["key"],
            value=data["value"],
            confidence=data.get("confidence", 0.7),
            source=data.get("source", "unknown"),
        )
        entry.id = data.get("id", entry.id)
        entry.created_at = data.get("created_at", entry.created_at)
        entry.updated_at = data.get("updated_at", entry.updated_at)
        entry.reinforced_count = data.get("reinforced_count", 0)
        entry.tags = data.get("tags", [])
        entry.related_ids = data.get("related_ids", [])
        return entry


class DigitalMemory:
    """
    Persistent knowledge graph.
    Shared between Claude and Gemini systems.
    """

    def __init__(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.entries: list[MemoryEntry] = []
        self._load()

    def _load(self):
        """Load memories from disk."""
        if MEMORY_FILE.exists():
            try:
                data = json.loads(MEMORY_FILE.read_text())
                self.entries = [MemoryEntry.from_dict(d) for d in data]
            except (json.JSONDecodeError, OSError):
                self.entries = []

    def _save(self):
        """Persist memories to disk."""
        data = [e.to_dict() for e in self.entries]
        MEMORY_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _log_change(self, action: str, entry: MemoryEntry, details: str = ""):
        """Log memory changes for audit trail."""
        log = []
        if MEMORY_LOG.exists():
            try:
                log = json.loads(MEMORY_LOG.read_text())
            except (json.JSONDecodeError, OSError):
                log = []

        log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "entry_id": entry.id,
            "category": entry.category,
            "key": entry.key,
            "details": details,
        })

        # Keep last 1000 log entries
        if len(log) > 1000:
            log = log[-1000:]

        MEMORY_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False))

    # -- Core Operations --

    def remember(
        self,
        category: str,
        key: str,
        value: str,
        confidence: float = 0.7,
        source: str = "unknown",
        tags: list[str] = None,
    ) -> MemoryEntry:
        """
        Store a memory. If a similar memory exists, reinforce it.
        """
        # Check for existing memory with same key in same category
        existing = self._find_by_key(category, key)

        if existing:
            # Reinforce existing memory
            existing.reinforced_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.05)
            existing.updated_at = datetime.now(timezone.utc).isoformat()

            # Update value if new info is more detailed
            if len(value) > len(existing.value):
                existing.value = value

            if tags:
                existing.tags = list(set(existing.tags + tags))

            self._log_change("reinforced", existing, f"count={existing.reinforced_count}")
            self._save()
            return existing

        # Create new memory
        entry = MemoryEntry(category, key, value, confidence, source)
        if tags:
            entry.tags = tags
        self.entries.append(entry)
        self._log_change("created", entry)
        self._save()
        return entry

    def recall(self, category: str = None, min_confidence: float = 0.0) -> list[dict]:
        """Retrieve memories, optionally filtered by category and confidence."""
        results = self.entries
        if category:
            results = [e for e in results if e.category == category]
        if min_confidence > 0:
            results = [e for e in results if e.confidence >= min_confidence]

        # Sort by confidence (highest first), then by recency
        results.sort(key=lambda e: (e.confidence, e.updated_at), reverse=True)
        return [e.to_dict() for e in results]

    def search(self, query: str) -> list[dict]:
        """Full-text search across all memories."""
        query_lower = query.lower()
        results = []
        for entry in self.entries:
            score = 0
            if query_lower in entry.key.lower():
                score += 3
            if query_lower in entry.value.lower():
                score += 2
            if any(query_lower in tag.lower() for tag in entry.tags):
                score += 1
            if score > 0:
                d = entry.to_dict()
                d["search_score"] = score
                results.append(d)

        results.sort(key=lambda x: x["search_score"], reverse=True)
        return results

    def forget(self, entry_id: str) -> bool:
        """Remove a specific memory."""
        for i, entry in enumerate(self.entries):
            if entry.id == entry_id:
                self._log_change("deleted", entry)
                self.entries.pop(i)
                self._save()
                return True
        return False

    def decay(self, rate: float = 0.95):
        """
        Apply memory decay. Reduces confidence of old, unreinforced memories.
        Memories reinforced recently are protected.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(weeks=1)).isoformat()
        for entry in self.entries:
            if entry.updated_at < cutoff and entry.reinforced_count < 3:
                entry.confidence *= rate
                if entry.confidence < 0.1:
                    entry.confidence = 0.1  # Never fully forget

        self._save()

    # -- Vision Profile --

    def get_vision_summary(self) -> dict:
        """Get a structured summary of everything we know."""
        summary = {}
        for cat in CATEGORIES:
            memories = self.recall(category=cat, min_confidence=0.3)
            if memories:
                summary[cat] = {
                    "count": len(memories),
                    "top_items": [
                        {"key": m["key"], "value": m["value"], "confidence": m["confidence"]}
                        for m in memories[:10]
                    ],
                }
        return summary

    def get_high_confidence(self, min_confidence: float = 0.8) -> list[dict]:
        """Get all high-confidence memories (things we're sure about)."""
        return self.recall(min_confidence=min_confidence)

    def get_gaps(self) -> list[str]:
        """Identify what we don't know yet (categories with few/no memories)."""
        gaps = []
        for cat, desc in CATEGORIES.items():
            memories = self.recall(category=cat)
            if len(memories) < 3:
                gaps.append(f"{cat}: {desc} (nur {len(memories)} Eintraege)")
        return gaps

    # -- Statistics --

    def stats(self) -> dict:
        """Memory statistics."""
        by_category = {}
        for cat in CATEGORIES:
            memories = [e for e in self.entries if e.category == cat]
            by_category[cat] = {
                "count": len(memories),
                "avg_confidence": (
                    sum(e.confidence for e in memories) / len(memories)
                    if memories else 0
                ),
            }

        return {
            "total_memories": len(self.entries),
            "by_category": by_category,
            "high_confidence": len([e for e in self.entries if e.confidence >= 0.8]),
            "low_confidence": len([e for e in self.entries if e.confidence < 0.3]),
            "gaps": self.get_gaps(),
            "oldest": min((e.created_at for e in self.entries), default="none"),
            "newest": max((e.created_at for e in self.entries), default="none"),
        }

    # -- Seed Knowledge --

    def seed_initial_knowledge(self):
        """Seed with known facts about Maurice from CLAUDE.md and context."""
        known_facts = [
            ("context", "name", "Maurice Pfeifer", 1.0),
            ("context", "age", "37 Jahre", 1.0),
            ("context", "profession", "Elektrotechnikmeister", 1.0),
            ("context", "expertise", "16 Jahre BMA-Expertise (Brandmeldeanlagen)", 1.0),
            ("financial", "revenue_target", "100 Mio EUR in 1-3 Jahren", 0.95),
            ("vision", "core_approach", "Alles automatisiert mit AI", 0.95),
            ("technical", "primary_stack", "Claude Code + GitHub + Ollama + Kimi + Redis + PostgreSQL + ChromaDB", 0.9),
            ("technical", "cost_strategy", "95% free (Ollama), 4% Kimi, 1% Claude", 0.9),
            ("strengths", "unique_niche", "BMA + AI Kombination - einzigartiger Vorteil", 0.9),
            ("financial", "current_revenue", "0 EUR - Channels muessen aktiviert werden", 1.0),
            ("patterns", "automation_first", "Automatisierung vor manueller Arbeit", 0.8),
            ("rules", "cost_conscious", "Minimale Kosten, maximaler Output", 0.85),
            ("vision", "system_architecture", "Dual-System: Claude (Mac) + Gemini (Cloud) Mirror", 0.9),
        ]

        for category, key, value, confidence in known_facts:
            self.remember(
                category=category,
                key=key,
                value=value,
                confidence=confidence,
                source="system_init",
            )

    # -- Helpers --

    def _find_by_key(self, category: str, key: str) -> Optional[MemoryEntry]:
        """Find memory by category and key."""
        for entry in self.entries:
            if entry.category == category and entry.key == key:
                return entry
        return None

    # -- Export --

    def export_for_system(self, system: str = "both") -> dict:
        """
        Export memory in a format optimized for system consumption.
        Can export for 'claude', 'gemini', or 'both'.
        """
        memories = self.recall()
        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "target_system": system,
            "total_memories": len(memories),
            "categories": {
                cat: [m for m in memories if m["category"] == cat]
                for cat in CATEGORIES
                if any(m["category"] == cat for m in memories)
            },
            "high_confidence_facts": self.get_high_confidence(0.8),
            "knowledge_gaps": self.get_gaps(),
        }
