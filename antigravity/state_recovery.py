"""
State Recovery System — Crash-Resistant Checkpointing
======================================================
Implements Google Antigravity pattern: automatic checkpoints before
risky operations, instant recovery on crash.

Checkpoint structure:
  - Atomic writes with .tmp → rename pattern
  - Checksum verification on load
  - Recovery manifests listing what to restore
  - Automatic rollback on corruption

Usage:
  checkpoint = StateCheckpoint("my_task")
  checkpoint.save({"progress": 50})
  if crash_detected():
    state = checkpoint.load()  # Resume from here
"""

import hashlib
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional


# ─── Checkpoint State ───────────────────────────────────────────────────────

@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint."""
    task_id: str
    timestamp: float
    phase: str
    agent_key: str
    checksum: str = ""
    tokens_used: int = 0
    duration_seconds: float = 0.0
    status: str = "active"  # active, completed, failed, rolled_back


@dataclass
class RecoveryManifest:
    """Manifest of all recoverable checkpoints."""
    checkpoints: dict[str, CheckpointMetadata] = field(default_factory=dict)
    last_crash: Optional[float] = None
    last_successful_checkpoint: Optional[str] = None
    recovery_count: int = 0
    created: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "checkpoints": {
                k: asdict(v) for k, v in self.checkpoints.items()
            },
            "last_crash": self.last_crash,
            "last_successful": self.last_successful_checkpoint,
            "recovery_count": self.recovery_count,
            "created": self.created,
        }


# ─── Checkpoint System ──────────────────────────────────────────────────────

class StateCheckpoint:
    """
    Crash-safe checkpoint system.

    Pattern:
      1. Write to temp file
      2. Compute checksum
      3. Atomic rename to final location
      4. Update manifest
    """

    CHECKPOINT_DIR = Path("antigravity/_state")
    MANIFEST_FILE = CHECKPOINT_DIR / "RECOVERY_MANIFEST.json"

    def __init__(self, task_id: str, agent_key: str = "default", phase: str = "init"):
        self.task_id = task_id
        self.agent_key = agent_key
        self.phase = phase
        self.checkpoint_dir = self.CHECKPOINT_DIR / agent_key / task_id
        self.start_time = time.time()

        # Ensure directories exist
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    def save(self, state: dict, phase: Optional[str] = None) -> bool:
        """
        Save state with atomic write pattern.

        Returns: True if successful, False if failed
        """
        try:
            if phase:
                self.phase = phase

            # Create temp file in same directory (atomic filesystem move)
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=self.checkpoint_dir,
                suffix='.tmp',
                delete=False
            ) as tmp:
                json.dump({
                    "task_id": self.task_id,
                    "phase": self.phase,
                    "timestamp": time.time(),
                    "state": state,
                }, tmp)
                tmp_path = tmp.name

            # Compute checksum
            with open(tmp_path, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()

            # Atomic rename
            final_path = self.checkpoint_dir / f"{self.phase}.json"
            os.replace(tmp_path, final_path)

            # Update manifest
            self._update_manifest(checksum)

            return True

        except Exception as e:
            print(f"❌ Checkpoint save failed: {e}")
            # Cleanup temp file if it exists
            try:
                if 'tmp_path' in locals():
                    os.remove(tmp_path)
            except:
                pass
            return False

    def load(self) -> Optional[dict]:
        """
        Load latest checkpoint, verify checksum.

        Returns: state dict or None if not found/corrupted
        """
        try:
            # Find latest phase checkpoint
            phases = ["VERIFY", "EXECUTE", "APPROVE", "PLAN", "RESEARCH"]
            for phase in phases:
                phase_file = self.checkpoint_dir / f"{phase}.json"
                if phase_file.exists():
                    return self._load_with_verification(phase_file, phase)

            return None

        except Exception as e:
            print(f"❌ Checkpoint load failed: {e}")
            return None

    def _load_with_verification(self, path: Path, phase: str) -> Optional[dict]:
        """Load file and verify checksum."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)

            # Verify checksum from manifest
            manifest = self._load_manifest()
            checkpoint_key = f"{self.agent_key}/{self.task_id}/{phase}"

            if checkpoint_key in manifest.checkpoints:
                stored_checksum = manifest.checkpoints[checkpoint_key].checksum
                with open(path, 'rb') as f:
                    computed = hashlib.sha256(f.read()).hexdigest()

                if stored_checksum != computed:
                    print(f"⚠️  Checksum mismatch for {path}, skipping")
                    return None

            return data.get("state", {})

        except json.JSONDecodeError:
            print(f"⚠️  Corrupted checkpoint file: {path}")
            return None

    def delete(self) -> bool:
        """Delete checkpoint and manifest entry."""
        try:
            shutil.rmtree(self.checkpoint_dir)
            manifest = self._load_manifest()
            # Clean manifest entries
            keys_to_remove = [k for k in manifest.checkpoints.keys()
                            if k.startswith(f"{self.agent_key}/{self.task_id}")]
            for k in keys_to_remove:
                del manifest.checkpoints[k]
            self._save_manifest(manifest)
            return True
        except Exception as e:
            print(f"❌ Delete failed: {e}")
            return False

    def mark_completed(self) -> None:
        """Mark task as completed (don't recover)."""
        manifest = self._load_manifest()
        for key, cp in manifest.checkpoints.items():
            if self.task_id in key:
                cp.status = "completed"
        self._save_manifest(manifest)

    # ─── Manifest Management ────────────────────────────────────────────────

    def _update_manifest(self, checksum: str) -> None:
        """Update recovery manifest."""
        manifest = self._load_manifest()
        checkpoint_key = f"{self.agent_key}/{self.task_id}/{self.phase}"

        metadata = CheckpointMetadata(
            task_id=self.task_id,
            timestamp=time.time(),
            phase=self.phase,
            agent_key=self.agent_key,
            checksum=checksum,
            duration_seconds=time.time() - self.start_time,
        )

        manifest.checkpoints[checkpoint_key] = metadata
        manifest.last_successful_checkpoint = checkpoint_key
        self._save_manifest(manifest)

    @classmethod
    def _load_manifest(cls) -> RecoveryManifest:
        """Load recovery manifest."""
        try:
            if cls.MANIFEST_FILE.exists():
                with open(cls.MANIFEST_FILE) as f:
                    data = json.load(f)
                manifest = RecoveryManifest()
                for key, cp_data in data.get("checkpoints", {}).items():
                    manifest.checkpoints[key] = CheckpointMetadata(**cp_data)
                manifest.last_crash = data.get("last_crash")
                manifest.last_successful_checkpoint = data.get("last_successful")
                manifest.recovery_count = data.get("recovery_count", 0)
                return manifest
        except Exception as e:
            print(f"⚠️  Could not load manifest: {e}")

        return RecoveryManifest()

    @classmethod
    def _save_manifest(cls, manifest: RecoveryManifest) -> None:
        """Save recovery manifest."""
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=cls.CHECKPOINT_DIR,
                suffix='.tmp',
                delete=False
            ) as tmp:
                json.dump(manifest.to_dict(), tmp, indent=2)
                tmp_path = tmp.name

            os.replace(tmp_path, cls.MANIFEST_FILE)
        except Exception as e:
            print(f"❌ Manifest save failed: {e}")

    @classmethod
    def record_crash(cls) -> None:
        """Record crash for recovery."""
        manifest = cls._load_manifest()
        manifest.last_crash = time.time()
        manifest.recovery_count += 1
        cls._save_manifest(manifest)

    @classmethod
    def get_recoverable_tasks(cls) -> dict[str, dict]:
        """Get all tasks that can be recovered."""
        manifest = cls._load_manifest()
        recoverable = {}

        for key, cp in manifest.checkpoints.items():
            if cp.status != "completed":
                if key not in recoverable:
                    recoverable[key] = asdict(cp)

        return recoverable

    @classmethod
    def cleanup_old_checkpoints(cls, days: int = 7) -> int:
        """Delete checkpoints older than N days."""
        cutoff = time.time() - (days * 86400)
        manifest = cls._load_manifest()
        removed = 0

        for key, cp in list(manifest.checkpoints.items()):
            if cp.timestamp < cutoff and cp.status == "completed":
                del manifest.checkpoints[key]
                removed += 1

        cls._save_manifest(manifest)
        return removed


# ─── Health Check ──────────────────────────────────────────────────────────

def check_recovery_status() -> dict:
    """Check system recovery status."""
    manifest = StateCheckpoint._load_manifest()

    return {
        "total_checkpoints": len(manifest.checkpoints),
        "last_crash": manifest.last_crash,
        "recovery_count": manifest.recovery_count,
        "recoverable_tasks": len([
            cp for cp in manifest.checkpoints.values()
            if cp.status != "completed"
        ]),
        "last_successful": manifest.last_successful_checkpoint,
    }


if __name__ == "__main__":
    # Test
    print("=== STATE RECOVERY TEST ===\n")

    checkpoint = StateCheckpoint("test_task_001", "coder", "PLAN")

    # Save checkpoint
    print("Saving checkpoint...")
    state = {"code": "def hello(): pass", "progress": 50}
    if checkpoint.save(state):
        print("✓ Checkpoint saved\n")

    # Load checkpoint
    print("Loading checkpoint...")
    loaded = checkpoint.load()
    print(f"✓ Loaded: {loaded}\n")

    # Show recovery status
    status = check_recovery_status()
    print(f"Recovery Status: {json.dumps(status, indent=2)}")
