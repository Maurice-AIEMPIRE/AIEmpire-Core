#!/usr/bin/env python3
"""
SMART OLLAMA LAUNCH - Memory-aware Ollama starter
Startet Ollama nur wenn genuegend RAM frei ist.
Waehlt automatisch das richtige Modell basierend auf verfuegbarem RAM.

Usage:
  python3 smart_ollama_launch.py              # Auto-detect und starten
  python3 smart_ollama_launch.py --model phi  # Spezifisches Modell
  python3 smart_ollama_launch.py --status     # Nur Status zeigen
"""

import argparse
import os
import subprocess
import sys
import time

# Modelle sortiert nach RAM-Bedarf (kleinste zuerst)
MODELS = [
    {"name": "phi:q4",         "ram_mb": 800,  "desc": "Phi-2 Q4 - schnell, klein"},
    {"name": "phi3:mini",      "ram_mb": 1200, "desc": "Phi-3 Mini - gut fuer Code"},
    {"name": "qwen2:1.5b",    "ram_mb": 1000, "desc": "Qwen2 1.5B - multilingual"},
    {"name": "llama3.2:1b",   "ram_mb": 1200, "desc": "Llama 3.2 1B - Meta baseline"},
    {"name": "gemma2:2b",     "ram_mb": 1500, "desc": "Gemma 2B - Google quality"},
    {"name": "mistral:7b-q4", "ram_mb": 4000, "desc": "Mistral 7B Q4 - stark"},
]

# Minimum freier RAM bevor Ollama gestartet wird
MIN_FREE_RAM_MB = 500
# RAM-Reserve die immer frei bleiben soll
RAM_RESERVE_MB = 800


def get_memory_info():
    """Liest /proc/meminfo fuer RAM-Status."""
    info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    val_kb = int(parts[1])
                    info[key] = val_kb
    except (FileNotFoundError, ValueError):
        # Fallback fuer macOS
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5,
            )
            total_bytes = int(result.stdout.strip())
            info["MemTotal"] = total_bytes // 1024

            result = subprocess.run(
                ["vm_stat"], capture_output=True, text=True, timeout=5,
            )
            # Rough estimate from vm_stat
            free_pages = 0
            for line in result.stdout.split("\n"):
                if "free" in line.lower():
                    parts = line.split()
                    for p in parts:
                        p = p.strip(".")
                        if p.isdigit():
                            free_pages = int(p)
                            break
            info["MemAvailable"] = free_pages * 4  # 4KB pages -> KB
        except Exception:
            return None

    return {
        "total_mb": info.get("MemTotal", 0) // 1024,
        "available_mb": info.get("MemAvailable", info.get("MemFree", 0)) // 1024,
        "used_mb": (info.get("MemTotal", 0) - info.get("MemAvailable", info.get("MemFree", 0))) // 1024,
        "percent": round(
            (1 - info.get("MemAvailable", info.get("MemFree", 0)) / max(info.get("MemTotal", 1), 1)) * 100,
            1
        ),
    }


