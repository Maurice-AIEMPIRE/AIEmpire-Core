"""
Sync Engine — Crash-Safe State Synchronization
================================================
Synchronizes state between local agents, cloud providers, and the
filesystem. Uses atomic writes and journaling to prevent corruption
from crashes or unexpected shutdowns.

Features:
- Atomic file writes (write to tmp, then rename)
- State journaling (track all state changes)
- Crash recovery (detect and repair incomplete writes)
- Provider state sync (Ollama, Gemini, Moonshot status)
"""

import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ─── Paths ──────────────────────────────────────────────────────────
STATE_DIR = Path(__file__).parent / "_state"
JOURNAL_FILE = STATE_DIR / "sync_journal.jsonl"
PROVIDER_STATE_FILE = STATE_DIR / "provider_state.json"
CRASH_MARKER = STATE_DIR / ".crash_marker"
LAST_SYNC_FILE = STATE_DIR / "last_sync.json"


def _ensure_dirs():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def atomic_write(path: Path, data: str) -> bool:
    """
    Write data atomically: write to temp file, then rename.
    This prevents corruption if the process is killed mid-write.
    """
    _ensure_dirs()
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=str(path.parent), suffix=".tmp", prefix=".sync_"
        )
        with os.fdopen(fd, "w") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp_path, str(path))
        return True
    except Exception as e:
        # Clean up temp file if rename failed
        try:
            os.unlink(tmp_path)
        except (OSError, UnboundLocalError):
            pass
        print(f"⚠️  atomic_write failed for {path}: {e}")
        return False


def atomic_write_json(path: Path, obj: Any) -> bool:
    """Write a JSON object atomically."""
    return atomic_write(path, json.dumps(obj, indent=2, ensure_ascii=False))


