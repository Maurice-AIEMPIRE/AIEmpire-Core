#!/usr/bin/env python3
"""
SMART OLLAMA LAUNCH - Startet Ollama mit RAM-Schutz.
Checkt verfuegbaren Speicher und waehlt das passende Modell.

RAM-Modell-Matrix:
    < 4GB  → phi:q4 (kleinst moeglich)
    4-8GB  → qwen2.5-coder:3b
    8-16GB → qwen2.5-coder:7b (Standard)
    > 16GB → deepseek-r1:8b oder groesser

Usage:
    python smart_ollama_launch.py          # Auto-detect + Launch
    python smart_ollama_launch.py --check  # Nur Status anzeigen
"""

import os
import sys
import shutil
import subprocess
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "workflow-system"))


def get_ram_info() -> dict:
    """Liest RAM-Informationen."""
    try:
        with open("/proc/meminfo") as f:
            info = {}
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = int(parts[1].strip().split()[0])  # kB
                    info[key] = val

            total_mb = info.get("MemTotal", 0) // 1024
            available_mb = info.get("MemAvailable", 0) // 1024
            used_mb = total_mb - available_mb
            pct = round(used_mb / max(total_mb, 1) * 100, 1)

            return {
                "total_mb": total_mb,
                "available_mb": available_mb,
                "used_mb": used_mb,
                "usage_pct": pct,
            }
    except (FileNotFoundError, ValueError):
        return {"total_mb": 0, "available_mb": 0, "used_mb": 0, "usage_pct": 0}


def select_model(available_mb: int) -> str:
    """Waehlt Modell basierend auf verfuegbarem RAM."""
    if available_mb < 4000:
        return "phi:q4"
    elif available_mb < 8000:
        return "qwen2.5-coder:3b"
    elif available_mb < 16000:
        return "qwen2.5-coder:7b"
    else:
        return "deepseek-r1:8b"


def is_ollama_running() -> bool:
    """Prueft ob Ollama Server laeuft."""
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def get_ollama_models() -> list:
    """Listet installierte Ollama Modelle."""
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


async def test_model(model: str) -> bool:
    """Testet ob ein Modell funktioniert."""
    try:
        from ollama_engine import OllamaEngine
        engine = OllamaEngine(model=model)
        resp = await engine.chat(
            [{"role": "user", "content": "Sage 'OK' und nichts anderes."}],
            max_tokens=10,
        )
        return resp.success
    except Exception as e:
        print(f"  Test fehlgeschlagen: {e}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Smart Ollama Launch")
    parser.add_argument("--check", action="store_true", help="Nur Status anzeigen")
    args = parser.parse_args()

    print("=" * 50)
    print("  SMART OLLAMA LAUNCH")
    print("=" * 50)

    # RAM Check
    ram = get_ram_info()
    print(f"\n  RAM Status:")
    print(f"    Total:     {ram['total_mb']:,} MB")
    print(f"    Available: {ram['available_mb']:,} MB")
    print(f"    Used:      {ram['used_mb']:,} MB ({ram['usage_pct']}%)")

    # Modell-Empfehlung
    recommended = select_model(ram["available_mb"])
    print(f"\n  Empfohlenes Modell: {recommended}")

    # Ollama Status
    running = is_ollama_running()
    print(f"\n  Ollama Server: {'RUNNING' if running else 'OFFLINE'}")

    if running:
        models = get_ollama_models()
        print(f"  Installierte Modelle: {', '.join(models) if models else 'keine'}")

        if recommended in models:
            print(f"\n  {recommended} ist installiert!")
            if not args.check:
                print(f"  Teste {recommended}...")
                success = asyncio.run(test_model(recommended))
                if success:
                    print(f"  Test: OK - {recommended} funktioniert!")

                    # OLLAMA_MODEL env var setzen
                    print(f"\n  Empfehlung: export OLLAMA_MODEL='{recommended}'")
                else:
                    print(f"  Test: FEHLGESCHLAGEN")
        else:
            print(f"\n  {recommended} nicht installiert.")
            print(f"  Installation: ollama pull {recommended}")
    else:
        ollama_bin = shutil.which("ollama")
        if ollama_bin:
            print(f"  Ollama binary: {ollama_bin}")
            if not args.check:
                print(f"\n  Starte Ollama Server...")
                print(f"  Befehl: ollama serve &")
                print(f"  Dann: ollama pull {recommended}")
        else:
            print(f"  Ollama binary: NICHT GEFUNDEN")
            print(f"\n  Installation:")
            print(f"    curl -fsSL https://ollama.com/install.sh | sh")

    # Env Vars
    print(f"\n  Environment Variables:")
    print(f"    OLLAMA_NUM_PARALLEL = {os.getenv('OLLAMA_NUM_PARALLEL', 'not set')}")
    print(f"    OLLAMA_NUM_THREAD   = {os.getenv('OLLAMA_NUM_THREAD', 'not set')}")
    print(f"    OLLAMA_MODEL        = {os.getenv('OLLAMA_MODEL', 'not set')}")
    print(f"    OLLAMA_HOST         = {os.getenv('OLLAMA_HOST', 'http://localhost:11434')}")

    print(f"\n{'='*50}")


if __name__ == "__main__":
    main()
