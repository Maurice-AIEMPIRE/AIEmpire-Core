#!/usr/bin/env python3
"""
EMPIRE NERVE - Zentrales Nervensystem
======================================
Verbindet ALLES mit ALLEM. Jedes System profitiert von jedem anderen.

Architektur:
  [Mission Control] <-> [Geldmaschine] <-> [Revenue Pipeline]
         |                    |                    |
  [Workflow System] <-> [Lead Machine] <-> [Kimi Swarm]
         |                    |                    |
  [Atomic Reactor] <-> [n8n Cloud]   <-> [Ollama]

Jedes System:
- Kann Daten von jedem anderen lesen
- Kann Aufgaben an jedes andere delegieren
- Profitiert von den Ergebnissen aller anderen

Usage:
  python empire_nerve.py pulse     # Heartbeat: alle Systeme pruefen
  python empire_nerve.py flow      # Ein Durchlauf: alles ausfuehren
  python empire_nerve.py nerve     # Continuous: alle 30 min
  python empire_nerve.py map       # Zeige Verbindungen
"""

import asyncio
import aiohttp
import json
import os
import sys
import importlib
import importlib.util
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "nerve"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = "http://localhost:11434"
N8N_LOCAL = "http://localhost:5678"
N8N_CLOUD = "https://ai1337empire.app.n8n.cloud"


# === SYSTEM REGISTRY ===
# Jedes System registriert sich hier mit seinen Faehigkeiten

SYSTEMS = {
    "ollama": {
        "name": "Ollama (Local AI)",
        "check": lambda: check_http(f"{OLLAMA_URL}/api/tags"),
        "provides": ["content_generation", "text_analysis", "summarization"],
        "consumes": ["prompts", "context"],
    },
    "n8n_local": {
        "name": "n8n Local",
        "check": lambda: check_http(f"{N8N_LOCAL}/healthz"),
        "provides": ["workflow_execution", "webhooks", "scheduling"],
        "consumes": ["triggers", "data"],
    },
    "n8n_cloud": {
        "name": "n8n Cloud",
        "check": lambda: check_http(N8N_CLOUD),
        "provides": ["cloud_workflows", "webhooks", "24_7_execution"],
        "consumes": ["triggers", "data"],
    },
    "mission_control": {
        "name": "Mission Control",
        "module": "mission_control",
        "provides": ["task_scanning", "prioritization", "blocker_detection"],
        "consumes": ["system_status"],
    },
    "geldmaschine": {
        "name": "Geldmaschine",
        "script": BASE_DIR / "scripts" / "geldmaschine.py",
        "provides": ["post_generation", "revenue_tracking", "sales_pipeline"],
        "consumes": ["content", "products", "analytics"],
    },
    "revenue_pipeline": {
        "name": "Revenue Pipeline",
        "script": BASE_DIR / "scripts" / "revenue_pipeline.py",
        "provides": ["revenue_dashboard", "funnel_tracking", "launch_sequence"],
        "consumes": ["sales_data", "content"],
    },
    "sales_machine": {
        "name": "Sales Machine",
        "script": BASE_DIR / "scripts" / "sales_machine.py",
        "provides": ["inventory", "content_blast", "asset_tracking"],
        "consumes": ["products", "analytics"],
    },
    "workflow_system": {
        "name": "Empire Workflow (5-Step)",
        "script": BASE_DIR / "workflow-system" / "empire.py",
        "provides": ["audit", "architecture", "analysis", "refinement", "compounding"],
        "consumes": ["context", "patterns"],
    },
    "lead_machine": {
        "name": "X Lead Machine",
        "path": BASE_DIR / "x-lead-machine",
        "provides": ["social_posts", "viral_replies", "weekly_plans"],
        "consumes": ["trends", "products"],
    },
    "atomic_reactor": {
        "name": "Atomic Reactor",
        "path": BASE_DIR / "atomic-reactor",
        "provides": ["task_execution", "research", "competitor_analysis"],
        "consumes": ["task_definitions", "api_keys"],
    },
    "kimi_swarm": {
        "name": "Kimi Swarm (100K Agents)",
        "path": BASE_DIR / "kimi-swarm",
        "provides": ["mass_content", "lead_mining", "research_at_scale"],
        "consumes": ["api_key", "task_configs"],
    },
}


async def check_http(url):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                return r.status in (200, 301, 302, 404)
    except Exception:
        return False


async def check_path(path):
    return Path(path).exists()


def load_module(name, path):
    """Dynamisch ein Python-Modul laden."""
    try:
        spec = importlib.util.spec_from_file_location(name, str(path))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    except Exception:
        pass
    return None


