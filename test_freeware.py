#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  FREEWARE TEST — 100% Kostenlos, 100% Lokal                    ║
║  ═══════════════════════════════════════════                    ║
║  Testet das komplette AI Empire System NUR mit Ollama.          ║
║  Keine API Keys noetig. Keine Cloud. Keine Kosten.              ║
║                                                                  ║
║  VORAUSSETZUNG: Ollama muss laufen!                             ║
║    → ollama serve                                                ║
║    → ollama pull qwen2.5-coder:7b                               ║
║                                                                  ║
║  AUSFUEHREN:                                                     ║
║    python3 test_freeware.py                                      ║
║                                                                  ║
║  WAS WIRD GETESTET:                                              ║
║    1. Ollama Verbindung                                          ║
║    2. Model verfuegbar                                           ║
║    3. AI Query (Frage stellen)                                   ║
║    4. Provider Chain (Fallback)                                   ║
║    5. Agent Orchestrator (Multi-Agent)                            ║
║    6. Knowledge Store (Speichern + Suchen)                       ║
║    7. Empire Boot (Status Dashboard)                             ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Force freeware mode
os.environ["OFFLINE_MODE"] = "false"  # We want to test Ollama, not skip it
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")

# Colors
G = "\033[92m"  # Green
R = "\033[91m"  # Red
Y = "\033[93m"  # Yellow
C = "\033[96m"  # Cyan
B = "\033[1m"   # Bold
D = "\033[2m"   # Dim
X = "\033[0m"   # Reset

passed = 0
failed = 0
total = 0


def test(name: str, ok: bool, detail: str = ""):
    """Log a test result."""
    global passed, failed, total
    total += 1
    if ok:
        passed += 1
        print(f"  {G}✓{X} {name} {D}{detail}{X}")
    else:
        failed += 1
        print(f"  {R}✗{X} {name} {D}{detail}{X}")