class SyncEngine:
    """
    Crash-safe state synchronization engine.

    Usage:
        engine = SyncEngine()
        engine.check_crash_recovery()  # On startup
        engine.save_state("providers", {"gemini": True, "ollama": True})
        state = engine.load_state("providers")
    """

    def __init__(self):
        _ensure_dirs()
        self._set_crash_marker()

    def _set_crash_marker(self):
        """Set crash marker on init. Cleared on clean shutdown."""
        try:
            CRASH_MARKER.write_text(json.dumps({
                "pid": os.getpid(),
                "timestamp": datetime.now().isoformat(),
                "status": "running",
            }))
        except OSError as e:
            import warnings
            warnings.warn(f"Failed to set crash marker: {e}", stacklevel=2)

    def clear_crash_marker(self):
        """Call on clean shutdown to indicate no crash."""
        try:
            CRASH_MARKER.unlink(missing_ok=True)
        except OSError as e:
            import warnings
            warnings.warn(f"Failed to clear crash marker: {e}", stacklevel=2)

    def was_crash(self) -> bool:
        """Check if the previous session crashed (marker still present)."""
        return CRASH_MARKER.exists()

    def check_crash_recovery(self) -> dict:
        """
        Check for crash artifacts and repair if needed.
        Call this at startup.
        """
        result = {
            "crash_detected": False,
            "repairs": [],
            "timestamp": datetime.now().isoformat(),
        }

        if self.was_crash():
            result["crash_detected"] = True
            try:
                marker_data = json.loads(CRASH_MARKER.read_text())
                result["previous_pid"] = marker_data.get("pid")
                result["crash_time"] = marker_data.get("timestamp")
            except (json.JSONDecodeError, OSError) as e:
                result["marker_read_error"] = str(e)

            # Clean up temp files from interrupted writes
            for tmp_file in STATE_DIR.glob(".sync_*.tmp"):
                try:
                    tmp_file.unlink()
                    result["repairs"].append(f"Removed temp file: {tmp_file.name}")
                except OSError as e:
                    result["repairs"].append(f"Failed to remove {tmp_file.name}: {e}")

            # Validate JSON state files
            for state_file in STATE_DIR.glob("*.json"):
                try:
                    json.loads(state_file.read_text())
                except (json.JSONDecodeError, Exception):
                    backup = state_file.with_suffix(".json.corrupt")
                    state_file.rename(backup)
                    result["repairs"].append(
                        f"Moved corrupt file: {state_file.name} → {backup.name}"
                    )

            self._journal({"event": "crash_recovery", **result})

        # Set fresh crash marker for this session
        self._set_crash_marker()
        return result

    def save_state(self, key: str, data: Any) -> bool:
        """Save a named state object atomically."""
        path = STATE_DIR / f"{key}.json"
        success = atomic_write_json(path, {
            "key": key,
            "data": data,
            "updated": datetime.now().isoformat(),
        })
        if success:
            self._journal({"event": "state_saved", "key": key})
        return success

    def load_state(self, key: str, default: Any = None) -> Any:
        """Load a named state object."""
        path = STATE_DIR / f"{key}.json"
        if not path.exists():
            return default
        try:
            envelope = json.loads(path.read_text())
            return envelope.get("data", default)
        except (json.JSONDecodeError, Exception):
            return default

    def save_provider_state(self, providers: dict[str, bool]) -> bool:
        """Save provider availability state."""
        return self.save_state("providers", {
            "status": providers,
            "checked_at": datetime.now().isoformat(),
        })

    def load_provider_state(self) -> Optional[dict]:
        """Load last known provider state."""
        return self.load_state("providers")

    def _journal(self, entry: dict):
        """Append an entry to the sync journal (append-only log)."""
        _ensure_dirs()
        entry["timestamp"] = datetime.now().isoformat()
        try:
            with open(JOURNAL_FILE, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            # Truncate journal if too large (keep last 500 entries)
            if JOURNAL_FILE.stat().st_size > 500_000:
                lines = JOURNAL_FILE.read_text().splitlines()
                JOURNAL_FILE.write_text("\n".join(lines[-500:]) + "\n")
        except OSError as e:
            import warnings
            warnings.warn(f"Failed to write journal: {e}", stacklevel=2)

    def get_journal(self, last_n: int = 50) -> list[dict]:
        """Read recent journal entries."""
        if not JOURNAL_FILE.exists():
            return []
        try:
            lines = JOURNAL_FILE.read_text().splitlines()
            entries = []
            for line in lines[-last_n:]:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            return entries
        except Exception:
            return []

    def shutdown(self):
        """Clean shutdown — clears crash marker."""
        self._journal({"event": "clean_shutdown"})
        self.clear_crash_marker()


# ─── Module-level singleton ─────────────────────────────────────────
_engine: Optional[SyncEngine] = None


def get_sync_engine() -> SyncEngine:
    """Get the default SyncEngine instance."""
    global _engine
    if _engine is None:
        _engine = SyncEngine()
    return _engine


# ─── CLI ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    engine = SyncEngine()

    if len(sys.argv) < 2:
        print("""
Sync Engine — Crash-Safe State Synchronization

Usage:
  python sync_engine.py recover    Check for crash & recover
  python sync_engine.py status     Show current state
  python sync_engine.py journal    Show recent journal entries
  python sync_engine.py test       Run atomic write test
""")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "recover":
        result = engine.check_crash_recovery()
        print(json.dumps(result, indent=2))

    elif cmd == "status":
        providers = engine.load_provider_state()
        print(f"Crash marker: {'YES' if engine.was_crash() else 'no'}")
        print(f"Provider state: {json.dumps(providers, indent=2) if providers else 'none'}")

    elif cmd == "journal":
        entries = engine.get_journal(20)
        for e in entries:
            print(json.dumps(e))

    elif cmd == "test":
        print("Testing atomic write...")
        test_path = STATE_DIR / "test_atomic.json"
        success = atomic_write_json(test_path, {"test": True, "time": time.time()})
        print(f"Result: {'OK' if success else 'FAILED'}")
        if success:
            data = json.loads(test_path.read_text())
            print(f"Read back: {data}")
            test_path.unlink()

    else:
        print(f"Unknown command: {cmd}")
