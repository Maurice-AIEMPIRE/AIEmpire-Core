#!/usr/bin/env python3
"""
System Guardian — Prevents Mac from ever becoming unstable.
Monitors RAM/CPU and auto-kills heavy processes before the system hangs.

Runs as a LaunchAgent every 30 seconds.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# CONFIGURATION — Hard limits for 16GB Mac
# ═══════════════════════════════════════════════════════════

TOTAL_RAM_GB = 16
RAM_CRITICAL_MB = 500  # Below this: emergency kill all models
RAM_WARNING_MB = 1000  # Below this: stop idle Ollama models
RAM_MIN_FOR_7B_GB = 6  # Minimum free RAM to load a 7B model
RAM_MIN_FOR_14B_GB = 11  # Minimum free RAM to load a 14B model
LOAD_AVG_CRITICAL = 10.0  # Above this for 60s: kill Ollama models
OLLAMA_IDLE_TIMEOUT_MIN = 5  # Auto-unload after N minutes idle

LOG_DIR = Path.home() / ".antigravity" / "logs"
LOG_FILE = LOG_DIR / "guardian.log"
STATE_FILE = LOG_DIR / "guardian_state.json"

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════


def ensure_dirs():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str, level: str = "INFO"):
    ensure_dirs()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
        # Keep log file under 1MB
        if LOG_FILE.stat().st_size > 1_000_000:
            lines = LOG_FILE.read_text().splitlines()
            LOG_FILE.write_text("\n".join(lines[-500:]) + "\n")
    except Exception:
        pass


def run(cmd: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════
# SYSTEM METRICS
# ═══════════════════════════════════════════════════════════


def get_free_ram_mb() -> int:
    """Get free RAM in MB using vm_stat."""
    output = run("vm_stat")
    if not output:
        return 0

    page_size = 16384  # Apple Silicon default
    free_pages = 0
    inactive_pages = 0

    for line in output.splitlines():
        if "page size of" in line:
            try:
                page_size = int(line.split()[-2])
            except (ValueError, IndexError):
                pass
        if "Pages free:" in line:
            try:
                free_pages = int(line.split()[-1].rstrip("."))
            except (ValueError, IndexError):
                pass
        if "Pages inactive:" in line:
            try:
                inactive_pages = int(line.split()[-1].rstrip("."))
            except (ValueError, IndexError):
                pass

    # Free = free + inactive (inactive can be reclaimed)
    free_bytes = (free_pages + inactive_pages) * page_size
    return int(free_bytes / 1024 / 1024)


def get_used_ram_gb() -> float:
    """Get used RAM from top."""
    output = run("top -l 1 -s 0 | grep PhysMem")
    if not output:
        return 0.0
    try:
        # "PhysMem: 15G used (7732M wired, 6318M compressor), 117M unused."
        parts = output.split()
        for i, p in enumerate(parts):
            if p == "used":
                val = parts[i - 1]
                if val.endswith("G"):
                    return float(val[:-1])
                elif val.endswith("M"):
                    return float(val[:-1]) / 1024
    except (ValueError, IndexError) as e:
        log(f"Failed to parse RAM usage from top: {e}", "WARNING")
    return 0.0


def get_load_avg() -> float:
    """Get 1-minute load average."""
    output = run("sysctl -n vm.loadavg")
    if not output:
        return 0.0
    try:
        # "{ 10.84 11.30 11.08 }"
        parts = output.strip("{ }").split()
        return float(parts[0])
    except (ValueError, IndexError):
        return 0.0


def get_ollama_models() -> list[dict]:
    """Get currently loaded Ollama models."""
    output = run("ollama ps 2>/dev/null")
    if not output or "NAME" not in output:
        return []

    models = []
    for line in output.splitlines()[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 2:
            models.append(
                {
                    "name": parts[0],
                    "id": parts[1] if len(parts) > 1 else "",
                    "size": parts[2] if len(parts) > 2 else "",
                }
            )
    return models


# ═══════════════════════════════════════════════════════════
# ACTIONS
# ═══════════════════════════════════════════════════════════


def stop_ollama_model(model_name: str):
    """Stop a specific Ollama model."""
    log(f"🛑 STOPPING Ollama model: {model_name}", "ACTION")
    run(f"ollama stop {model_name}")


def stop_all_ollama_models():
    """Stop ALL loaded Ollama models."""
    models = get_ollama_models()
    for m in models:
        stop_ollama_model(m["name"])
    if models:
        log(f"🛑 STOPPED {len(models)} Ollama models to free RAM", "ACTION")


def send_notification(title: str, message: str):
    """Send macOS notification."""
    script = f'display notification "{message}" with title "{title}" sound name "Basso"'
    run(f"osascript -e '{script}'")


# ═══════════════════════════════════════════════════════════
# GUARDIAN LOGIC
# ═══════════════════════════════════════════════════════════


def check_and_protect() -> dict:
    """Main guardian check. Returns status dict."""
    free_ram = get_free_ram_mb()
    load_avg = get_load_avg()
    models = get_ollama_models()

    status = {
        "timestamp": datetime.now().isoformat(),
        "free_ram_mb": free_ram,
        "load_avg": load_avg,
        "ollama_models": len(models),
        "actions_taken": [],
        "status": "OK",
    }

    # ─── CRITICAL: Almost no RAM left ───
    if free_ram < RAM_CRITICAL_MB:
        log(
            f"🚨 CRITICAL: Only {free_ram}MB RAM free! Emergency shutdown of all models.",
            "CRITICAL",
        )
        stop_all_ollama_models()
        send_notification(
            "⚠️ System Guardian",
            f"CRITICAL: {free_ram}MB RAM free. Ollama models stopped.",
        )
        status["actions_taken"].append("emergency_stop_all_models")
        status["status"] = "CRITICAL"

    # ─── WARNING: RAM getting low ───
    elif free_ram < RAM_WARNING_MB:
        log(
            f"⚠️ WARNING: Only {free_ram}MB RAM free. Checking for idle models.",
            "WARNING",
        )
        if models:
            # Stop all models when RAM is low
            stop_all_ollama_models()
            send_notification("⚠️ System Guardian", f"Low RAM ({free_ram}MB). Ollama models stopped.")
            status["actions_taken"].append("stop_models_low_ram")
        status["status"] = "WARNING"

    # ─── HIGH LOAD: CPU overwhelmed ───
    if load_avg > LOAD_AVG_CRITICAL:
        log(f"⚠️ HIGH LOAD: {load_avg:.1f} (limit: {LOAD_AVG_CRITICAL})", "WARNING")
        if models:
            log("Stopping Ollama models to reduce load", "ACTION")
            stop_all_ollama_models()
            send_notification("⚠️ System Guardian", f"High CPU load ({load_avg:.1f}). Models stopped.")
            status["actions_taken"].append("stop_models_high_load")
        status["status"] = "HIGH_LOAD"

    # ─── TOO MANY MODELS ───
    if len(models) > 1:
        log(
            f"⚠️ {len(models)} models loaded. Max allowed: 1. Stopping extras.",
            "WARNING",
        )
        # Keep only the first model, stop the rest
        for m in models[1:]:
            stop_ollama_model(m["name"])
        status["actions_taken"].append("enforce_single_model")

    # ─── ALL GOOD ───
    if status["status"] == "OK":
        log(f"✅ System OK: {free_ram}MB free, load {load_avg:.1f}, {len(models)} model(s)")

    # Save state
    try:
        ensure_dirs()
        STATE_FILE.write_text(json.dumps(status, indent=2))
    except OSError as e:
        log(f"Failed to save guardian state: {e}", "WARNING")

    return status


def can_load_model(model_name: str) -> tuple[bool, str]:
    """Check if it's safe to load a model. Returns (allowed, reason)."""
    free_ram = get_free_ram_mb()
    free_ram_gb = free_ram / 1024
    models = get_ollama_models()

    # Already a model loaded?
    if models:
        return (
            False,
            f"❌ Already {len(models)} model(s) loaded: {', '.join(m['name'] for m in models)}. Stop them first: ollama stop {models[0]['name']}",
        )

    # Check RAM for model size
    is_large = any(s in model_name for s in ["14b", "32b", "70b"])
    required_gb = RAM_MIN_FOR_14B_GB if is_large else RAM_MIN_FOR_7B_GB

    if free_ram_gb < required_gb:
        return (
            False,
            f"❌ Not enough RAM: {free_ram_gb:.1f}GB free, need {required_gb}GB for {model_name}. Close apps first.",
        )

    return (
        True,
        f"✅ Safe to load {model_name}: {free_ram_gb:.1f}GB free (need {required_gb}GB)",
    )


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════


