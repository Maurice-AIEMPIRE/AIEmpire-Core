"""
Mirror Sync Engine - Bidirectional synchronization between Claude (Mac) and Gemini (Cloud).

Architecture:
  Mac (Claude) <--git--> GitHub <--sync--> Gemini Mirror

  Both systems push improvements, patterns, and insights.
  The sync engine merges them, resolves conflicts, and distributes.

Sync Artifacts:
  - improvements: Code/system improvements discovered by either side
  - patterns: Business/automation patterns recognized
  - insights: Strategic intelligence from analysis
  - vision_answers: Maurice's answers to vision discovery questions
  - memory_updates: Knowledge graph changes
  - evolution_logs: How each system evolved
"""

import os
import json
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from gemini_client import GeminiClient


STATE_DIR = Path(__file__).parent / "state"
SYNC_LOG = STATE_DIR / "sync_log.json"
OUTBOX_CLAUDE = STATE_DIR / "outbox_claude.json"   # Claude -> Gemini
OUTBOX_GEMINI = STATE_DIR / "outbox_gemini.json"   # Gemini -> Claude
MERGED_STATE = STATE_DIR / "merged_state.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:12]


class SyncArtifact:
    """A single piece of knowledge/improvement being synced."""

    def __init__(
        self,
        artifact_type: str,
        content: dict,
        source: str,
        priority: int = 5,
    ):
        self.id = _hash(json.dumps(content, sort_keys=True) + _now())
        self.artifact_type = artifact_type
        self.content = content
        self.source = source  # "claude" or "gemini"
        self.priority = priority  # 1-10
        self.created_at = _now()
        self.synced = False
        self.synced_at = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.artifact_type,
            "content": self.content,
            "source": self.source,
            "priority": self.priority,
            "created_at": self.created_at,
            "synced": self.synced,
            "synced_at": self.synced_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SyncArtifact":
        art = cls(
            artifact_type=data["type"],
            content=data["content"],
            source=data["source"],
            priority=data.get("priority", 5),
        )
        art.id = data["id"]
        art.created_at = data["created_at"]
        art.synced = data.get("synced", False)
        art.synced_at = data.get("synced_at")
        return art


