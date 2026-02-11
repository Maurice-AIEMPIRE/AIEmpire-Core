#!/usr/bin/env python3
"""RAM-aware Ollama launcher.

- Checks available RAM before starting.
- Starts `ollama serve` (if needed).
- Smoke-tests `phi:q4`.

Env overrides:
- MIN_FREE_MB (default: 512)
- MAX_USED_PCT (default: 85)
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

    min_free_mb = int(os.getenv("MIN_FREE_MB", "512"))
    max_used_pct = float(os.getenv("MAX_USED_PCT", "85"))

    if avail_mb < min_free_mb or pct > max_used_pct:
        print(f"ERROR: insufficient memory. Need >={min_free_mb}MB free and <= {max_used_pct}% used")
        print("Run: bash QUICK_MEMORY_FIX.sh")
        sys.exit(1)

    # Low-RAM defaults for Ollama.
    os.environ.setdefault("OLLAMA_NUM_PARALLEL", "1")
    os.environ.setdefault("OLLAMA_NUM_THREAD", "2")
    os.environ.setdefault("OLLAMA_KEEP_ALIVE", "5m")

    if not check_ollama_running():
        print("Starting Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)

    print("Testing phi:q4...")
    try:
        result = subprocess.run(
            ["ollama", "run", "phi:q4", "hello"],
            capture_output=True,
            text=True,
            timeout=30,
        )
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