async def main():
    global passed, failed

    print(f"""
{B}{C}╔══════════════════════════════════════════════════════╗
║     AI EMPIRE — FREEWARE TEST SUITE                  ║
║     100% Lokal • 100% Kostenlos • Ollama Only        ║
╚══════════════════════════════════════════════════════╝{X}
""")

    # ═══════════════════════════════════════════════════════
    # TEST 1: Ollama Connection
    # ═══════════════════════════════════════════════════════
    print(f"\n{B}[1/7] OLLAMA VERBINDUNG{X}")

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_ok = False
    models = []

    try:
        import httpx
        r = httpx.get(f"{ollama_url}/api/tags", timeout=5)
        ollama_ok = r.status_code == 200
        if ollama_ok:
            models = [m["name"] for m in r.json().get("models", [])]
        test("Ollama erreichbar", ollama_ok, f"auf {ollama_url}")
        test("Models geladen", len(models) > 0, f"{len(models)} models")
    except Exception as e:
        test("Ollama erreichbar", False, str(e))
        print(f"\n  {R}{B}STOP:{X} Ollama laeuft nicht!")
        print(f"  {Y}Starte Ollama:{X}")
        print(f"    1. ollama serve")
        print(f"    2. ollama pull qwen2.5-coder:7b")
        print(f"    3. python3 test_freeware.py")
        return

    if not ollama_ok:
        print(f"\n  {R}Ollama nicht erreichbar. Bitte starten:{X}")
        print(f"    ollama serve && ollama pull qwen2.5-coder:7b")
        return

    # ═══════════════════════════════════════════════════════
    # TEST 2: Model Check
    # ═══════════════════════════════════════════════════════
    print(f"\n{B}[2/7] MODELS CHECK{X}")

    preferred = ["qwen2.5-coder:7b", "qwen2.5-coder:14b", "llama3.2:latest",
                 "deepseek-r1:7b", "codellama:7b"]

    found_model = None
    for m in preferred:
        exists = any(m in model_name for model_name in models)
        test(f"Model: {m}", exists, "installiert" if exists else "nicht installiert")
        if exists and not found_model:
            found_model = m

    if not found_model and models:
        found_model = models[0]
        print(f"  {Y}→ Nutze erstes verfuegbares Model: {found_model}{X}")

    if not found_model:
        print(f"\n  {R}Kein Model gefunden! Installiere eins:{X}")
        print(f"    ollama pull qwen2.5-coder:7b")
        return

    # ═══════════════════════════════════════════════════════
    # TEST 3: AI Query (Direkte Ollama-Abfrage)
    # ═══════════════════════════════════════════════════════
    print(f"\n{B}[3/7] AI QUERY (Ollama direkt){X}")

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": found_model,
                    "prompt": "Sage nur das Wort 'Empire' und nichts anderes.",
                    "stream": False,
                }
            )
            elapsed = time.time() - start
            data = r.json()
            response = data.get("response", "").strip()

        test("Ollama antwortet", bool(response), f"in {elapsed:.1f}s")
        test("Antwort erhalten", len(response) > 0, f'"{response[:80]}"')
    except Exception as e:
        test("Ollama antwortet", False, str(e))

    # ═══════════════════════════════════════════════════════
    # TEST 4: Provider Chain
    # ═══════════════════════════════════════════════════════
    print(f"\n{B}[4/7] PROVIDER CHAIN (Smart Routing){X}")

    try:
        from antigravity.provider_chain import ProviderChain
        chain = ProviderChain()
        test("Provider Chain importiert", True)

        # Health check
        health = await chain.health_check()
        test("Health Check", True, str({k: v["available"] for k, v in health.items()}))

        # Query through chain (should route to Ollama)
        start = time.time()
        result = await chain.query(
            prompt="Nenne 3 Vorteile von AI Automation. Kurz und knapp.",
            prefer="ollama"
        )
        elapsed = time.time() - start
        test("Chain Query", result.get("success", False),
             f'{result.get("provider")} in {elapsed:.1f}s')
        if result.get("content"):
            print(f"    {D}→ {result['content'][:120]}...{X}")

    except Exception as e:
        test("Provider Chain", False, str(e))

    # ═══════════════════════════════════════════════════════
    # TEST 5: Agent Orchestrator
    # ═══════════════════════════════════════════════════════
    print(f"\n{B}[5/7] AGENT ORCHESTRATOR{X}")

    try:
        from antigravity.agent_orchestrator import Orchestrator
        orch = Orchestrator(prefer_provider="ollama")
        test("Orchestrator importiert", True)

        # Run scanner agent
        start = time.time()
        result = await orch.run("scanner", "Nenne 2 aktuelle AI Trends. Kurz.")
        elapsed = time.time() - start
        test("Scanner Agent", result.get("success", False),
             f'{result.get("provider")} in {elapsed:.1f}s')

        # Run producer agent
        start = time.time()
        result = await orch.run("producer", "Erstelle 1 kurzen X-Post ueber AI Agents.")
        elapsed = time.time() - start
        test("Producer Agent", result.get("success", False),
             f'{result.get("provider")} in {elapsed:.1f}s')

    except Exception as e:
        test("Agent Orchestrator", False, str(e))

    # ═══════════════════════════════════════════════════════
    # TEST 6: Knowledge Store
    # ═══════════════════════════════════════════════════════
    print(f"\n{B}[6/7] KNOWLEDGE STORE{X}")

    try:
        from antigravity.knowledge_store import KnowledgeStore
        ks = KnowledgeStore()
        test("Knowledge Store importiert", True)

        # Add knowledge
        ks.add("test", "Freeware Test",
               content="Das Freeware-System laeuft 100% mit Ollama",
               tags=["test", "freeware"])
        test("Wissen gespeichert", True)

        # Search
        results = ks.search("freeware")
        test("Wissen gefunden", len(results) > 0, f"{len(results)} Treffer")

    except Exception as e:
        test("Knowledge Store", False, str(e))

    # ═══════════════════════════════════════════════════════
    # TEST 7: Empire Boot (Import Test)
    # ═══════════════════════════════════════════════════════
    print(f"\n{B}[7/7] EMPIRE BOOT SYSTEM{X}")

    try:
        # Test imports
        from empire_boot import check_ollama, check_api_keys, check_port
        test("empire_boot.py importiert", True)

        ollama_status = check_ollama()
        test("Ollama Status Check", ollama_status["available"],
             f'{ollama_status["count"]} models')

        keys = check_api_keys()
        test("API Keys Check", True,
             f'{sum(1 for v in keys.values() if v)} konfiguriert')

    except Exception as e:
        test("Empire Boot", False, str(e))

    # ═══════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════
    print(f"""
{B}{'═' * 54}
  ERGEBNIS: {G if failed == 0 else Y}{passed}/{total} Tests bestanden{X}{B}
{'═' * 54}{X}
""")

    if failed == 0:
        print(f"""  {G}{B}ALLES FUNKTIONIERT!{X}

  {C}Dein System laeuft 100% kostenlos mit Ollama.{X}
  Keine API Keys noetig. Keine Cloud-Kosten.

  {B}Naechste Schritte:{X}
    {C}python3 empire_boot.py{X}           → System Dashboard
    {C}python3 empire_boot.py ask "..."{X}  → AI fragen (kostenlos)
    {C}python3 empire_engine.py auto{X}     → Autonomer Zyklus
    {C}python3 -m antigravity.agent_orchestrator auto{X} → Agent Swarm
""")
    else:
        print(f"""  {Y}{failed} Tests fehlgeschlagen.{X}

  {B}Quick Fix:{X}
    1. {C}ollama serve{X}                  → Ollama starten
    2. {C}ollama pull qwen2.5-coder:7b{X}  → Model installieren
    3. {C}python3 test_freeware.py{X}       → Nochmal testen
""")


if __name__ == "__main__":
    asyncio.run(main())
