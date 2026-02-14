#!/usr/bin/env python3
"""
\U0001f527 COMPLETE MEMORY FIX FOR LOW-RAM SYSTEMS
=================================================
Aggressive(ish) memory management + helper scripts.

Notes:
- Uses psutil for cross-platform memory info.
- Avoids deleting ~/.ollama (models).
- Generates helper scripts (also committed separately):
  - memory_monitor.sh
  - smart_ollama_launch.py
"""

import os
import psutil
import subprocess
from datetime import datetime
from pathlib import Path


class MemoryFixer:
    def __init__(self):
        self.log_file = Path("memory_fix.log")

    def log(self, msg: str, level: str = "INFO") -> None:
        """Print + append a timestamped log line."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level}] {msg}"
        print(line)
        try:
            self.log_file.write_text(self.log_file.read_text() + line + "\n")
        except FileNotFoundError:
            self.log_file.write_text(line + "\n")

    def _vm(self):
        return psutil.virtual_memory()

    def print_status(self) -> None:
        vm = self._vm()
        total_gb = vm.total / (1024**3)
        used_gb = vm.used / (1024**3)
        avail_gb = vm.available / (1024**3)

        status = "OK"
        if avail_gb < 0.5:
            status = "CRITICAL"
        elif avail_gb < 1.0:
            status = "WARNING"

        print("\n" + "=" * 60)
        print("SYSTEM MEMORY STATUS")
        print("=" * 60)
        print(f"Total RAM:      {total_gb:.2f} GB")
        print(f"Used RAM:       {used_gb:.2f} GB ({vm.percent}%)")
        print(f"Available RAM:  {avail_gb:.2f} GB")
        print(f"Status:         {status}")
        print("=" * 60 + "\n")

    def kill_memory_hogs(self) -> None:
        """Kill very heavy processes only when available RAM is critically low."""
        vm = self._vm()
        avail_gb = vm.available / (1024**3)

        self.log("Scanning for memory hogs...", "SCAN")

        if avail_gb >= 0.3:
            self.log(
                f"Available RAM {avail_gb:.2f}GB is not critical; not killing processes.",
                "INFO",
            )
            return

        skip_names = {
            "kernel_task",
            "WindowServer",
            "loginwindow",
            "systemd",
            "kernel",
            "init",
            "bash",
            "zsh",
            "ssh",
        }

        for proc in psutil.process_iter(["pid", "name", "memory_percent"]):
            try:
                mem_pct = float(proc.info.get("memory_percent") or 0.0)
                name = proc.info.get("name") or ""
                pid = int(proc.info.get("pid") or 0)

                if mem_pct < 5.0:
                    continue
                if name in skip_names:
                    continue

                self.log(f"Found hog: {name} (PID {pid}) using {mem_pct:.1f}%", "WARN")

                # Critical RAM: terminate aggressively.
                self.log(f"KILLING: {name} (critical RAM)", "ERROR")
                try:
                    os.kill(pid, 9)
                except Exception:
                    pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def cleanup_cache_files(self) -> None:
        """Delete common cache locations (keeps ~/.ollama)."""
        self.log("Cleaning up cache files...", "CLEANUP")

        cache_paths = [
            Path.home() / ".cache",
            Path.home() / "Library" / "Caches",  # macOS
            Path("/tmp"),
        ]

        for cache_dir in cache_paths:
            if not cache_dir.exists():
                continue

            # Keep Ollama models.
            if str(cache_dir).endswith("/.ollama"):
                continue

            try:
                # Best-effort size log.
                result = subprocess.run(
                    ["du", "-sh", str(cache_dir)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    size_str = result.stdout.split()[0]
                    self.log(f"Cache {cache_dir}: {size_str}", "INFO")
            except Exception:
                pass

            # Best-effort cleanup.
            try:
                subprocess.run(["rm", "-rf", str(cache_dir)], timeout=30)
                self.log(f"Cleaned: {cache_dir}", "SUCCESS")
            except Exception:
                pass

    def optimize_ollama_config(self) -> None:
        """Append low-RAM Ollama env vars to shell rc files."""
        self.log("Optimizing Ollama configuration...", "CONFIG")

        ollama_env = {
            "OLLAMA_NUM_PARALLEL": "1",
            "OLLAMA_NUM_THREAD": "2",
            "OLLAMA_KEEP_ALIVE": "5m",
            "OLLAMA_MODELS_DIR": str(Path.home() / ".ollama/models"),
        }

        block_header = "# OLLAMA Memory Optimization"
        block_lines = "\n".join([f"export {k}={v}" for k, v in ollama_env.items()])
        block = f"\n{block_header}\n{block_lines}\n"

        for shell_rc in (Path.home() / ".zshrc", Path.home() / ".bashrc"):
            if not shell_rc.exists():
                continue
            try:
                existing = shell_rc.read_text()
                if block_header in existing:
                    self.log(f"{shell_rc} already contains Ollama optimization block", "INFO")
                    continue
                shell_rc.write_text(existing + block)
                self.log(f"Updated {shell_rc}", "SUCCESS")
            except Exception:
                continue

        self.log("Ollama configured for low-RAM system", "SUCCESS")

    def create_memory_monitor(self) -> None:
        """Create a cross-platform memory monitor script."""
        monitor_script = r'''#!/usr/bin/env bash
# Memory Monitor - cross-platform
# Writes to memory_fix.log and prints warnings/critical lines.

LOG_FILE="${LOG_FILE:-memory_fix.log}"

mem_snapshot() {
  # Output: total_mb used_mb avail_mb percent
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY' 2>/dev/null && return 0
try:
    import psutil
except Exception:
    raise SystemExit(1)
vm = psutil.virtual_memory()
print(int(vm.total/1024/1024), int(vm.used/1024/1024), int(vm.available/1024/1024), int(vm.percent))
PY
  fi

  if command -v free >/dev/null 2>&1; then
    free -m | awk 'NR==2{print $2, $3, $7, int($3/$2*100)}'
    return 0
  fi

  return 1
}

echo "Memory Monitor Started - $(date)" >> "$LOG_FILE"

action_on_critical() {
  pkill -f "python.*test" 2>/dev/null || true
  pkill -f "node" 2>/dev/null || true
}

while true; do
  TS=$(date "+%Y-%m-%d %H:%M:%S")

  if SNAP=$(mem_snapshot); then
    TOTAL=$(echo "$SNAP" | awk '{print $1}')
    USED=$(echo "$SNAP" | awk '{print $2}')
    FREE=$(echo "$SNAP" | awk '{print $3}')
    PERCENT=$(echo "$SNAP" | awk '{print $4}')

    if [ "$PERCENT" -gt 90 ]; then
      echo "[$TS] CRITICAL: ${PERCENT}% (${USED}MB used, ${FREE}MB free)" | tee -a "$LOG_FILE"
      action_on_critical
    elif [ "$PERCENT" -gt 75 ]; then
      echo "[$TS] WARNING: ${PERCENT}% (${USED}MB used, ${FREE}MB free)" | tee -a "$LOG_FILE"
    else
      echo "[$TS] OK: ${PERCENT}% (${USED}MB used, ${FREE}MB free)" >> "$LOG_FILE"
    fi

    OLLAMA_PROCS=$(pgrep -f ollama 2>/dev/null | wc -l | tr -d ' ')
    if [ "${OLLAMA_PROCS:-0}" -gt 0 ]; then
      echo "[$TS] Ollama running (${OLLAMA_PROCS} processes)" >> "$LOG_FILE"
    else
      echo "[$TS] Ollama not running" >> "$LOG_FILE"
    fi
  else
    echo "[$TS] Unable to read memory stats (need python3+psutil or free)" | tee -a "$LOG_FILE"
  fi

  sleep 30
done
'''

        monitor_path = Path("memory_monitor.sh")
        monitor_path.write_text(monitor_script)
        os.chmod(monitor_path, 0o755)
        self.log(f"Created memory monitor: {monitor_path}", "SUCCESS")

    def recommend_modelle(self) -> None:
        """Recommend small Ollama models for low-RAM."""
        self.log("\n" + "=" * 60, "INFO")
        self.log("MODEL RECOMMENDATIONS FOR LOW-RAM", "INFO")
        self.log("=" * 60, "INFO")

        models = [
            ("ollama pull phi:q4", "2.7B (q4)", "~600MB", "Best fit"),
            ("ollama pull phi:latest", "2.7B", "~1.4GB", "Good"),
            ("ollama pull mistral:q4_K_M", "7B (q4)", "~2.6GB", "Maybe"),
        ]

        for cmd, size, disk, note in models:
            self.log(f"{cmd:<28} | {size:<10} | {disk:<8} | {note}", "INFO")

        self.log("=" * 60 + "\n", "INFO")

    def create_smart_launcher(self) -> None:
        """Create a RAM-aware Ollama launcher."""
        launcher = r'''#!/usr/bin/env python3
"""RAM-aware Ollama launcher.

