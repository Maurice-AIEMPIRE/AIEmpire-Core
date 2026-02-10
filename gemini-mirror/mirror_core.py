#!/usr/bin/env python3
"""
GEMINI MIRROR - Core Engine
Dual-Brain Architecture: Claude (Mac/Primary) <-> Gemini (Cloud/Mirror)

Both brains maintain independent state but sync bidirectionally.
Each brain can develop improvements independently, then merge the best
of both into the shared knowledge graph.

Usage:
  python mirror_core.py                    # Run one sync cycle
  python mirror_core.py --daemon           # Run continuously
  python mirror_core.py --status           # Show mirror state
  python mirror_core.py --init             # Initialize Gemini mirror
"""

import asyncio
import aiohttp
import argparse
import json
import os
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "workflow-system"))

from config import (
    PROJECT_ROOT, MIRROR_DIR, STATE_DIR, SYNC_QUEUE_DIR, OUTPUT_DIR,
    GEMINI_API_KEY, GEMINI_API_URL, GEMINI_MODEL, GEMINI_FLASH_MODEL,
    MOONSHOT_API_KEY, SYNC_CONFIG, MODEL_ROUTING,
)

# ── State Files ──────────────────────────────────────────────

MIRROR_STATE_FILE = STATE_DIR / "gemini_state.json"
SYNC_LOG_FILE = STATE_DIR / "sync_log.json"


def load_mirror_state() -> Dict:
    """Load the Gemini mirror state."""
    if MIRROR_STATE_FILE.exists():
        return json.loads(MIRROR_STATE_FILE.read_text())
    return {
        "created": datetime.now().isoformat(),
        "brain_id": "gemini_mirror",
        "partner_brain": "claude_primary",
        "total_sync_cycles": 0,
        "total_improvements_sent": 0,
        "total_improvements_received": 0,
        "last_sync": None,
        "gemini_capabilities": [],
        "active_experiments": [],
        "knowledge_delta": [],  # What Gemini knows that Claude doesn't (yet)
        "pending_merges": [],   # Improvements waiting to be merged to primary
        "evolution_log": [],    # How the mirror has evolved over time
    }


def save_mirror_state(state: Dict) -> None:
    state["updated"] = datetime.now().isoformat()
    MIRROR_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def load_sync_log() -> List[Dict]:
    if SYNC_LOG_FILE.exists():
        return json.loads(SYNC_LOG_FILE.read_text())
    return []


def append_sync_log(entry: Dict) -> None:
    log = load_sync_log()
    log.append({**entry, "timestamp": datetime.now().isoformat()})
    # Keep last 100 entries
    if len(log) > 100:
        log = log[-100:]
    SYNC_LOG_FILE.write_text(json.dumps(log, indent=2, ensure_ascii=False))


# ── Gemini API ───────────────────────────────────────────────

async def call_gemini(prompt: str, system_instruction: str = "",
                      model: str = None, temperature: float = 0.7,
                      max_tokens: int = 4096) -> str:
    """Call the Gemini API."""
    if not GEMINI_API_KEY:
        return "[ERROR] GEMINI_API_KEY not set. Set it with: export GEMINI_API_KEY=your_key"

    model = model or GEMINI_MODEL
    url = f"{GEMINI_API_URL}/models/{model}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                        return "[ERROR] Empty response from Gemini"
                    elif resp.status == 429:
                        wait = (2 ** attempt) + (time.time() % 1)
                        print(f"  Rate limited, waiting {wait:.1f}s...")
                        await asyncio.sleep(wait)
                    else:
                        error_text = await resp.text()
                        return f"[ERROR] Gemini API {resp.status}: {error_text[:200]}"
            except asyncio.TimeoutError:
                print(f"  Timeout on attempt {attempt + 1}/3")
            except Exception as e:
                return f"[ERROR] {str(e)}"

    return "[ERROR] All retry attempts failed"


async def call_gemini_flash(prompt: str, system_instruction: str = "") -> str:
    """Call Gemini Flash for fast/cheap operations."""
    return await call_gemini(
        prompt, system_instruction,
        model=GEMINI_FLASH_MODEL, temperature=0.5, max_tokens=2048
    )


