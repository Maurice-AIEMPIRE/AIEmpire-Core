"""
RESOURCE GUARD v2 - Crash-Proof System Protection
===================================================
Prevents system overload AND recovers from crashes.

v2 Improvements over v1:
- PREEMPTIVE checks: blocks agent launch if resources insufficient
- PREDICTIVE throttling: detects rising trends before hitting limits
- SIGNAL handling: graceful shutdown on SIGTERM/SIGINT
- CRASH RECOVERY: detects previous crash and enters safe mode
- OLLAMA INTEGRATION: auto-kills models when RAM critical (macOS)
- ATOMIC STATE: saves guard state crash-safe via sync_engine

Usage:
  guard = ResourceGuard()
  guard.startup_check()  # Run once at start — detects crashes

  async with guard.check():   # Wartet automatisch wenn Last zu hoch
      await do_work()

  guard.can_launch("14b")     # Preemptive: enough resources?
  guard.get_status()           # Zeigt aktuellen Zustand
"""

import asyncio
import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable, Awaitable, Tuple


# ── State File ──────────────────────────────────────────
STATE_DIR = Path(__file__).parent / "state"
GUARD_STATE_FILE = STATE_DIR / "guard_state.json"
CRASH_LOG_FILE = STATE_DIR / "crash_log.jsonl"


def _ensure_state_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


# ── Thresholds ───────────────────────────────────────────

@dataclass
class ResourceLimits:
    """Konfigurierbare Schwellenwerte — optimiert fuer 16GB Mac."""
    cpu_warn: float = 70.0
    cpu_critical: float = 85.0
    cpu_emergency: float = 95.0
    ram_warn: float = 75.0
    ram_critical: float = 85.0
    ram_emergency: float = 92.0
    disk_warn: float = 85.0
    disk_critical: float = 95.0
    max_concurrent_default: int = 500
    max_concurrent_warn: int = 200
    max_concurrent_critical: int = 50
    max_concurrent_emergency: int = 0
    throttle_delay_warn: float = 0.5
    throttle_delay_critical: float = 2.0
    recovery_check_interval: int = 10
    # v2: Preemptive limits
    min_ram_pct_free_for_7b: float = 35.0   # Need 35% free RAM for 7B model
    min_ram_pct_free_for_14b: float = 60.0  # Need 60% free RAM for 14B model
    min_ram_pct_free_for_agent: float = 15.0  # Minimum free for any agent work
    trend_rising_threshold: float = 5.0     # % increase per 5 samples = rising


# ── Resource Sampling ────────────────────────────────────

def _get_cpu_percent() -> float:
    """CPU-Auslastung ohne psutil (pure /proc/stat oder Fallback)."""
    try:
        with open("/proc/stat", "r") as f:
            line = f.readline()
        parts = line.split()
        idle = int(parts[4])
        total = sum(int(p) for p in parts[1:])
        if not hasattr(_get_cpu_percent, "_prev"):
            _get_cpu_percent._prev = (idle, total)
            time.sleep(0.1)
            return _get_cpu_percent()
        prev_idle, prev_total = _get_cpu_percent._prev
        _get_cpu_percent._prev = (idle, total)
        d_idle = idle - prev_idle
        d_total = total - prev_total
        if d_total == 0:
            return 0.0
        return (1.0 - d_idle / d_total) * 100.0
    except (FileNotFoundError, IndexError, ValueError):
        try:
            load = os.getloadavg()[0]
            cpu_count = os.cpu_count() or 1
            return min((load / cpu_count) * 100.0, 100.0)
        except OSError:
            return 0.0


def _get_ram_percent() -> float:
    """RAM-Auslastung ohne psutil."""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
        info = {}
        for line in lines[:10]:
            parts = line.split()
            if len(parts) >= 2:
                info[parts[0].rstrip(":")] = int(parts[1])
        total = info.get("MemTotal", 1)
        available = info.get("MemAvailable", info.get("MemFree", 0))
        return (1.0 - available / total) * 100.0
    except (FileNotFoundError, KeyError, ValueError, ZeroDivisionError):
        # macOS fallback
        try:
            out = subprocess.check_output(
                ["vm_stat"], text=True, timeout=5, stderr=subprocess.DEVNULL
            )
            page_size = 16384
            free_pages = inactive_pages = 0
            for l in out.splitlines():
                if "page size of" in l:
                    try: page_size = int(l.split()[-2])
                    except: pass
                if "Pages free:" in l:
                    try: free_pages = int(l.split()[-1].rstrip("."))
                    except: pass
                if "Pages inactive:" in l:
                    try: inactive_pages = int(l.split()[-1].rstrip("."))
                    except: pass
            free_bytes = (free_pages + inactive_pages) * page_size
            total_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            if total_bytes > 0:
                return (1.0 - free_bytes / total_bytes) * 100.0
        except Exception:
            pass
        return 0.0