- Checks available RAM before starting.
- Starts `ollama serve` (if needed).
- Smoke-tests `phi:q4`.
"""

import os
import subprocess
import sys
import time

import psutil


def get_memory_mb():
    vm = psutil.virtual_memory()
    return int(vm.used / (1024 * 1024)), int(vm.available / (1024 * 1024)), float(vm.percent)


def check_ollama_running() -> bool:
    try:
        result = subprocess.run(["pgrep", "-f", "ollama"], capture_output=True, text=True)
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


def main() -> None:
    print("Smart Ollama Launcher")
    print("====================")

    used_mb, avail_mb, pct = get_memory_mb()
    print(f"Memory: {used_mb}MB used, {avail_mb}MB free ({pct:.1f}%)")

    # Conservative defaults for low-RAM boxes.
    min_free_mb = int(os.getenv("MIN_FREE_MB", "512"))
    max_used_pct = float(os.getenv("MAX_USED_PCT", "85"))

    if avail_mb < min_free_mb or pct > max_used_pct:
        print(f"ERROR: insufficient memory. Need >={min_free_mb}MB free and <= {max_used_pct}% used")
        print("Run: bash QUICK_MEMORY_FIX.sh")
        sys.exit(1)

    # Limit Ollama parallelism/threads for low RAM.
    os.environ.setdefault("OLLAMA_NUM_PARALLEL", "1")
    os.environ.setdefault("OLLAMA_NUM_THREAD", "2")
    os.environ.setdefault("OLLAMA_KEEP_ALIVE", "5m")

    if not check_ollama_running():
        print("Starting Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)

    print("Testing phi:q4...")
    try:
        result = subprocess.run(["ollama", "run", "phi:q4", "hello"], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print("ERROR: phi:q4 not responding")
            print(result.stderr.strip()[:500])
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: phi:q4 timed out")
        sys.exit(1)

    print("OK: system ready")


if __name__ == "__main__":
    main()
'''

        launcher_path = Path("smart_ollama_launch.py")
        launcher_path.write_text(launcher)
        os.chmod(launcher_path, 0o755)
        self.log(f"Created smart launcher: {launcher_path}", "SUCCESS")

    def generate_fix_report(self) -> None:
        """Generate a short fix report."""
        vm = self._vm()
        report = f"""