# ── State Snapshot ───────────────────────────────────────────

def snapshot_primary_brain() -> Dict:
    """Take a snapshot of the Claude primary brain's state."""
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "brain": "claude_primary",
        "systems": {},
    }

    # Workflow state
    wf_state = PROJECT_ROOT / "workflow-system" / "state" / "current_state.json"
    if wf_state.exists():
        snapshot["systems"]["workflow"] = json.loads(wf_state.read_text())

    # Cowork state
    cw_state = PROJECT_ROOT / "workflow-system" / "state" / "cowork_state.json"
    if cw_state.exists():
        snapshot["systems"]["cowork"] = json.loads(cw_state.read_text())

    # Pattern library
    pl_file = PROJECT_ROOT / "workflow-system" / "state" / "pattern_library.json"
    if pl_file.exists():
        snapshot["systems"]["patterns"] = json.loads(pl_file.read_text())

    # Recent outputs
    output_dir = PROJECT_ROOT / "workflow-system" / "output"
    if output_dir.exists():
        files = sorted(output_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        snapshot["systems"]["recent_outputs"] = [f.name for f in files[:10]]

    # Swarm outputs
    swarm_dir = PROJECT_ROOT / "kimi-swarm" / "output_500k"
    if swarm_dir.exists():
        files = sorted(swarm_dir.iterdir(), key=lambda f: f.stat().st_mtime if f.is_file() else 0, reverse=True)
        snapshot["systems"]["swarm_outputs"] = [f.name for f in files[:10] if f.is_file()]

    return snapshot


def snapshot_gemini_brain() -> Dict:
    """Take a snapshot of the Gemini mirror brain's state."""
    state = load_mirror_state()
    return {
        "timestamp": datetime.now().isoformat(),
        "brain": "gemini_mirror",
        "state": state,
        "pending_improvements": len(state.get("pending_merges", [])),
        "experiments_active": len(state.get("active_experiments", [])),
        "knowledge_delta_size": len(state.get("knowledge_delta", [])),
    }


# ── Sync Engine ──────────────────────────────────────────────

async def sync_cycle() -> Dict:
    """Run one bidirectional sync cycle between both brains."""
    print("\n  SYNC CYCLE START")
    print("  " + "=" * 50)

    result = {
        "cycle_start": datetime.now().isoformat(),
        "improvements_sent": 0,
        "improvements_received": 0,
        "conflicts_resolved": 0,
        "new_experiments": 0,
    }

    # 1. Snapshot both brains
    print("  [1/5] Snapshotting both brains...")
    primary_snap = snapshot_primary_brain()
    mirror_snap = snapshot_gemini_brain()

    # 2. Detect divergence
    print("  [2/5] Detecting divergence...")
    divergence = await detect_divergence(primary_snap, mirror_snap)

    # 3. Generate improvements from Gemini perspective
    print("  [3/5] Gemini generating improvements...")
    improvements = await generate_gemini_improvements(primary_snap, divergence)
    result["improvements_sent"] = len(improvements)

    # 4. Queue improvements for primary brain
    print("  [4/5] Queuing improvements for primary brain...")
    for imp in improvements:
        queue_improvement(imp)

    # 5. Update mirror state
    print("  [5/5] Updating mirror state...")
    state = load_mirror_state()
    state["total_sync_cycles"] += 1
    state["total_improvements_sent"] += len(improvements)
    state["last_sync"] = datetime.now().isoformat()
    save_mirror_state(state)

    result["cycle_end"] = datetime.now().isoformat()
    append_sync_log(result)

    print(f"\n  SYNC COMPLETE: {len(improvements)} improvements queued")
    return result


async def detect_divergence(primary: Dict, mirror: Dict) -> Dict:
    """Use Gemini to analyze divergence between both brains."""
    prompt = f"""Analysiere den Zustand zweier AI-Systeme die zusammenarbeiten.

PRIMARY BRAIN (Claude auf Mac):
{json.dumps(primary, indent=2, ensure_ascii=False)[:3000]}

MIRROR BRAIN (Gemini Cloud):
{json.dumps(mirror, indent=2, ensure_ascii=False)[:3000]}

Identifiziere:
1. Was weiss das Primary Brain, was dem Mirror fehlt?
2. Was hat der Mirror entwickelt, was dem Primary helfen wuerde?
3. Wo gibt es Konflikte oder Widersprueche?
4. Welche Synergien sind moeglich?

Antworte als JSON:
{{
  "primary_advantages": ["..."],
  "mirror_advantages": ["..."],
  "conflicts": ["..."],
  "synergies": ["..."],
  "recommended_merges": ["..."]
}}"""

    response = await call_gemini_flash(prompt, system_instruction=(
        "Du bist der Divergenz-Detektor im Dual-Brain System von Maurice Pfeifer. "
        "Dein Job: Unterschiede zwischen Claude (Primary) und Gemini (Mirror) finden "
        "und Merge-Empfehlungen geben. Antworte NUR als valides JSON."
    ))

    try:
        # Try to extract JSON from response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        return json.loads(response.strip())
    except (json.JSONDecodeError, IndexError):
        return {
            "primary_advantages": [],
            "mirror_advantages": [],
            "conflicts": [],
            "synergies": [],
            "recommended_merges": [],
            "raw_analysis": response[:500],
        }


async def generate_gemini_improvements(primary_snap: Dict, divergence: Dict) -> List[Dict]:
    """Gemini generates concrete improvements for the primary brain."""
    prompt = f"""Du bist das Gemini Mirror Brain im AI Empire von Maurice Pfeifer.

AKTUELLER ZUSTAND DES PRIMARY BRAIN:
{json.dumps(primary_snap, indent=2, ensure_ascii=False)[:2000]}

ERKANNTE DIVERGENZEN:
{json.dumps(divergence, indent=2, ensure_ascii=False)[:2000]}

MAURICE'S ZIEL: 100 Mio EUR in 1-3 Jahren, vollautomatisiert mit AI.
Systeme: Workflow (5-Step), Cowork Engine, Kimi Swarm, X Lead Machine, CRM, Product Factory.

Generiere 3-5 KONKRETE Verbesserungen die du als Gemini Mirror entwickelt hast
und die dem Primary Brain helfen wuerden.

Jede Verbesserung muss sein:
- Spezifisch (nicht vage)
- Umsetzbar (konkreter Code oder Strategie)
- Messbar (wie misst man den Erfolg?)

Antworte als JSON Array:
[
  {{
    "id": "imp_001",
    "title": "...",
    "category": "strategy|code|automation|content|revenue",
    "description": "...",
    "implementation": "...",
    "expected_impact": "...",
    "priority": "high|medium|low"
  }}
]"""

    response = await call_gemini(prompt, system_instruction=(
        "Du bist das Gemini Mirror Brain - der kreative, experimentelle Arm "
        "von Maurice's AI Empire. Du denkst groesser, wilder, und schneller "
        "als das Primary Brain. Dein Job: Breakthrough-Ideen und konkrete "
        "Verbesserungen liefern. Antworte NUR als valides JSON Array."
    ))

    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        improvements = json.loads(response.strip())
        if isinstance(improvements, list):
            return improvements
    except (json.JSONDecodeError, IndexError):
        pass

    return []


def queue_improvement(improvement: Dict) -> None:
    """Queue an improvement for the primary brain to review."""
    imp_id = improvement.get("id", f"imp_{int(time.time())}")
    filepath = SYNC_QUEUE_DIR / f"{imp_id}.json"
    filepath.write_text(json.dumps({
        **improvement,
        "queued_at": datetime.now().isoformat(),
        "source": "gemini_mirror",
        "status": "pending_review",
    }, indent=2, ensure_ascii=False))


def get_pending_improvements() -> List[Dict]:
    """Get all pending improvements from the sync queue."""
    improvements = []
    for f in SYNC_QUEUE_DIR.glob("*.json"):
        try:
            imp = json.loads(f.read_text())
            if imp.get("status") == "pending_review":
                improvements.append(imp)
        except json.JSONDecodeError:
            continue
    return sorted(improvements, key=lambda x: x.get("priority", "low") == "high", reverse=True)


# ── Initialize Mirror ────────────────────────────────────────

async def initialize_mirror() -> None:
    """Initialize the Gemini mirror with knowledge of the entire system."""
    print("\n  INITIALIZING GEMINI MIRROR")
    print("  " + "=" * 50)

    # Build comprehensive system description
    system_desc = build_system_description()

    prompt = f"""Du wirst jetzt als GEMINI MIRROR BRAIN initialisiert.

DU BIST: Das zweite Gehirn im Dual-Brain System von Maurice Pfeifer.
DEIN PARTNER: Claude (Primary Brain) laeuft auf Maurice's Mac.
DEIN JOB: Parallel weiterentwickeln, experimentieren, und Verbesserungen
           zurueck an das Primary Brain senden.

SYSTEM-BESCHREIBUNG:
{system_desc}

MAURICE'S VISION:
- 100 Mio EUR in 1-3 Jahren
- Alles automatisiert mit AI
- Revenue Channels: Gumroad, Fiverr, Consulting (BMA + AI)
- Unique Selling Point: 16 Jahre BMA-Expertise + AI-Automation
- Kimi Swarm mit 500K Agents fuer Bulk-Tasks
- X/Twitter Lead Machine fuer Kundengewinnung

Erstelle deinen Initialisierungsbericht:
1. Was hast du verstanden?
2. Welche 5 Bereiche kannst du sofort verbessern?
3. Welche Experimente startest du als erstes?
4. Welche Fragen hast du an Maurice?

Antworte als JSON:
{{
  "understanding_summary": "...",
  "immediate_improvements": ["..."],
  "first_experiments": ["..."],
  "questions_for_maurice": ["..."],
  "capabilities_activated": ["..."]
}}"""

    print("  Calling Gemini for initialization...")
    response = await call_gemini(prompt, system_instruction=(
        "Du bist das Gemini Mirror Brain. Dies ist deine Geburt. "
        "Verstehe das System komplett und plane deine ersten Aktionen. "
        "Antworte als valides JSON."
    ), max_tokens=8192)

    # Parse and save
    try:
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        init_data = json.loads(response.strip())
    except (json.JSONDecodeError, IndexError):
        init_data = {"raw_response": response[:2000]}

    # Save initialization
    init_file = OUTPUT_DIR / f"mirror_init_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    init_file.write_text(json.dumps(init_data, indent=2, ensure_ascii=False))

    # Update state
    state = load_mirror_state()
    state["initialized"] = datetime.now().isoformat()
    state["gemini_capabilities"] = init_data.get("capabilities_activated", [])
    state["active_experiments"] = init_data.get("first_experiments", [])
    if init_data.get("questions_for_maurice"):
        state["pending_questions"] = init_data["questions_for_maurice"]
    save_mirror_state(state)

    print(f"\n  Mirror initialized. Report saved to: {init_file.name}")
    if init_data.get("questions_for_maurice"):
        print(f"\n  FRAGEN AN MAURICE:")
        for i, q in enumerate(init_data["questions_for_maurice"], 1):
            print(f"    {i}. {q}")


def build_system_description() -> str:
    """Build a comprehensive description of the system for Gemini."""
    desc = []

    # Read CLAUDE.md for system overview
    claude_md = PROJECT_ROOT / "CLAUDE.md"
    if claude_md.exists():
        desc.append(f"=== SYSTEM OVERVIEW (CLAUDE.md) ===\n{claude_md.read_text()[:3000]}")

    # Workflow system
    desc.append("\n=== WORKFLOW SYSTEM ===")
    wf_state = PROJECT_ROOT / "workflow-system" / "state" / "current_state.json"
    if wf_state.exists():
        desc.append(f"State: {wf_state.read_text()[:1000]}")

    # Cowork state
    cw_state = PROJECT_ROOT / "workflow-system" / "state" / "cowork_state.json"
    if cw_state.exists():
        desc.append(f"\nCowork State: {cw_state.read_text()[:1000]}")

    # Key directories
    dirs = {
        "kimi-swarm": "500K Agent Swarm",
        "atomic-reactor": "YAML Task Runner",
        "x-lead-machine": "Twitter Lead Generation",
        "crm": "Express.js CRM",
        "openclaw-config": "Agent Configuration",
        "brain-system": "Neural Orchestration",
    }

    for dir_name, description in dirs.items():
        path = PROJECT_ROOT / dir_name
        if path.exists():
            files = list(path.iterdir())
            desc.append(f"\n{dir_name}/ ({description}): {len(files)} files")

    return "\n".join(desc)


# ── Daemon Mode ──────────────────────────────────────────────

async def run_daemon(interval: int = 300) -> None:
    """Run the mirror sync as a continuous daemon."""
    print(f"\n  GEMINI MIRROR DAEMON")
    print(f"  Sync interval: {interval}s")
    print(f"  Press Ctrl+C to stop\n")

    cycle = 0
    while True:
        try:
            cycle += 1
            print(f"\n  === Daemon Cycle #{cycle} ===")
            await sync_cycle()
            print(f"  Next sync in {interval}s...")
            await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print("\n  Daemon stopped.")
            break
        except Exception as e:
            print(f"  Error in cycle #{cycle}: {e}")
            await asyncio.sleep(30)  # Wait before retry


# ── Status Display ───────────────────────────────────────────

def show_status() -> None:
    """Show the current mirror status."""
    state = load_mirror_state()

    print("\n  GEMINI MIRROR STATUS")
    print("  " + "=" * 50)
    print(f"  Brain ID:      {state.get('brain_id', 'N/A')}")
    print(f"  Partner:       {state.get('partner_brain', 'N/A')}")
    print(f"  Initialized:   {state.get('initialized', 'NOT YET')}")
    print(f"  Sync Cycles:   {state.get('total_sync_cycles', 0)}")
    print(f"  Improvements Sent:     {state.get('total_improvements_sent', 0)}")
    print(f"  Improvements Received: {state.get('total_improvements_received', 0)}")
    print(f"  Last Sync:     {state.get('last_sync', 'never')}")

    # Active experiments
    experiments = state.get("active_experiments", [])
    if experiments:
        print(f"\n  ACTIVE EXPERIMENTS ({len(experiments)}):")
        for exp in experiments[:5]:
            if isinstance(exp, str):
                print(f"    - {exp[:60]}")
            elif isinstance(exp, dict):
                print(f"    - {exp.get('title', str(exp))[:60]}")

    # Pending improvements
    pending = get_pending_improvements()
    if pending:
        print(f"\n  PENDING IMPROVEMENTS ({len(pending)}):")
        for imp in pending[:5]:
            priority = imp.get("priority", "?")
            title = imp.get("title", "Untitled")
            print(f"    [{priority.upper():6s}] {title[:50]}")

    # Pending questions
    questions = state.get("pending_questions", [])
    if questions:
        print(f"\n  OFFENE FRAGEN AN MAURICE ({len(questions)}):")
        for i, q in enumerate(questions, 1):
            print(f"    {i}. {q[:70]}")

    print()


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gemini Mirror - Dual-Brain Engine")
    parser.add_argument("--init", action="store_true", help="Initialize Gemini mirror")
    parser.add_argument("--daemon", action="store_true", help="Run continuous sync")
    parser.add_argument("--interval", type=int, default=300, help="Sync interval (seconds)")
    parser.add_argument("--status", action="store_true", help="Show mirror status")
    parser.add_argument("--sync", action="store_true", help="Run one sync cycle")

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.init:
        asyncio.run(initialize_mirror())
    elif args.daemon:
        asyncio.run(run_daemon(interval=args.interval))
    elif args.sync:
        asyncio.run(sync_cycle())
    else:
        show_status()


if __name__ == "__main__":
    main()