class MirrorSyncEngine:
    """
    Bidirectional sync engine.

    Flow:
    1. Each system writes to its outbox
    2. Sync engine reads both outboxes
    3. Gemini merges & enhances artifacts
    4. Merged state is written for both systems to read
    5. Both systems pull from merged state
    """

    def __init__(self, gemini: GeminiClient = None):
        self.gemini = gemini
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.sync_count = 0

    # -- Outbox Operations --

    def push_to_claude_outbox(self, artifact: SyncArtifact):
        """Push an artifact from Gemini to Claude's inbox."""
        self._append_to_file(OUTBOX_GEMINI, artifact.to_dict())

    def push_to_gemini_outbox(self, artifact: SyncArtifact):
        """Push an artifact from Claude to Gemini's inbox."""
        self._append_to_file(OUTBOX_CLAUDE, artifact.to_dict())

    def push_artifact(self, artifact_type: str, content: dict, source: str, priority: int = 5):
        """Convenience: create and push an artifact to the appropriate outbox."""
        art = SyncArtifact(artifact_type, content, source, priority)
        if source == "claude":
            self.push_to_gemini_outbox(art)
        else:
            self.push_to_claude_outbox(art)
        return art

    # -- Sync Operations --

    async def sync(self) -> dict:
        """
        Run a full sync cycle:
        1. Read both outboxes
        2. Merge artifacts
        3. Enhance with Gemini (find connections, insights)
        4. Write merged state
        5. Clear synced items from outboxes
        """
        claude_artifacts = self._read_file(OUTBOX_CLAUDE)
        gemini_artifacts = self._read_file(OUTBOX_GEMINI)

        unsynced_claude = [a for a in claude_artifacts if not a.get("synced")]
        unsynced_gemini = [a for a in gemini_artifacts if not a.get("synced")]

        if not unsynced_claude and not unsynced_gemini:
            return {
                "status": "no_changes",
                "claude_pending": 0,
                "gemini_pending": 0,
                "timestamp": _now(),
            }

        # Merge all unsynced artifacts
        all_artifacts = unsynced_claude + unsynced_gemini

        # Use Gemini to find connections and enhance
        enhanced = await self._enhance_artifacts(all_artifacts)

        # Mark as synced
        for art in claude_artifacts:
            if not art.get("synced"):
                art["synced"] = True
                art["synced_at"] = _now()
        for art in gemini_artifacts:
            if not art.get("synced"):
                art["synced"] = True
                art["synced_at"] = _now()

        # Write back
        self._write_file(OUTBOX_CLAUDE, claude_artifacts)
        self._write_file(OUTBOX_GEMINI, gemini_artifacts)

        # Update merged state
        merged = self._read_file(MERGED_STATE)
        merged.append({
            "sync_id": self.sync_count,
            "timestamp": _now(),
            "artifacts_synced": len(all_artifacts),
            "from_claude": len(unsynced_claude),
            "from_gemini": len(unsynced_gemini),
            "enhanced_insights": enhanced,
            "artifacts": all_artifacts,
        })
        self._write_file(MERGED_STATE, merged)

        # Log
        log_entry = {
            "sync_id": self.sync_count,
            "timestamp": _now(),
            "claude_synced": len(unsynced_claude),
            "gemini_synced": len(unsynced_gemini),
            "total": len(all_artifacts),
        }
        self._append_to_file(SYNC_LOG, log_entry)
        self.sync_count += 1

        return {
            "status": "synced",
            "claude_synced": len(unsynced_claude),
            "gemini_synced": len(unsynced_gemini),
            "total_artifacts": len(all_artifacts),
            "enhanced_insights": enhanced,
            "timestamp": _now(),
        }

    async def _enhance_artifacts(self, artifacts: list[dict]) -> dict:
        """Use Gemini to find cross-connections and generate meta-insights."""
        if not self.gemini or not artifacts:
            return {"connections": [], "meta_insights": []}

        prompt = f"""Du bist der Sync-Analyst des AIEmpire Dual-Systems.

Analysiere diese {len(artifacts)} Artefakte die zwischen dem Claude-System (Mac) und dem Gemini-System synchronisiert werden:

{json.dumps(artifacts, indent=2, ensure_ascii=False)[:6000]}

Finde:
1. Verbindungen zwischen Artefakten beider Systeme
2. Meta-Insights die nur durch die Kombination beider Perspektiven sichtbar werden
3. Konkrete Aktionen die aus der Synergie entstehen
4. Widersprueche oder Konflikte die aufgeloest werden muessen

Antworte als JSON:
{{
  "connections": [
    {{"from": "artifact_id", "to": "artifact_id", "insight": "..."}}
  ],
  "meta_insights": ["..."],
  "actions": ["..."],
  "conflicts": ["..."]
}}"""

        result = await self.gemini.chat_json(prompt, tier="flash")
        return result.get("parsed") or {"connections": [], "meta_insights": []}

    # -- State Reporting --

    def status(self) -> dict:
        """Get current sync status."""
        claude_arts = self._read_file(OUTBOX_CLAUDE)
        gemini_arts = self._read_file(OUTBOX_GEMINI)
        merged = self._read_file(MERGED_STATE)
        log = self._read_file(SYNC_LOG)

        return {
            "claude_outbox": len(claude_arts),
            "claude_unsynced": len([a for a in claude_arts if not a.get("synced")]),
            "gemini_outbox": len(gemini_arts),
            "gemini_unsynced": len([a for a in gemini_arts if not a.get("synced")]),
            "total_syncs": len(log),
            "total_merged_artifacts": sum(
                s.get("artifacts_synced", 0) for s in merged
            ),
            "last_sync": log[-1]["timestamp"] if log else "never",
        }

    # -- File Operations --

    def _read_file(self, path: Path) -> list:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _write_file(self, path: Path, data: list):
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _append_to_file(self, path: Path, item: dict):
        data = self._read_file(path)
        data.append(item)
        self._write_file(path, data)