def is_ollama_running():
    """Prueft ob Ollama bereits laeuft."""
    try:
        result = subprocess.run(
            ["pgrep", "-x", "ollama"],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def is_ollama_installed():
    """Prueft ob Ollama installiert ist."""
    try:
        result = subprocess.run(
            ["which", "ollama"],
            capture_output=True, timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def select_best_model(available_ram_mb):
    """Waehlt das beste Modell basierend auf verfuegbarem RAM."""
    usable_ram = available_ram_mb - RAM_RESERVE_MB

    for model in MODELS:
        if model["ram_mb"] <= usable_ram:
            return model

    return None


def check_model_installed(model_name):
    """Prueft ob ein Modell bereits installiert ist."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10,
        )
        return model_name.split(":")[0] in result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def start_ollama_server():
    """Startet den Ollama Server im Hintergrund."""
    env = os.environ.copy()
    env["OLLAMA_NUM_PARALLEL"] = "1"
    env["OLLAMA_NUM_THREAD"] = "2"

    print("  Starting Ollama server...")
    subprocess.Popen(
        ["ollama", "serve"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)
    print("  Ollama server gestartet.")


def pull_model(model_name):
    """Zieht ein Modell falls nicht vorhanden."""
    print(f"  Pulling {model_name}...")
    try:
        subprocess.run(
            ["ollama", "pull", model_name],
            timeout=600,  # 10 min timeout
        )
        return True
    except subprocess.SubprocessError as e:
        print(f"  Pull fehlgeschlagen: {e}")
        return False


def show_status():
    """Zeigt System- und Ollama-Status."""
    mem = get_memory_info()
    if not mem:
        print("  Konnte RAM-Info nicht lesen.")
        return

    installed = is_ollama_installed()
    running = is_ollama_running()

    print(f"\n  SMART OLLAMA STATUS")
    print(f"  {'=' * 40}")
    print(f"  RAM Total:     {mem['total_mb']} MB")
    print(f"  RAM Available: {mem['available_mb']} MB")
    print(f"  RAM Used:      {mem['used_mb']} MB ({mem['percent']}%)")
    print(f"  Ollama:        {'Installed' if installed else 'NOT INSTALLED'}")
    print(f"  Server:        {'Running' if running else 'Stopped'}")

    best = select_best_model(mem["available_mb"])
    if best:
        print(f"\n  Empfohlenes Modell: {best['name']}")
        print(f"    RAM-Bedarf: {best['ram_mb']} MB")
        print(f"    {best['desc']}")
    else:
        print(f"\n  WARNUNG: Nicht genug RAM fuer Ollama ({mem['available_mb']} MB frei)")
        print(f"  Mindestens {MODELS[0]['ram_mb'] + RAM_RESERVE_MB} MB benoetigt.")

    print(f"\n  Verfuegbare Modelle:")
    for m in MODELS:
        fits = "OK" if m["ram_mb"] + RAM_RESERVE_MB <= mem["available_mb"] else "zu gross"
        print(f"    {m['name']:20s} {m['ram_mb']:5d} MB  [{fits:>8s}]  {m['desc']}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Smart Ollama Launcher")
    parser.add_argument("--model", type=str, help="Spezifisches Modell starten")
    parser.add_argument("--status", action="store_true", help="Nur Status zeigen")
    parser.add_argument("--pull-only", action="store_true", help="Nur Modell ziehen")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    # Check RAM
    mem = get_memory_info()
    if not mem:
        print("ERROR: Konnte RAM-Info nicht lesen.")
        sys.exit(1)

    print(f"\n  RAM: {mem['available_mb']} MB frei von {mem['total_mb']} MB ({mem['percent']}%)")

    # Check Ollama
    if not is_ollama_installed():
        print("  ERROR: Ollama ist nicht installiert.")
        print("  Install: curl -fsSL https://ollama.com/install.sh | sh")
        sys.exit(1)

    # Check RAM
    if mem["available_mb"] < MIN_FREE_RAM_MB:
        print(f"  ERROR: Nicht genug RAM ({mem['available_mb']} MB < {MIN_FREE_RAM_MB} MB minimum)")
        sys.exit(1)

    # Select model
    if args.model:
        model = next((m for m in MODELS if args.model in m["name"]), None)
        if not model:
            model = {"name": args.model, "ram_mb": 0, "desc": "Custom"}
    else:
        model = select_best_model(mem["available_mb"])

    if not model:
        print(f"  ERROR: Kein Modell passt in {mem['available_mb']} MB RAM")
        show_status()
        sys.exit(1)

    print(f"  Modell: {model['name']} ({model['ram_mb']} MB)")

    # Start server if needed
    if not is_ollama_running():
        start_ollama_server()

    # Pull model if needed
    if not check_model_installed(model["name"]):
        if not pull_model(model["name"]):
            sys.exit(1)

    if args.pull_only:
        print("  Modell bereit.")
        return

    # Test inference
    print(f"\n  Testing {model['name']}...")
    try:
        result = subprocess.run(
            ["ollama", "run", model["name"], "Say 'Hello' in one word."],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            print(f"  Response: {result.stdout.strip()[:100]}")
            print(f"\n  Ollama laeuft mit {model['name']}")
        else:
            print(f"  ERROR: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("  TIMEOUT: Modell reagiert nicht (RAM zu knapp?)")
    except subprocess.SubprocessError as e:
        print(f"  ERROR: {e}")


if __name__ == "__main__":
    main()