async def generate_via_ollama(prompt, system="You are a helpful assistant."):
    """Ollama als zentralen Content-Generator nutzen."""
    try:
        payload = {
            "model": "qwen2.5-coder:7b",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{OLLAMA_URL}/api/chat", json=payload,
                              timeout=aiohttp.ClientTimeout(total=120)) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["message"]["content"]
    except Exception:
        pass
    return None


# === PULSE: Heartbeat aller Systeme ===

async def pulse():
    print("=" * 60)
    print("  EMPIRE NERVE - SYSTEM PULSE")
    print("=" * 60)

    results = {}
    online = 0
    total = 0

    for key, sys_info in SYSTEMS.items():
        total += 1
        status = False

        if "check" in sys_info:
            status = await sys_info["check"]()
        elif "script" in sys_info:
            status = Path(sys_info["script"]).exists()
        elif "path" in sys_info:
            status = Path(sys_info["path"]).exists()
        elif "module" in sys_info:
            status = (BASE_DIR / f"{sys_info['module']}.py").exists()

        if status:
            online += 1
        results[key] = status

        icon = "ON " if status else "OFF"
        provides = ", ".join(sys_info.get("provides", [])[:3])
        print(f"  [{icon}] {sys_info['name']:30s} -> {provides}")

    print(f"\n  {online}/{total} Systeme online")

    # Verbindungsmatrix
    print(f"\n  DATENFLUSS:")
    for key, sys_info in SYSTEMS.items():
        if results.get(key):
            for cap in sys_info.get("provides", []):
                # Finde wer das konsumiert
                consumers = []
                for k2, s2 in SYSTEMS.items():
                    if k2 != key and cap in s2.get("consumes", []):
                        consumers.append(s2["name"])
                if consumers:
                    print(f"    {sys_info['name']:20s} --[{cap}]--> {', '.join(consumers)}")

    # Speichere Pulse
    pulse_file = DATA_DIR / f"pulse_{date.today().isoformat()}.json"
    pulse_data = {
        "timestamp": datetime.now().isoformat(),
        "online": online,
        "total": total,
        "systems": {k: {"status": v, "name": SYSTEMS[k]["name"]} for k, v in results.items()},
    }
    pulse_file.write_text(json.dumps(pulse_data, indent=2))

    return results


# === FLOW: Ein kompletter Durchlauf ===

