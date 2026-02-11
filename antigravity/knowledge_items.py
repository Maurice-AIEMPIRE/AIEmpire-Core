"""
Knowledge Items (KI) System
============================
Persistent, distilled knowledge management across sessions.
Inspired by Google Antigravity's KI system.

Each KI has:
- metadata.json (summary, timestamps, source references, tags)
- artifacts/ directory (docs, code samples, implementation details)

Usage:
    ki = KnowledgeItems()
    ki.create("api-design", summary="REST API patterns for Empire API", tags=["api", "design"])
    ki.update("api-design", content="New endpoint pattern discovered...")
    results = ki.search("api patterns")
    ki.list_all()
"""

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


# ─── Configuration ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
KI_DIR = PROJECT_ROOT / "knowledge-items"

# Ensure directory exists
KI_DIR.mkdir(exist_ok=True)


@dataclass
class KnowledgeItem:
    """A single knowledge item with metadata and artifacts."""
    name: str
    summary: str
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    source_refs: list[str] = field(default_factory=list)
    confidence: float = 0.8
    status: str = "active"  # active, stale, archived
    access_count: int = 0
    last_accessed: str = ""

    def __post_init__(self):
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


class KnowledgeItems:
    """
    Persistent Knowledge Items manager.

    Protocol (from Antigravity):
    1. ALWAYS check KI summaries FIRST before any research
    2. Read relevant KI artifacts before diving into code
    3. Build upon existing knowledge (never redundant work)
    4. Verify KI info with original sources
    """

    def __init__(self, ki_dir: Optional[Path] = None):
        self.ki_dir = ki_dir or KI_DIR
        self.ki_dir.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        name: str,
        summary: str,
        tags: Optional[list[str]] = None,
        source_refs: Optional[list[str]] = None,
        confidence: float = 0.8,
    ) -> KnowledgeItem:
        """Create a new knowledge item."""
        ki = KnowledgeItem(
            name=name,
            summary=summary,
            tags=tags or [],
            source_refs=source_refs or [],
            confidence=confidence,
        )

        # Create directory structure
        ki_path = self.ki_dir / name
        ki_path.mkdir(parents=True, exist_ok=True)
        (ki_path / "artifacts").mkdir(exist_ok=True)

        # Save metadata
        self._save_metadata(ki)

        return ki

    def get(self, name: str) -> Optional[KnowledgeItem]:
        """Get a knowledge item by name."""
        meta_path = self.ki_dir / name / "metadata.json"
        if not meta_path.exists():
            return None

        with open(meta_path) as f:
            data = json.load(f)

        ki = KnowledgeItem(**data)
        ki.access_count += 1
        ki.last_accessed = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_metadata(ki)

        return ki

    def update(
        self,
        name: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        tags: Optional[list[str]] = None,
        artifact_name: Optional[str] = None,
        artifact_content: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> Optional[KnowledgeItem]:
        """Update an existing knowledge item."""
        ki = self.get(name)
        if not ki:
            return None

        ki.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")

        if summary:
            ki.summary = summary
        if tags:
            ki.tags = list(set(ki.tags + tags))
        if confidence is not None:
            ki.confidence = confidence

        # Add content to main notes
        if content:
            notes_path = self.ki_dir / name / "notes.md"
            timestamp = time.strftime("%Y-%m-%d %H:%M")
            with open(notes_path, "a") as f:
                f.write(f"\n\n## Update {timestamp}\n{content}\n")

        # Add artifact
        if artifact_name and artifact_content:
            artifact_path = self.ki_dir / name / "artifacts" / artifact_name
            with open(artifact_path, "w") as f:
                f.write(artifact_content)

        self._save_metadata(ki)
        return ki

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search knowledge items by text matching in name, summary, and tags."""
        results = []
        query_lower = query.lower()
        query_terms = query_lower.split()

        for ki_path in self.ki_dir.iterdir():
            if not ki_path.is_dir():
                continue

            meta_path = ki_path / "metadata.json"
            if not meta_path.exists():
                continue

            with open(meta_path) as f:
                data = json.load(f)

            # Score based on matches
            score = 0
            searchable = f"{data.get('name', '')} {data.get('summary', '')} {' '.join(data.get('tags', []))}".lower()

            for term in query_terms:
                if term in searchable:
                    score += 1
                if term in data.get("name", "").lower():
                    score += 2  # Name matches are worth more

            if score > 0:
                results.append({
                    "name": data["name"],
                    "summary": data.get("summary", ""),
                    "tags": data.get("tags", []),
                    "confidence": data.get("confidence", 0),
                    "score": score,
                    "updated_at": data.get("updated_at", ""),
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def list_all(self) -> list[dict[str, Any]]:
        """List all knowledge items with summaries."""
        items = []
        for ki_path in sorted(self.ki_dir.iterdir()):
            if not ki_path.is_dir():
                continue

            meta_path = ki_path / "metadata.json"
            if not meta_path.exists():
                continue

            with open(meta_path) as f:
                data = json.load(f)

            items.append({
                "name": data["name"],
                "summary": data.get("summary", ""),
                "tags": data.get("tags", []),
                "status": data.get("status", "active"),
                "confidence": data.get("confidence", 0),
                "updated_at": data.get("updated_at", ""),
                "access_count": data.get("access_count", 0),
            })

        return items

    def list_artifacts(self, name: str) -> list[str]:
        """List artifacts for a knowledge item."""
        artifacts_dir = self.ki_dir / name / "artifacts"
        if not artifacts_dir.exists():
            return []
        return [f.name for f in artifacts_dir.iterdir() if f.is_file()]

    def read_artifact(self, name: str, artifact_name: str) -> Optional[str]:
        """Read an artifact file."""
        path = self.ki_dir / name / "artifacts" / artifact_name
        if not path.exists():
            return None
        return path.read_text()

    def archive(self, name: str) -> bool:
        """Archive a knowledge item (mark as stale)."""
        ki = self.get(name)
        if not ki:
            return False
        ki.status = "archived"
        ki.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_metadata(ki)
        return True

    def status_report(self) -> str:
        """Get a formatted status report."""
        items = self.list_all()
        if not items:
            return "No knowledge items yet. Use ki.create() to add one."

        lines = [
            "=" * 60,
            "KNOWLEDGE ITEMS STATUS",
            "=" * 60,
        ]

        active = [i for i in items if i["status"] == "active"]
        archived = [i for i in items if i["status"] == "archived"]

        for item in active:
            tags = ", ".join(item["tags"][:3]) if item["tags"] else "no tags"
            conf = f"{item['confidence']:.0%}"
            lines.append(
                f"  [{conf}] {item['name']:30s} | {tags}"
            )
            lines.append(f"          {item['summary'][:60]}")

        if archived:
            lines.append(f"\n  Archived: {len(archived)} items")

        lines.append(f"\n  Total: {len(items)} items ({len(active)} active)")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _save_metadata(self, ki: KnowledgeItem) -> None:
        """Save KI metadata to disk."""
        meta_path = self.ki_dir / ki.name / "metadata.json"
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, "w") as f:
            json.dump(asdict(ki), f, indent=2)