def _get_disk_percent(path: str = "/") -> float:
    """Disk-Auslastung."""
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        if total == 0:
            return 0.0
        return (1.0 - free / total) * 100.0
    except OSError:
        return 0.0


def sample_resources() -> Dict:
    """Alle Metriken auf einmal samplen."""
    return {
        "cpu_percent": round(_get_cpu_percent(), 1),
        "ram_percent": round(_get_ram_percent(), 1),
        "disk_percent": round(_get_disk_percent(), 1),
        "timestamp": time.time(),
    }


# ── Guard State ──────────────────────────────────────────

@dataclass
class GuardState:
    level: str = "normal"
    max_concurrent: int = 500
    throttle_delay: float = 0.0
    paused: bool = False
    outsource_mode: bool = False
    safe_mode: bool = False       # v2: After crash, start in safe mode
    last_sample: Dict = field(default_factory=dict)
    history: list = field(default_factory=list)
    crash_count: int = 0          # v2: Track crash history
    last_crash: str = ""          # v2: ISO timestamp of last crash


# ── Resource Guard v2 ───────────────────────────────────

class ResourceGuard:
    """Crash-proof system protection for AI agents."""

    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        self.state = GuardState(max_concurrent=self.limits.max_concurrent_default)
        self._lock = asyncio.Lock()
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._on_outsource: Optional[Callable[[], Awaitable]] = None
        self._shutdown_requested = False
        _ensure_state_dir()
        self._setup_signal_handlers()

    # ── Signal Handling (Graceful Shutdown) ──────────────

    def _setup_signal_handlers(self):
        """Register handlers for SIGTERM/SIGINT to prevent corrupt state."""
        try:
            signal.signal(signal.SIGTERM, self._handle_shutdown)
            signal.signal(signal.SIGINT, self._handle_shutdown)
        except (ValueError, OSError):
            # Can fail if not in main thread
            pass

    def _handle_shutdown(self, signum, frame):
        """Graceful shutdown: save state, unpause, exit cleanly."""
        self._shutdown_requested = True
        self.state.paused = False
        self._pause_event.set()
        self._save_state(clean_shutdown=True)
        print(f"\n    GUARD: Graceful shutdown (signal {signum}). State saved.")

    # ── Crash Detection & Recovery ──────────────────────

    def startup_check(self) -> Dict:
        """
        Run at startup. Detects if previous session crashed and enters safe mode.
        Returns: {crash_detected, safe_mode, crash_count, recommendations}
        """
        result = {
            "crash_detected": False,
            "safe_mode": False,
            "crash_count": 0,
            "recommendations": [],
        }

        # Load previous state
        prev_state = self._load_state()
        if prev_state:
            # If previous state wasn't a clean shutdown, it was a crash
            if not prev_state.get("clean_shutdown", False):
                result["crash_detected"] = True
                self.state.crash_count = prev_state.get("crash_count", 0) + 1
                self.state.last_crash = datetime.now().isoformat()
                result["crash_count"] = self.state.crash_count

                # Log the crash
                self._log_crash(prev_state)

                # Enter safe mode after crash
                self.state.safe_mode = True
                result["safe_mode"] = True

                # Reduce limits in safe mode
                self.limits.max_concurrent_default = min(100, self.limits.max_concurrent_default)
                self.limits.cpu_warn = min(60.0, self.limits.cpu_warn)
                self.limits.ram_warn = min(65.0, self.limits.ram_warn)
                self.state.max_concurrent = self.limits.max_concurrent_default

                result["recommendations"].append(
                    "System crashed previously. Running in SAFE MODE with reduced limits."
                )

                if self.state.crash_count >= 3:
                    result["recommendations"].append(
                        "3+ crashes detected. Consider: (1) Reduce model size to 7B, "
                        "(2) Enable OFFLINE_MODE, (3) Check system_guardian.py daemon."
                    )

        # Save fresh state (not clean yet — will be marked clean on shutdown)
        self._save_state(clean_shutdown=False)
        return result

    def exit_safe_mode(self):
        """Exit safe mode once system is confirmed stable."""
        self.state.safe_mode = False
        self.limits.max_concurrent_default = 500
        self.limits.cpu_warn = 70.0
        self.limits.ram_warn = 75.0
        self.state.max_concurrent = self.limits.max_concurrent_default
        print("    GUARD: Exited safe mode. Full performance restored.")

    def _save_state(self, clean_shutdown: bool = False):
        """Save guard state atomically."""
        try:
            data = {
                "level": self.state.level,
                "crash_count": self.state.crash_count,
                "last_crash": self.state.last_crash,
                "safe_mode": self.state.safe_mode,
                "clean_shutdown": clean_shutdown,
                "timestamp": datetime.now().isoformat(),
                "last_sample": self.state.last_sample,
            }
            # Atomic write: temp file + rename
            tmp_path = GUARD_STATE_FILE.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(data, indent=2))
            tmp_path.rename(GUARD_STATE_FILE)
        except Exception:
            pass

    def _load_state(self) -> Optional[Dict]:
        """Load previous guard state."""
        try:
            if GUARD_STATE_FILE.exists():
                return json.loads(GUARD_STATE_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            pass
        return None

    def _log_crash(self, prev_state: Dict):
        """Append crash to crash log."""
        try:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "previous_level": prev_state.get("level", "unknown"),
                "previous_sample": prev_state.get("last_sample", {}),
                "crash_number": self.state.crash_count,
            }
            with open(CRASH_LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ── Preemptive Checks (v2 — check BEFORE launch) ───

    def can_launch(self, model_size: str = "7b") -> Tuple[bool, str]:
        """
        Preemptive check: is it safe to launch an agent/model?

        Args:
            model_size: "7b", "14b", "32b", or "agent" (no model)

        Returns:
            (allowed, reason)
        """
        metrics = sample_resources()
        ram_free_pct = 100.0 - metrics["ram_percent"]
        cpu = metrics["cpu_percent"]

        # Emergency: never launch anything
        if cpu >= self.limits.cpu_emergency or metrics["ram_percent"] >= self.limits.ram_emergency:
            return False, f"EMERGENCY: CPU={cpu}% RAM={metrics['ram_percent']}%. System overloaded."

        # Check model-specific RAM requirements
        if "14b" in model_size or "32b" in model_size:
            if ram_free_pct < self.limits.min_ram_pct_free_for_14b:
                return False, (
                    f"Not enough RAM for {model_size}: {ram_free_pct:.0f}% free, "
                    f"need {self.limits.min_ram_pct_free_for_14b:.0f}%."
                )
        elif "7b" in model_size:
            if ram_free_pct < self.limits.min_ram_pct_free_for_7b:
                return False, (
                    f"Not enough RAM for {model_size}: {ram_free_pct:.0f}% free, "
                    f"need {self.limits.min_ram_pct_free_for_7b:.0f}%."
                )
        else:
            if ram_free_pct < self.limits.min_ram_pct_free_for_agent:
                return False, (
                    f"Not enough RAM for agent work: {ram_free_pct:.0f}% free, "
                    f"need {self.limits.min_ram_pct_free_for_agent:.0f}%."
                )

        # Check trend: if RAM is rising fast, warn
        trend = self.get_trend()
        if trend.get("ram_direction") == "rising":
            return True, f"OK but RAM trending up ({trend.get('avg_ram', '?')}% avg). Monitor closely."

        return True, f"OK: CPU={cpu}% RAM={metrics['ram_percent']}% ({ram_free_pct:.0f}% free)"

    # ── Predictive Trend Detection ──────────────────────

    def get_trend(self) -> Dict:
        """CPU/RAM Trend ueber die letzten Samples — now with direction detection."""
        if len(self.state.history) < 3:
            return {"trend": "insufficient_data"}
        recent = self.state.history[-10:]
        avg_cpu = sum(s["cpu_percent"] for s in recent) / len(recent)
        avg_ram = sum(s["ram_percent"] for s in recent) / len(recent)
        first_cpu = recent[0]["cpu_percent"]
        last_cpu = recent[-1]["cpu_percent"]
        first_ram = recent[0]["ram_percent"]
        last_ram = recent[-1]["ram_percent"]

        threshold = self.limits.trend_rising_threshold

        return {
            "avg_cpu": round(avg_cpu, 1),
            "avg_ram": round(avg_ram, 1),
            "cpu_direction": (
                "rising" if last_cpu > first_cpu + threshold
                else "falling" if last_cpu < first_cpu - threshold
                else "stable"
            ),
            "ram_direction": (
                "rising" if last_ram > first_ram + threshold
                else "falling" if last_ram < first_ram - threshold
                else "stable"
            ),
            "samples": len(recent),
        }

    # ── Core Evaluation ─────────────────────────────────

    def on_outsource(self, callback: Callable[[], Awaitable]) -> None:
        """Registriere Callback fuer Outsource-Modus."""
        self._on_outsource = callback

    def evaluate(self) -> GuardState:
        """Bewerte aktuelle Ressourcen und setze Guard-Level."""
        if self._shutdown_requested:
            return self.state

        metrics = sample_resources()
        self.state.last_sample = metrics

        self.state.history.append(metrics)
        if len(self.state.history) > 60:
            self.state.history.pop(0)

        cpu = metrics["cpu_percent"]
        ram = metrics["ram_percent"]
        disk = metrics["disk_percent"]

        # Safe mode: use lower thresholds
        cpu_warn = self.limits.cpu_warn
        ram_warn = self.limits.ram_warn

        # Emergency
        if cpu >= self.limits.cpu_emergency or ram >= self.limits.ram_emergency:
            self.state.level = "emergency"
            self.state.max_concurrent = self.limits.max_concurrent_emergency
            self.state.throttle_delay = 5.0
            self.state.paused = True
            self.state.outsource_mode = True
            self._pause_event.clear()
            self._emergency_actions(metrics)

        # Critical
        elif cpu >= self.limits.cpu_critical or ram >= self.limits.ram_critical or disk >= self.limits.disk_critical:
            self.state.level = "critical"
            self.state.max_concurrent = self.limits.max_concurrent_critical
            self.state.throttle_delay = self.limits.throttle_delay_critical
            self.state.paused = False
            self.state.outsource_mode = True
            self._pause_event.set()

        # Warning
        elif cpu >= cpu_warn or ram >= ram_warn or disk >= self.limits.disk_warn:
            self.state.level = "warn"
            self.state.max_concurrent = self.limits.max_concurrent_warn
            self.state.throttle_delay = self.limits.throttle_delay_warn
            self.state.paused = False
            self.state.outsource_mode = False
            self._pause_event.set()

        # v2: Predictive — check if trend is rising toward critical
        elif self._is_trending_critical():
            self.state.level = "warn"
            self.state.max_concurrent = self.limits.max_concurrent_warn
            self.state.throttle_delay = self.limits.throttle_delay_warn
            self.state.paused = False
            self.state.outsource_mode = False
            self._pause_event.set()

        # Normal
        else:
            self.state.level = "normal"
            self.state.max_concurrent = self.limits.max_concurrent_default
            self.state.throttle_delay = 0.0
            self.state.paused = False
            self.state.outsource_mode = False
            self._pause_event.set()

        # Periodically save state (every 10 samples)
        if len(self.state.history) % 10 == 0:
            self._save_state(clean_shutdown=False)

        return self.state

    def _is_trending_critical(self) -> bool:
        """Predictive: are we headed toward critical levels?"""
        trend = self.get_trend()
        if trend.get("trend") == "insufficient_data":
            return False
        avg_cpu = trend.get("avg_cpu", 0)
        avg_ram = trend.get("avg_ram", 0)
        cpu_rising = trend.get("cpu_direction") == "rising"
        ram_rising = trend.get("ram_direction") == "rising"

        # If average is above 60% AND rising → preemptive throttle
        if (avg_cpu > 60 and cpu_rising) or (avg_ram > 65 and ram_rising):
            return True
        return False

    def _emergency_actions(self, metrics: Dict):
        """v2: Active emergency response — try to free resources."""
        # Try to stop Ollama models (macOS)
        try:
            result = subprocess.run(
                ["ollama", "ps"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "NAME" in result.stdout:
                for line in result.stdout.splitlines()[1:]:
                    model_name = line.split()[0] if line.split() else None
                    if model_name:
                        subprocess.run(
                            ["ollama", "stop", model_name],
                            capture_output=True, timeout=10
                        )
                        print(f"    GUARD: EMERGENCY — stopped Ollama model: {model_name}")
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass

    # ── Async Context Manager ───────────────────────────

    async def wait_if_paused(self) -> None:
        """Blockiert bis System nicht mehr im Emergency-Modus."""
        if self.state.paused:
            print(
                f"    GUARD: System paused (CPU={self.state.last_sample.get('cpu_percent', '?')}%, "
                f"RAM={self.state.last_sample.get('ram_percent', '?')}%). Waiting for recovery..."
            )
            while self.state.paused and not self._shutdown_requested:
                await asyncio.sleep(self.limits.recovery_check_interval)
                self.evaluate()
                if not self.state.paused:
                    print(f"    GUARD: Recovered! Resuming at level={self.state.level}")

    async def throttle(self) -> None:
        if self.state.throttle_delay > 0:
            await asyncio.sleep(self.state.throttle_delay)

    class _CheckContext:
        """Async Context Manager fuer guard.check()."""
        def __init__(self, guard: 'ResourceGuard'):
            self.guard = guard

        async def __aenter__(self):
            self.guard.evaluate()
            await self.guard.wait_if_paused()
            await self.guard.throttle()
            return self.guard.state

        async def __aexit__(self, *args):
            pass

    def check(self) -> '_CheckContext':
        return self._CheckContext(self)

    # ── Status & Formatting ─────────────────────────────

    def get_status(self) -> Dict:
        self.evaluate()
        return {
            "level": self.state.level,
            "cpu_percent": self.state.last_sample.get("cpu_percent", 0),
            "ram_percent": self.state.last_sample.get("ram_percent", 0),
            "disk_percent": self.state.last_sample.get("disk_percent", 0),
            "max_concurrent": self.state.max_concurrent,
            "throttle_delay": self.state.throttle_delay,
            "paused": self.state.paused,
            "outsource_mode": self.state.outsource_mode,
            "safe_mode": self.state.safe_mode,
            "crash_count": self.state.crash_count,
            "samples_in_history": len(self.state.history),
        }

    def format_status(self) -> str:
        s = self.get_status()
        level_icons = {"normal": "OK", "warn": "WARN", "critical": "CRIT", "emergency": "STOP"}
        icon = level_icons.get(s["level"], "?")
        safe = " | SAFE-MODE" if s["safe_mode"] else ""
        return (
            f"[{icon}] CPU={s['cpu_percent']}% RAM={s['ram_percent']}% "
            f"Disk={s['disk_percent']}% | "
            f"Concurrency={s['max_concurrent']} Delay={s['throttle_delay']}s"
            f"{' | OUTSOURCE' if s['outsource_mode'] else ''}"
            f"{' | PAUSED' if s['paused'] else ''}"
            f"{safe}"
        )

    def shutdown(self):
        """Call for clean shutdown — marks state as clean."""
        self._save_state(clean_shutdown=True)
        print("    GUARD: Clean shutdown. State saved.")


# ── Standalone Check ─────────────────────────────────────

def main():
    """CLI: Zeige aktuellen Ressourcen-Status + crash recovery."""
    import sys

    guard = ResourceGuard()

    if len(sys.argv) > 1 and sys.argv[1] == "--recover":
        result = guard.startup_check()
        print(json.dumps(result, indent=2))
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--can-launch":
        model = sys.argv[2] if len(sys.argv) > 2 else "7b"
        allowed, reason = guard.can_launch(model)
        print(f"{'ALLOWED' if allowed else 'BLOCKED'}: {reason}")
        return

    # Default: show status
    recovery = guard.startup_check()
    status = guard.get_status()

    if recovery["crash_detected"]:
        print(f"""
╔══════════════════════════════════════════════════════════╗
║          !! CRASH DETECTED — SAFE MODE !!               ║
╠══════════════════════════════════════════════════════════╣
  Crash Count:    {recovery['crash_count']}
  Safe Mode:      {recovery['safe_mode']}
  Recommendations:""")
        for rec in recovery.get("recommendations", []):
            print(f"    - {rec}")
        print(f"╚══════════════════════════════════════════════════════════╝")

    print(f"""
╔══════════════════════════════════════════════════════════╗
║              RESOURCE GUARD v2 STATUS                    ║
╠══════════════════════════════════════════════════════════╣
  Level:          {status['level'].upper()}
  CPU:            {status['cpu_percent']}%
  RAM:            {status['ram_percent']}%
  Disk:           {status['disk_percent']}%
  Max Concurrent: {status['max_concurrent']}
  Throttle Delay: {status['throttle_delay']}s
  Paused:         {status['paused']}
  Outsource Mode: {status['outsource_mode']}
  Safe Mode:      {status['safe_mode']}
  Crash Count:    {status['crash_count']}
╚══════════════════════════════════════════════════════════╝
    """)

    # Preemptive check
    for model in ["7b", "14b"]:
        allowed, reason = guard.can_launch(model)
        icon = "OK" if allowed else "BLOCK"
        print(f"  [{icon}] Launch {model}: {reason}")

    print(f"\n  Status line: {guard.format_status()}")


if __name__ == "__main__":
    main()