async def flow():
    print("=" * 60)
    print("  EMPIRE NERVE - FULL FLOW")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = await pulse()
    flow_results = {"timestamp": datetime.now().isoformat(), "stages": []}

    # Stage 1: Mission Control Scan
    print(f"\n{'─' * 60}")
    print("  STAGE 1: Mission Control Scan")
    print(f"{'─' * 60}")
    try:
        mc_path = BASE_DIR / "mission_control.py"
        if mc_path.exists():
            sys.path.insert(0, str(BASE_DIR))
            from mission_control import MissionControl
            mc = MissionControl(str(BASE_DIR))
            await mc.scan_all_sources()
            tasks_found = len(mc.tasks)
            blockers = len(mc.get_top_blockers())
            dashboard = mc.generate_dashboard()
            mc.export_to_json()
            print(f"    Tasks: {tasks_found} | Blockers: {blockers}")
            flow_results["stages"].append({"name": "mission_control", "tasks": tasks_found, "blockers": blockers})
        else:
            print("    SKIP: mission_control.py not found")
    except Exception as e:
        print(f"    ERROR: {e}")

    # Stage 2: Revenue Pipeline Check
    print(f"\n{'─' * 60}")
    print("  STAGE 2: Revenue Pipeline")
    print(f"{'─' * 60}")
    try:
        rev_file = DATA_DIR.parent / "geldmaschine" / "revenue.json"
        if rev_file.exists():
            rev = json.loads(rev_file.read_text())
            today = date.today().isoformat()
            today_rev = sum(s["amount"] for s in rev.get("sales", []) if s.get("date") == today)
            total_rev = sum(s["amount"] for s in rev.get("sales", []))
            print(f"    Heute: EUR {today_rev:.2f} / 180 Ziel")
            print(f"    Gesamt: EUR {total_rev:.2f}")
            flow_results["stages"].append({"name": "revenue", "today": today_rev, "total": total_rev})
        else:
            print(f"    Noch kein Revenue getrackt (EUR 0)")
            flow_results["stages"].append({"name": "revenue", "today": 0, "total": 0})
    except Exception as e:
        print(f"    ERROR: {e}")

    # Stage 3: Content Generation via Ollama
    print(f"\n{'─' * 60}")
    print("  STAGE 3: Content Generation (Ollama)")
    print(f"{'─' * 60}")
    if results.get("ollama"):
        posts_dir = DATA_DIR.parent / "geldmaschine" / "posts"
        posts_dir.mkdir(parents=True, exist_ok=True)
        today_file = posts_dir / f"posts_{date.today().isoformat()}.json"
        existing = json.loads(today_file.read_text()) if today_file.exists() else []

        if len(existing) < 10:
            prompt = (
                "Generate 3 short Twitter posts to sell the 'AI Prompt Vault' (EUR 27, 127 prompts). "
                "Each post should be under 280 chars, include a CTA and [LINK] placeholder. "
                "Return ONLY the 3 posts separated by ---"
            )
            content = await generate_via_ollama(prompt)
            if content:
                new_posts = []
                for chunk in content.split("---"):
                    chunk = chunk.strip()
                    if chunk and len(chunk) > 20:
                        new_posts.append({
                            "platform": "twitter",
                            "product": "AI Prompt Vault",
                            "text": chunk,
                            "generated": datetime.now().isoformat(),
                            "source": "empire_nerve",
                        })
                existing.extend(new_posts)
                today_file.write_text(json.dumps(existing, indent=2))
                print(f"    Generated {len(new_posts)} new posts ({len(existing)} total today)")
                flow_results["stages"].append({"name": "content", "new": len(new_posts), "total": len(existing)})
            else:
                print("    Ollama returned no content")
        else:
            print(f"    Already {len(existing)} posts today - skipping generation")
            flow_results["stages"].append({"name": "content", "new": 0, "total": len(existing)})
    else:
        print("    SKIP: Ollama offline")

    # Stage 4: Workflow System State
    print(f"\n{'─' * 60}")
    print("  STAGE 4: Workflow System")
    print(f"{'─' * 60}")
    state_file = BASE_DIR / "workflow-system" / "state" / "current_state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text())
        cycle = state.get("cycle", 0)
        steps_done = len(state.get("steps", {}))
        print(f"    Cycle: #{cycle} | Steps completed: {steps_done}/5")
        flow_results["stages"].append({"name": "workflow", "cycle": cycle, "steps": steps_done})
    else:
        print("    No workflow state yet - run: python empire.py workflow")
        flow_results["stages"].append({"name": "workflow", "cycle": 0, "steps": 0})

    # Stage 5: Asset Inventory
    print(f"\n{'─' * 60}")
    print("  STAGE 5: Asset Inventory")
    print(f"{'─' * 60}")
    asset_dirs = {
        "Gumroad Products": Path.home() / ".openclaw/workspace/ai-empire/04_OUTPUT/GUMROAD_PRODUCTS",
        "Gold Nuggets": BASE_DIR / "gold-nuggets",
        "N8N Workflows": BASE_DIR / "n8n-workflows",
        "X-Lead Posts": BASE_DIR / "x-lead-machine",
        "Scripts": BASE_DIR / "scripts",
    }
    total_assets = 0
    for name, path in asset_dirs.items():
        count = len(list(path.glob("*"))) if path.exists() else 0
        total_assets += count
        print(f"    {name:20s}: {count:3d} files")
    print(f"    {'TOTAL':20s}: {total_assets:3d} assets")
    flow_results["stages"].append({"name": "assets", "total": total_assets})

    # Stage 6: n8n Cloud Connection
    print(f"\n{'─' * 60}")
    print("  STAGE 6: n8n Cloud")
    print(f"{'─' * 60}")
    if results.get("n8n_cloud"):
        print(f"    ONLINE: {N8N_CLOUD}")
        print(f"    Webhook ready for content automation")
        flow_results["stages"].append({"name": "n8n_cloud", "status": "online"})
    else:
        print(f"    OFFLINE: {N8N_CLOUD}")
        flow_results["stages"].append({"name": "n8n_cloud", "status": "offline"})

    # Summary
    print(f"\n{'=' * 60}")
    print("  FLOW COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Systems online: {sum(1 for v in results.values() if v)}/{len(results)}")
    print(f"  Stages run: {len(flow_results['stages'])}")
    print(f"  Total assets: {total_assets}")

    # Next actions
    print(f"\n  NEXT ACTIONS:")
    if not any(True for f in (DATA_DIR.parent / "geldmaschine" / "posts").glob("*.json") if f.exists()):
        print("    [!] Run: python geldmaschine.py run")
    rev_file = DATA_DIR.parent / "geldmaschine" / "revenue.json"
    if not rev_file.exists() or sum(s["amount"] for s in json.loads(rev_file.read_text()).get("sales", [])) == 0:
        print("    [!] Kein Revenue - Gumroad Account + Posts absetzen!")
    print("    [>] Naechster Flow: python empire_nerve.py flow")
    print("    [>] Continuous: python empire_nerve.py nerve")

    # Save flow results
    flow_file = DATA_DIR / f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    flow_file.write_text(json.dumps(flow_results, indent=2))

    return flow_results


