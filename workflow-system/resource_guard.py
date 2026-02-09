"""
RESOURCE GUARD - System-Ueberlastungsschutz
Verhindert dass Agents den Rechner ueberlasten.

Features:
- CPU/RAM/Disk Monitoring
- Automatisches Throttling bei hoher Last
- Concurrency-Reduktion bei Engpaessen
- Outsource-Modus: Verlagert Arbeit auf externe APIs wenn lokal voll
- Auto-Recovery: Skaliert wieder hoch wenn Ressourcen frei

Usage:
  guard = ResourceGuard()
  async with guard.check():   # Wartet automatisch wenn Last zu hoch
      await do_work()

  guard.get_status()           # Zeigt aktuellen Zustand
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Awaitable


# ── Thresholds ───────────────────────────────────────────

@dataclass
class ResourceLimits:
    """Konfigurierbare Schwellenwerte."""
    cpu_warn: float = 70.0          # % - Ab hier: Warning, langsamere Batches
    cpu_critical: float = 85.0      # % - Ab hier: Throttle, halbe Concurrency
    cpu_emergency: float = 95.0     # % - Ab hier: Pause alle Agents
    ram_warn: float = 75.0          # %
    ram_critical: float = 85.0      # %
    ram_emergency: float = 92.0     # %
    disk_warn: float = 85.0         # %
    disk_critical: float = 95.0     # %
    max_concurrent_default: int = 500
    max_concurrent_warn: int = 200
    max_concurrent_critical: int = 50
    max_concurrent_emergency: int = 0   # 0 = pause
    throttle_delay_warn: float = 0.5    # Extra-Delay in Sekunden
    throttle_delay_critical: float = 2.0
    recovery_check_interval: int = 10   # Sekunden zwischen Recovery-Checks


# ── Resource Sampling ────────────────────────────────────

def _get_cpu_percent() -> float:
    """CPU-Auslastung ohne psutil (pure /proc/stat oder Fallback)."""
    try:
        with open("/proc/stat", "r") as f:
            line = f.readline()
        parts = line.split()
        idle = int(parts[4])
        total = sum(int(p) for p in parts[1:])
        # Speichere fuer Delta-Berechnung
        if not hasattr(_get_cpu_percent, "_prev"):
            _get_cpu_percent._prev = (idle, total)
            time.sleep(0.1)
            return _get_cpu_percent()  # Zweite Messung fuer Delta
        prev_idle, prev_total = _get_cpu_percent._prev
        _get_cpu_percent._prev = (idle, total)
        d_idle = idle - prev_idle
        d_total = total - prev_total
        if d_total == 0:
            return 0.0
        return (1.0 - d_idle / d_total) * 100.0
    except (FileNotFoundError, IndexError, ValueError):
        # Fallback: load average (rough approximation)
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
        used_pct = (1.0 - available / total) * 100.0
        return used_pct
    except (FileNotFoundError, KeyError, ValueError, ZeroDivisionError):
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
    level: str = "normal"            # normal | warn | critical | emergency
    max_concurrent: int = 500
    throttle_delay: float = 0.0
    paused: bool = False
    outsource_mode: bool = False     # True = Arbeit auf externe API verlagern
    last_sample: Dict = field(default_factory=dict)
    history: list = field(default_factory=list)  # Letzte 60 Samples


# ── Resource Guard ───────────────────────────────────────

class ResourceGuard:
    """Schuetzt den Rechner vor Ueberlastung durch AI Agents."""

    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        self.state = GuardState(max_concurrent=self.limits.max_concurrent_default)
        self._lock = asyncio.Lock()
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Nicht pausiert
        self._on_outsource: Optional[Callable[[], Awaitable]] = None

    def on_outsource(self, callback: Callable[[], Awaitable]) -> None:
        """Registriere Callback fuer Outsource-Modus."""
        self._on_outsource = callback

    def evaluate(self) -> GuardState:
        """Bewerte aktuelle Ressourcen und setze Guard-Level."""
        metrics = sample_resources()
        self.state.last_sample = metrics

        # History fuer Trendanalyse
        self.state.history.append(metrics)
        if len(self.state.history) > 60:
            self.state.history.pop(0)

        cpu = metrics["cpu_percent"]
        ram = metrics["ram_percent"]
        disk = metrics["disk_percent"]

        # Emergency: ALLES stoppen
        if cpu >= self.limits.cpu_emergency or ram >= self.limits.ram_emergency:
            self.state.level = "emergency"
            self.state.max_concurrent = self.limits.max_concurrent_emergency
            self.state.throttle_delay = 5.0
            self.state.paused = True
            self.state.outsource_mode = True
            self._pause_event.clear()

        # Critical: Stark drosseln
        elif cpu >= self.limits.cpu_critical or ram >= self.limits.ram_critical or disk >= self.limits.disk_critical:
            self.state.level = "critical"
            self.state.max_concurrent = self.limits.max_concurrent_critical
            self.state.throttle_delay = self.limits.throttle_delay_critical
            self.state.paused = False
            self.state.outsource_mode = True
            self._pause_event.set()

        # Warning: Leicht drosseln
        elif cpu >= self.limits.cpu_warn or ram >= self.limits.ram_warn or disk >= self.limits.disk_warn:
            self.state.level = "warn"
            self.state.max_concurrent = self.limits.max_concurrent_warn
            self.state.throttle_delay = self.limits.throttle_delay_warn
            self.state.paused = False
            self.state.outsource_mode = False
            self._pause_event.set()

        # Normal: Volle Leistung
        else:
            self.state.level = "normal"
            self.state.max_concurrent = self.limits.max_concurrent_default
            self.state.throttle_delay = 0.0
            self.state.paused = False
            self.state.outsource_mode = False
            self._pause_event.set()

        return self.state

    async def wait_if_paused(self) -> None:
        """Blockiert bis System nicht mehr im Emergency-Modus."""
        if self.state.paused:
            print(f"    GUARD: System paused (CPU={self.state.last_sample.get('cpu_percent', '?')}%, "
                  f"RAM={self.state.last_sample.get('ram_percent', '?')}%). Waiting for recovery...")
            while self.state.paused:
                await asyncio.sleep(self.limits.recovery_check_interval)
                self.evaluate()
                if not self.state.paused:
                    print(f"    GUARD: Recovered! Resuming at level={self.state.level}")

    async def throttle(self) -> None:
        """Wartet die konfigurierte Throttle-Delay."""
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
        """Context Manager: evaluiert, wartet bei Pause, throttled.

        Usage:
            async with guard.check() as state:
                if state.outsource_mode:
                    await use_external_api()
                else:
                    await use_local_model()
        """
        return self._CheckContext(self)

    def get_status(self) -> Dict:
        """Aktuellen Guard-Status als Dict."""
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
            "samples_in_history": len(self.state.history),
        }

    def get_trend(self) -> Dict:
        """CPU/RAM Trend ueber die letzten Samples."""
        if len(self.state.history) < 2:
            return {"trend": "insufficient_data"}
        recent = self.state.history[-10:]
        avg_cpu = sum(s["cpu_percent"] for s in recent) / len(recent)
        avg_ram = sum(s["ram_percent"] for s in recent) / len(recent)
        first_cpu = recent[0]["cpu_percent"]
        last_cpu = recent[-1]["cpu_percent"]
        return {
            "avg_cpu": round(avg_cpu, 1),
            "avg_ram": round(avg_ram, 1),
            "cpu_direction": "rising" if last_cpu > first_cpu + 5 else "falling" if last_cpu < first_cpu - 5 else "stable",
            "ram_direction": "stable",
            "samples": len(recent),
        }

    def format_status(self) -> str:
        """Human-readable Status-Zeile."""
        s = self.get_status()
        level_icons = {"normal": "OK", "warn": "WARN", "critical": "CRIT", "emergency": "STOP"}
        icon = level_icons.get(s["level"], "?")
        return (
            f"[{icon}] CPU={s['cpu_percent']}% RAM={s['ram_percent']}% "
            f"Disk={s['disk_percent']}% | "
            f"Concurrency={s['max_concurrent']} Delay={s['throttle_delay']}s"
            f"{' | OUTSOURCE' if s['outsource_mode'] else ''}"
            f"{' | PAUSED' if s['paused'] else ''}"
        )


# ── Standalone Check ─────────────────────────────────────

def main():
    """CLI: Zeige aktuellen Ressourcen-Status."""
    guard = ResourceGuard()
    status = guard.get_status()
    print(f"""
╔══════════════════════════════════════════════════════════╗
║              RESOURCE GUARD STATUS                      ║
╠══════════════════════════════════════════════════════════╣
  Level:          {status['level'].upper()}
  CPU:            {status['cpu_percent']}%
  RAM:            {status['ram_percent']}%
  Disk:           {status['disk_percent']}%
  Max Concurrent: {status['max_concurrent']}
  Throttle Delay: {status['throttle_delay']}s
  Paused:         {status['paused']}
  Outsource Mode: {status['outsource_mode']}
╚══════════════════════════════════════════════════════════╝
    """)

    print(f"  Status line: {guard.format_status()}")


if __name__ == "__main__":
    main()
