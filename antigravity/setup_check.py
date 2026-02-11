#!/usr/bin/env python3
"""
AIEmpire Setup Check
=====================
Diagnostiziert warum Agenten nicht laufen und zeigt genau was fehlt.

Usage:
    python antigravity/setup_check.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def check_env_var(name, secret=True):
    """Check if an env var is set and non-empty."""
    val = os.getenv(name, "")
    if not val:
        return False, "NOT SET"
    if secret:
        return True, f"SET ({len(val)} chars)"
    return True, val


def check_url(url, timeout=3):
    """Check if a URL is reachable."""
    try:
        import httpx
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url)
            return resp.status_code == 200, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)[:80]


def check_command(cmd, timeout=5):
    """Check if a command exists and runs."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip()[:80]
    except FileNotFoundError:
        return False, "NOT INSTALLED"
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"


def load_env_file():
    """Try to load .env file if it exists."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        loaded = 0
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                # Remove 'export ' prefix
                if line.startswith("export "):
                    line = line[7:]
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value and not os.getenv(key):
                    os.environ[key] = value
                    loaded += 1
        return loaded
    return -1  # No .env file


def main():
    print("=" * 60)
    print("  AIEMPIRE SETUP CHECK")
    print("=" * 60)
    print()

    # Try loading .env
    loaded = load_env_file()
    if loaded == -1:
        print("  [!] Keine .env Datei gefunden!")
        print("      cp .env.example .env && nano .env")
        print()
    elif loaded > 0:
        print(f"  [i] {loaded} Variablen aus .env geladen")
        print()

    all_ok = True
    has_any_provider = False

    # ─── Provider 1: Gemini ─────────────────────────────────
    print("  --- GEMINI (Cloud, schnell, smart) ---")
    gemini_ok, gemini_msg = check_env_var("GEMINI_API_KEY")
    icon = "OK" if gemini_ok else "!!"
    print(f"  [{icon}] GEMINI_API_KEY:      {gemini_msg}")

    gcp_ok, gcp_msg = check_env_var("GOOGLE_CLOUD_PROJECT", secret=False)
    icon = "OK" if gcp_ok else "--"
    print(f"  [{icon}] GOOGLE_CLOUD_PROJECT: {gcp_msg}")

    if gemini_ok:
        has_any_provider = True
        # Test actual connectivity
        from antigravity.gemini_client import GeminiClient
        client = GeminiClient()
        health = client.health_check()
        icon = "OK" if health else "!!"
        print(f"  [{icon}] Gemini API erreichbar: {health}")
    else:
        print("  [!!] KEIN GEMINI KEY!")
        print("       Kostenlos holen: https://aistudio.google.com/apikey")
        print("       Dann: echo 'export GEMINI_API_KEY=dein-key' >> .env && source .env")
    print()

    # ─── Provider 2: Ollama ─────────────────────────────────
    print("  --- OLLAMA (Lokal, kostenlos, offline) ---")
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_cmd_ok, ollama_ver = check_command(["ollama", "--version"])
    icon = "OK" if ollama_cmd_ok else "--"
    print(f"  [{icon}] ollama CLI:          {ollama_ver}")

    ollama_api_ok, ollama_api_msg = check_url(f"{ollama_url}/api/tags")
    icon = "OK" if ollama_api_ok else "!!"
    print(f"  [{icon}] Ollama API ({ollama_url}): {ollama_api_msg}")

    if ollama_api_ok:
        has_any_provider = True
        # Check models
        try:
            import httpx
            with httpx.Client(timeout=5) as c:
                resp = c.get(f"{ollama_url}/api/tags")
                models = resp.json().get("models", [])
                names = [m["name"] for m in models[:5]]
                print(f"  [OK] Modelle: {', '.join(names) if names else 'keine'}")
        except Exception:
            pass
    else:
        print("  [!!] Ollama nicht erreichbar!")
        print("       Starten: ollama serve")
        print("       Oder installieren: curl -fsSL https://ollama.ai/install.sh | sh")
    print()

    # ─── Provider 3: Moonshot/Kimi ──────────────────────────
    print("  --- MOONSHOT/KIMI (Cloud, Free Tier) ---")
    moon_ok, moon_msg = check_env_var("MOONSHOT_API_KEY")
    icon = "OK" if moon_ok else "--"
    print(f"  [{icon}] MOONSHOT_API_KEY:    {moon_msg}")
    if moon_ok:
        has_any_provider = True
    print()

    # ─── Summary ────────────────────────────────────────────
    print("=" * 60)
    if has_any_provider:
        print("  [OK] Mindestens 1 Provider verfuegbar!")
        print("       Agenten koennen laufen.")
    else:
        print("  [!!] KEIN PROVIDER VERFUEGBAR!")
        print()
        print("  SCHNELLSTE LOESUNG (30 Sekunden):")
        print("  1. Oeffne: https://aistudio.google.com/apikey")
        print("  2. Klick: 'Create API Key'")
        print("  3. Key kopieren")
        print("  4. Ausfuehren:")
        print()
        print("     cp .env.example .env")
        print("     # Key in .env eintragen bei GEMINI_API_KEY=")
        print("     source .env")
        print("     python antigravity/setup_check.py  # nochmal testen")
        print()
        print("  ODER Ollama starten (100% kostenlos + offline):")
        print("     curl -fsSL https://ollama.ai/install.sh | sh")
        print("     ollama serve &")
        print("     ollama pull phi:q4")
        all_ok = False

    print("=" * 60)
    return 0 if all_ok and has_any_provider else 1


if __name__ == "__main__":
    sys.exit(main())