# === MAP: Zeige Verbindungen ===

async def show_map():
    print("=" * 60)
    print("  EMPIRE NERVE - SYSTEM MAP")
    print("=" * 60)

    print("""
  ┌─────────────────────────────────────────────────────────┐
  │                    EMPIRE NERVE                         │
  │               (Zentrales Nervensystem)                  │
  └─────────┬───────────┬───────────┬───────────┬───────────┘
            │           │           │           │
  ┌─────────▼──┐ ┌──────▼─────┐ ┌──▼────────┐ ┌▼──────────┐
  │  Mission   │ │ Geldma-    │ │ Revenue   │ │ Sales     │
  │  Control   │ │ schine     │ │ Pipeline  │ │ Machine   │
  │            │ │            │ │           │ │           │
  │ Scannt     │ │ Generiert  │ │ Trackt    │ │ Inventory │
  │ Tasks      │ │ Posts      │ │ Revenue   │ │ + Blast   │
  └─────┬──────┘ └──────┬─────┘ └─────┬─────┘ └─────┬─────┘
        │               │             │              │
  ┌─────▼──────────────▼─────────────▼──────────────▼─────┐
  │                    OLLAMA (Lokal, 0 EUR)                │
  │      qwen2.5-coder:7b | deepseek-r1:8b | glm-4.7      │
  └─────┬──────────────┬─────────────┬──────────────┬─────┘
        │              │             │              │
  ┌─────▼──────┐ ┌─────▼─────┐ ┌────▼───────┐ ┌───▼──────┐
  │ Workflow   │ │ X-Lead    │ │ Atomic     │ │ Kimi     │
  │ System     │ │ Machine   │ │ Reactor    │ │ Swarm    │
  │ (5-Step)   │ │ (Posts)   │ │ (Tasks)    │ │ (100K)   │
  └────────────┘ └───────────┘ └────────────┘ └──────────┘
        │              │             │              │
  ┌─────▼──────────────▼─────────────▼──────────────▼─────┐
  │              n8n Cloud (ai1337empire)                   │
  │          Webhooks + Scheduling + Automation             │
  └───────────────────────────────────────────────────────┘
            │
  ┌─────────▼─────────────────────────────────────────────┐
  │                    GUMROAD                             │
  │   AI Prompt Vault (27) | Docker Guide (99) | SaaS     │
  │              EUR 180/Tag = EUR 5,400/Monat             │
  └───────────────────────────────────────────────────────┘
  """)

    # Show data flows
    print("  DATENFLUESSE:")
    print("    Ollama → Geldmaschine → Posts → n8n Cloud → Social Media → Revenue")
    print("    Mission Control → Blocker → Workflow System → Fixes → Improvement")
    print("    X-Lead Machine → Posts → Geldmaschine → Queue → Scheduling")
    print("    Atomic Reactor → Research → Gold Nuggets → Products → Revenue")
    print("    Kimi Swarm → Mass Content → Lead Mining → CRM → Sales")
    print("    Revenue Pipeline → Tracking → Dashboard → Decisions → Strategy")
    print()
    print("  PROFIT-KREISLAUF:")
    print("    Content (Ollama) → Posts (Geldmaschine) → Sales (Gumroad)")
    print("    Sales → Revenue → Invest → More Content → More Sales")
    print("    Jeder EUR reinvestiert in Automation = Compound Growth")


# === NERVE: Continuous Mode ===

async def nerve():
    print("  EMPIRE NERVE - CONTINUOUS MODE (alle 30 min)")
    print("  Ctrl+C zum Stoppen")
    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'=' * 60}")
        print(f"  NERVE CYCLE #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
        try:
            await flow()
        except Exception as e:
            print(f"  ERROR: {e}")
        print(f"\n  Naechster Cycle in 30 Minuten...")
        await asyncio.sleep(1800)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    if cmd == "pulse":
        asyncio.run(pulse())
    elif cmd == "flow":
        asyncio.run(flow())
    elif cmd == "nerve":
        asyncio.run(nerve())
    elif cmd == "map":
        asyncio.run(show_map())
    else:
        print(f"  Unknown: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