MEMORY FIX REPORT
=================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Current status:
- Total RAM: {vm.total / (1024**3):.2f} GB
- Used RAM: {vm.used / (1024**3):.2f} GB ({vm.percent}%)
- Available RAM: {vm.available / (1024**3):.2f} GB

What was configured:
- memory_monitor.sh (continuous monitoring)
- smart_ollama_launch.py (RAM-aware launcher)
- Shell env vars for Ollama (if rc file exists)

Recommended next steps:
1) Install a small model:
   ollama pull phi:q4
2) Start monitor:
   bash memory_monitor.sh &
3) Start via launcher:
   python3 smart_ollama_launch.py
"""

        Path("MEMORY_FIX_REPORT.txt").write_text(report)
        print(report)
        self.log("Fix report generated", "SUCCESS")


def main() -> None:
    print("\n" + "=" * 60)
    print("STARTING COMPLETE MEMORY FIX")
    print("=" * 60 + "\n")

    fixer = MemoryFixer()
    fixer.print_status()

    print("Step 1: Killing memory hogs (only if critical)...")
    fixer.kill_memory_hogs()

    print("\nStep 2: Cleaning cache files...")
    fixer.cleanup_cache_files()

    print("\nStep 3: Optimizing Ollama configuration...")
    fixer.optimize_ollama_config()

    print("\nStep 4: Creating memory monitor...")
    fixer.create_memory_monitor()

    print("\nStep 5: Creating smart launcher...")
    fixer.create_smart_launcher()

    print("\nStep 6: Model recommendations...")
    fixer.recommend_modelle()

    print("\nStep 7: Generating report...")
    fixer.generate_fix_report()

    print("\n" + "=" * 60)
    print("MEMORY FIX COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