def print_status():
    """Print current system status."""
    free_ram = get_free_ram_mb()
    load_avg = get_load_avg()
    models = get_ollama_models()

    print(f"\n{'=' * 50}")
    print("🛡️  System Guardian — Status")
    print(f"{'=' * 50}")
    print(f"  RAM free:     {free_ram}MB ({free_ram / 1024:.1f}GB)")
    print(f"  Load avg:     {load_avg:.1f}")
    print(f"  Ollama models: {len(models)}")
    for m in models:
        print(f"    → {m['name']} ({m.get('size', '?')})")

    # Health assessment
    if free_ram < RAM_CRITICAL_MB:
        print(f"\n  🚨 CRITICAL: System near crash! Only {free_ram}MB free!")
    elif free_ram < RAM_WARNING_MB:
        print("\n  ⚠️  WARNING: RAM low. Consider stopping models.")
    elif free_ram < 2000:
        print("\n  ℹ️  FAIR: RAM adequate but tight.")
    else:
        print("\n  ✅ HEALTHY: System running well.")

    print(f"{'=' * 50}\n")


def daemon_loop():
    """Run guardian in daemon mode (every 30 seconds)."""
    log("🛡️ System Guardian STARTED — Protecting your Mac", "START")
    send_notification("🛡️ System Guardian", "Guardian active. Your Mac is protected.")

    while True:
        try:
            check_and_protect()
        except Exception as e:
            log(f"Guardian error: {e}", "ERROR")
        time.sleep(30)


def main():
    if len(sys.argv) < 2:
        print("""
🛡️  System Guardian — Never Crash Again

Usage:
  python3 system_guardian.py --check     One-time check & protect
  python3 system_guardian.py --status    Show system status
  python3 system_guardian.py --daemon    Run as background daemon (30s interval)
  python3 system_guardian.py --can-load <model>  Check if safe to load model
  python3 system_guardian.py --stop-all  Emergency: stop all Ollama models
""")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "--check":
        result = check_and_protect()
        print(json.dumps(result, indent=2))

    elif cmd == "--status":
        print_status()

    elif cmd == "--daemon":
        daemon_loop()

    elif cmd == "--can-load":
        model = sys.argv[2] if len(sys.argv) > 2 else "qwen2.5-coder:7b"
        allowed, reason = can_load_model(model)
        print(reason)
        sys.exit(0 if allowed else 1)

    elif cmd == "--stop-all":
        stop_all_ollama_models()
        print("✅ All Ollama models stopped.")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
