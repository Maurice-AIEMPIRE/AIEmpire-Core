#!/usr/bin/env python3
"""
COWORK ENGINE - Autonomous Background Agent
Equivalent of Claude Desktop Cowork, built for CLI.

Observe-Plan-Act-Reflect Loop:
1. OBSERVE: Scan project state, recent outputs, file changes
2. PLAN:    Identify highest-impact next action
3. ACT:     Execute via workflow system or direct API call
4. REFLECT: Score result, extract patterns, update state

Runs as a daemon. Each cycle produces actionable output.

Usage:
  python cowork.py                   # Run one cycle
  python cowork.py --daemon          # Run continuously (interval-based)
  python cowork.py --interval 1800   # Custom interval in seconds
  python cowork.py --focus revenue   # Focus on specific area
  python cowork.py --status          # Show cowork state
"""

import argparse
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import aiohttp
from resource_guard import ResourceGuard

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
WORKFLOW_DIR = Path(__file__).parent
COWORK_DIR = WORKFLOW_DIR / "cowork_output"
COWORK_STATE_FILE = WORKFLOW_DIR / "state" / "cowork_state.json"

COWORK_DIR.mkdir(parents=True, exist_ok=True)

# API
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")

# Focus areas with their scan targets
FOCUS_AREAS = {
    "revenue": {
        "description": "Revenue generation and monetization",
        "scan_dirs": [
            "gold-nuggets",
            "kimi_swarm/output_500k",
            "REVENUE_STRATEGY_50K_AGENTS.md",
        ],
        "priority_keywords": [
            "revenue",
            "monetization",
            "gumroad",
            "fiverr",
            "sales",
            "lead",
        ],
    },
    "content": {
        "description": "Content pipeline and social media",
        "scan_dirs": ["x_lead_machine", "workflow_system/output"],
        "priority_keywords": ["content", "post", "viral", "twitter", "engagement"],
    },
    "automation": {
        "description": "System automation and efficiency",
        "scan_dirs": ["atomic_reactor", "openclaw-config", "workflow_system"],
        "priority_keywords": ["automation", "cron", "task", "workflow", "pipeline"],
    },
    "product": {
        "description": "Digital product development",
        "scan_dirs": ["gold-nuggets", "workflow_system/output"],
        "priority_keywords": ["product", "guide", "template", "gumroad", "ebook"],
    },
}


def load_cowork_state() -> Dict:
    """Load persistent cowork state."""
    if COWORK_STATE_FILE.exists():
        return json.loads(COWORK_STATE_FILE.read_text())
    return {
        "created": datetime.now().isoformat(),
        "total_cycles": 0,
        "actions_taken": [],
        "observations": [],
        "active_focus": "revenue",
        "pending_recommendations": [],
        "patterns_discovered": [],
    }


def save_cowork_state(state: Dict) -> None:
    state["updated"] = datetime.now().isoformat()
    COWORK_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ── OBSERVE ──────────────────────────────────────────────


def observe_project() -> Dict:
    """Scan the project and build a situational awareness snapshot."""
    observations = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "files": {},
        "recent_outputs": [],
        "system_health": {},
        "blockers": [],
    }

    # Scan key directories for recent activity
    scan_targets = [
        ("workflow_system/output", "workflow_outputs"),
        ("workflow_system/state", "workflow_state"),
        ("kimi_swarm/output_500k", "swarm_outputs"),
        ("atomic_reactor/reports", "reactor_reports"),
        ("x_lead_machine", "lead_machine"),
        ("gold-nuggets", "gold_nuggets"),
    ]

    for rel_path, key in scan_targets:
        target = PROJECT_ROOT / rel_path
        if target.exists():
            if target.is_dir():
                files = sorted(
                    target.glob("*"),
                    key=lambda f: f.stat().st_mtime if f.exists() else 0,
                    reverse=True,
                )
                observations["files"][key] = {
                    "count": len(files),
                    "recent": [f.name for f in files[:5]],
                    "newest_age_hours": _file_age_hours(files[0]) if files else None,
                }
            else:
                observations["files"][key] = {
                    "exists": True,
                    "age_hours": _file_age_hours(target),
                }

    # Check workflow state
    wf_state_file = WORKFLOW_DIR / "state" / "current_state.json"
    if wf_state_file.exists():
        wf_state = json.loads(wf_state_file.read_text())
        observations["system_health"]["workflow_cycle"] = wf_state.get("cycle", 0)
        observations["system_health"]["steps_completed"] = len(wf_state.get("steps_completed", []))
        observations["system_health"]["patterns_count"] = len(wf_state.get("patterns", []))
    else:
        observations["blockers"].append("Workflow system has not been run yet (no state)")

    # Check for revenue status
    revenue_file = PROJECT_ROOT / "REVENUE_STRATEGY_50K_AGENTS.md"
    if revenue_file.exists():
        observations["system_health"]["revenue_strategy"] = True
    else:
        observations["blockers"].append("No revenue strategy document found")

    # Detect stale outputs (nothing new in 24h)
    for key, info in observations["files"].items():
        if isinstance(info, dict) and info.get("newest_age_hours") and info["newest_age_hours"] > 24:
            observations["blockers"].append(f"{key}: No new output in {info['newest_age_hours']:.0f}h")

    return observations


def _file_age_hours(path: Path) -> float:
    if not path.exists():
        return float("inf")
    age_sec = time.time() - path.stat().st_mtime
    return age_sec / 3600


# ── PLAN ─────────────────────────────────────────────────

PLAN_PROMPT = """Du bist der Cowork Planning Agent fuer Maurice's AI Empire.

BEOBACHTUNGEN (aktuelle Projektsituation):
{observations}

FOKUS-BEREICH: {focus} - {focus_description}

BISHERIGE AKTIONEN ({action_count} total):
{recent_actions}

ERKANNTE BLOCKER:
{blockers}

AUFGABE: Basierend auf den Beobachtungen, identifiziere die EINE wichtigste
Aktion die JETZT ausgefuehrt werden sollte.

Kriterien:
- Hoechster Impact auf Revenue
- Niedrigster Aufwand
- Beseitigt Blocker
- Baut auf bestehender Arbeit auf

OUTPUT als JSON:
{{
    "priority_action": {{
        "title": "Was genau tun",
        "why": "Warum JETZT und nicht spaeter",
        "how": "Konkrete Schritte (max 5)",
        "expected_impact": "Was aendert sich dadurch",
        "effort_minutes": <geschaetzter Aufwand>,
        "category": "revenue|content|automation|product",
        "dependencies": ["Was muss vorher erledigt sein"],
        "success_criteria": "Woran erkennt man dass es geklappt hat"
    }},
    "secondary_actions": [
        {{
            "title": "Naechste Prioritaet",
            "why": "Kurze Begruendung",
            "effort_minutes": <Aufwand>
        }}
    ],
    "situation_assessment": "2-3 Saetze Lagebeurteilung",
    "risk_alert": "Warnung falls etwas Kritisches uebersehen wird (oder null)"
}}"""


async def plan_next_action(observations: Dict, state: Dict) -> Dict:
    """Use AI to determine the highest-impact next action."""
    focus = state.get("active_focus", "revenue")
    focus_info = FOCUS_AREAS.get(focus, FOCUS_AREAS["revenue"])

    recent_actions = state.get("actions_taken", [])[-5:]
    actions_str = (
        json.dumps(recent_actions, indent=2, ensure_ascii=False) if recent_actions else "Keine bisherigen Aktionen"
    )

    blockers = observations.get("blockers", [])
    blockers_str = "\n".join(f"- {b}" for b in blockers) if blockers else "Keine Blocker erkannt"

    prompt = PLAN_PROMPT.format(
        observations=json.dumps(observations, indent=2, ensure_ascii=False)[:3000],
        focus=focus,
        focus_description=focus_info["description"],
        action_count=len(state.get("actions_taken", [])),
        recent_actions=actions_str[:1500],
        blockers=blockers_str,
    )

    raw = await _call_kimi(
        "Du bist ein strategischer Planning Agent. Priorisiere brutal. Eine Aktion. JSON output.",
        prompt,
    )
    return _parse_json(raw, "plan")


# ── ACT ──────────────────────────────────────────────────

ACT_PROMPT = """Fuehre folgende Aktion aus und liefere das Ergebnis.

AKTION:
{action}

PROJEKT-KONTEXT:
- Verzeichnis: /home/user/AIEmpire-Core
- Workflow System: workflow_system/orchestrator.py (5-step loop)
- Kimi Swarm: kimi_swarm/swarm_500k.py (50K-500K agents)
- Content: x_lead_machine/ (Posts, Replies, Lead Gen)
- CRM: crm/server.js (Express.js + SQLite)
- Produkte: Gumroad (1 aktiv: AI Prompt Vault 27 EUR)

AUFGABE: Erstelle das konkrete OUTPUT fuer diese Aktion.
Wenn es Code ist: liefere den Code.
Wenn es Content ist: liefere den Content.
Wenn es eine Analyse ist: liefere die Analyse.
Sei KONKRET und ACTIONABLE.

OUTPUT als JSON:
{{
    "action_title": "Was ausgefuehrt wurde",
    "deliverable_type": "code|content|analysis|config|plan",
    "deliverable": "Das konkrete Ergebnis (Code, Text, Config, etc.)",
    "files_to_create": [
        {{
            "path": "relativer/pfad/datei.ext",
            "description": "Was die Datei tut"
        }}
    ],
    "files_to_modify": [
        {{
            "path": "relativer/pfad/datei.ext",
            "change": "Was aendern"
        }}
    ],
    "next_manual_step": "Was Maurice als naechstes MANUELL tun muss (oder null)",
    "execution_notes": "Wichtige Hinweise zur Ausfuehrung"
}}"""


async def execute_action(plan: Dict) -> Dict:
    """Execute the planned action via AI."""
    action = plan.get("priority_action", {})
    prompt = ACT_PROMPT.format(
        action=json.dumps(action, indent=2, ensure_ascii=False),
    )

    raw = await _call_kimi(
        "Du bist ein Execution Agent. Liefere konkrete, sofort nutzbare Ergebnisse. JSON output.",
        prompt,
    )
    return _parse_json(raw, "act")


# ── REFLECT ──────────────────────────────────────────────

REFLECT_PROMPT = """Reflektiere ueber den gerade abgeschlossenen Cowork-Zyklus.

BEOBACHTUNG:
{observation_summary}

PLAN:
{plan_summary}

AKTION (Ergebnis):
{action_summary}

BISHERIGE PATTERNS ({pattern_count}):
{existing_patterns}

AUFGABE: Bewerte den Zyklus und extrahiere Learnings.

OUTPUT als JSON:
{{
    "cycle_score": <1-10>,
    "what_worked": "Was gut funktioniert hat",
    "what_didnt": "Was nicht funktioniert hat (oder null)",
    "pattern_discovered": {{
        "name": "Pattern Name (oder null wenn kein neues Pattern)",
        "description": "Was das Pattern ist",
        "reusable": true
    }},
    "improvement_for_next_cycle": "Wie der naechste Zyklus besser wird",
    "recommended_focus_shift": "revenue|content|automation|product|stay",
    "confidence": <1-10 wie sicher ist die Empfehlung>
}}"""


async def reflect_on_cycle(observations: Dict, plan: Dict, action_result: Dict, state: Dict) -> Dict:
    """Evaluate the cycle and extract patterns."""
    prompt = REFLECT_PROMPT.format(
        observation_summary=json.dumps(_summarize(observations), indent=2, ensure_ascii=False),
        plan_summary=json.dumps(plan.get("priority_action", {}), indent=2, ensure_ascii=False)[:1000],
        action_summary=json.dumps(action_result, indent=2, ensure_ascii=False)[:2000],
        pattern_count=len(state.get("patterns_discovered", [])),
        existing_patterns=json.dumps(state.get("patterns_discovered", [])[-5:], indent=2, ensure_ascii=False)[:1000],
    )

    raw = await _call_kimi(
        "Du bist ein Reflection Agent. Bewerte ehrlich. Extrahiere Patterns. JSON output.",
        prompt,
    )
    return _parse_json(raw, "reflect")


def _summarize(obs: Dict) -> Dict:
    return {
        "blockers": obs.get("blockers", []),
        "file_counts": {k: v.get("count", 0) for k, v in obs.get("files", {}).items() if isinstance(v, dict)},
        "health": obs.get("system_health", {}),
    }


# ── MAIN LOOP ────────────────────────────────────────────


async def run_cycle(focus: Optional[str] = None, guard: Optional[ResourceGuard] = None) -> Dict:
    """Run one complete Observe-Plan-Act-Reflect cycle."""
    if guard is None:
        guard = ResourceGuard()

    state = load_cowork_state()
    if focus:
        state["active_focus"] = focus

    cycle_num = state.get("total_cycles", 0) + 1
    state["total_cycles"] = cycle_num

    # Resource check before starting
    async with guard.check() as gs:
        guard_status = guard.format_status()

    print(f"""
{"=" * 60}
  COWORK ENGINE - Cycle #{cycle_num}
  Focus: {state.get("active_focus", "revenue")}
  Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
  Guard: {guard_status}
{"=" * 60}
""")

    # Resource guard before each phase
    async with guard.check() as gs:
        if gs.paused:
            print("  GUARD: System overloaded. Cycle deferred.")
            save_cowork_state(state)
            return {
                "cycle": cycle_num,
                "status": "deferred_by_guard",
                "guard": guard.get_status(),
            }

    # 1. OBSERVE
    print("  [1/4] OBSERVE - Scanning project state...")
    observations = observe_project()
    blocker_count = len(observations.get("blockers", []))
    print(f"         Found {blocker_count} blockers, scanned {len(observations.get('files', {}))} areas")

    # Resource check before PLAN
    async with guard.check():
        pass

    # 2. PLAN
    print("  [2/4] PLAN - Identifying highest-impact action...")
    plan = await plan_next_action(observations, state)
    action_title = plan.get("priority_action", {}).get("title", "unknown")
    print(f"         Priority: {action_title}")
    print(f"         Assessment: {plan.get('situation_assessment', 'N/A')[:80]}")

    # Resource check before ACT
    async with guard.check():
        pass

    # 3. ACT
    print("  [3/4] ACT - Executing action...")
    action_result = await execute_action(plan)
    deliverable_type = action_result.get("deliverable_type", "unknown")
    print(f"         Deliverable: {deliverable_type}")
    files_created = len(action_result.get("files_to_create", []))
    files_modified = len(action_result.get("files_to_modify", []))
    if files_created or files_modified:
        print(f"         Files: {files_created} new, {files_modified} modified")

    # Resource check before REFLECT
    async with guard.check():
        pass

    # 4. REFLECT
    print("  [4/4] REFLECT - Evaluating cycle...")
    reflection = await reflect_on_cycle(observations, plan, action_result, state)
    score = reflection.get("cycle_score", "?")
    print(f"         Score: {score}/10")
    print(f"         Learned: {reflection.get('what_worked', 'N/A')[:60]}")

    # Update state
    state["actions_taken"].append(
        {
            "cycle": cycle_num,
            "timestamp": datetime.now().isoformat(),
            "action": action_title,
            "score": score,
            "focus": state.get("active_focus"),
        }
    )

    # Keep only last 50 actions
    if len(state["actions_taken"]) > 50:
        state["actions_taken"] = state["actions_taken"][-50:]

    # Store pattern if discovered
    pattern = reflection.get("pattern_discovered", {})
    if pattern and pattern.get("name"):
        state.setdefault("patterns_discovered", []).append(pattern)

    # Shift focus if recommended
    recommended = reflection.get("recommended_focus_shift", "stay")
    if recommended != "stay" and recommended in FOCUS_AREAS:
        print(f"         Focus shift: {state['active_focus']} -> {recommended}")
        state["active_focus"] = recommended

    # Store pending recommendations
    secondary = plan.get("secondary_actions", [])
    state["pending_recommendations"] = secondary[:5]

    save_cowork_state(state)

    # Save cycle output
    cycle_file = COWORK_DIR / f"cycle_{cycle_num:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    cycle_data = {
        "cycle": cycle_num,
        "focus": state.get("active_focus"),
        "observations": _summarize(observations),
        "plan": plan,
        "action_result": action_result,
        "reflection": reflection,
        "timestamp": datetime.now().isoformat(),
    }
    cycle_file.write_text(json.dumps(cycle_data, indent=2, ensure_ascii=False))

    print(f"""
{"=" * 60}
  CYCLE #{cycle_num} COMPLETE
  Score: {score}/10
  Output: {cycle_file.name}
  Next focus: {state.get("active_focus")}
  Guard: {guard.format_status()}
  Manual step: {action_result.get("next_manual_step", "None")}
{"=" * 60}
""")

    return cycle_data


async def run_daemon(interval: int = 1800, focus: Optional[str] = None):
    """Run continuously with given interval (default: 30 min)."""
    guard = ResourceGuard()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║          COWORK ENGINE - DAEMON MODE                    ║
║          Interval: {interval}s ({interval // 60} min)                          ║
║          Resource Guard: ACTIVE                         ║
║          Press Ctrl+C to stop                           ║
╚══════════════════════════════════════════════════════════╝
    """)

    while True:
        try:
            # Check resources before starting a cycle
            status = guard.get_status()
            print(f"  Guard: {guard.format_status()}")

            if status["paused"]:
                print("  System overloaded! Waiting for recovery...")
                await guard.wait_if_paused()
                print("  Recovered. Starting cycle.")

            await run_cycle(focus=focus, guard=guard)
            print(f"\n  Next cycle in {interval}s ({interval // 60} min)...\n")
            await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print("\n  Daemon stopped by user.")
            break
        except Exception as e:
            print(f"\n  Cycle error: {e}")
            print(f"  Retrying in {interval}s...\n")
            await asyncio.sleep(interval)


def show_status():
    """Display cowork state."""
    state = load_cowork_state()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║              COWORK ENGINE STATUS                       ║
╠══════════════════════════════════════════════════════════╣
  Total cycles:     {state.get("total_cycles", 0)}
  Active focus:     {state.get("active_focus", "N/A")}
  Actions taken:    {len(state.get("actions_taken", []))}
  Patterns found:   {len(state.get("patterns_discovered", []))}
  Last updated:     {state.get("updated", "Never")}
╚══════════════════════════════════════════════════════════╝
    """)

    recent = state.get("actions_taken", [])[-5:]
    if recent:
        print("  Recent actions:")
        for a in recent:
            print(f"    [{a.get('score', '?')}/10] {a.get('action', 'N/A')[:50]}")

    pending = state.get("pending_recommendations", [])
    if pending:
        print("\n  Pending recommendations:")
        for p in pending:
            print(f"    - {p.get('title', 'N/A')[:50]} ({p.get('effort_minutes', '?')} min)")

    patterns = state.get("patterns_discovered", [])
    if patterns:
        print(f"\n  Pattern library ({len(patterns)}):")
        for p in patterns[-5:]:
            print(f"    - {p.get('name', 'unnamed')}: {p.get('description', '')[:50]}")


# ── HELPERS ──────────────────────────────────────────────


async def _call_kimi(system: str, user: str) -> str:
    if not MOONSHOT_API_KEY:
        raise ValueError("MOONSHOT_API_KEY not set")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.moonshot.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {MOONSHOT_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "moonshot-v1-32k",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.7,
                "max_tokens": 3000,
            },
            timeout=aiohttp.ClientTimeout(total=90),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                tokens = data.get("usage", {}).get("total_tokens", 0)
                cost = (tokens / 1000) * 0.001
                print(f"         API: {tokens} tokens, ${cost:.4f}")
                return data["choices"][0]["message"]["content"]
            else:
                text = await resp.text()
                raise RuntimeError(f"Kimi API {resp.status}: {text[:200]}")


def _parse_json(raw: str, step_name: str) -> Dict:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {"step": step_name, "raw": raw, "parse_error": True}


# ── CLI ──────────────────────────────────────────────────


async def main():
    parser = argparse.ArgumentParser(description="Cowork Engine - Autonomous Background Agent")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument(
        "--interval",
        type=int,
        default=1800,
        help="Daemon interval in seconds (default: 1800)",
    )
    parser.add_argument("--focus", choices=list(FOCUS_AREAS.keys()), help="Focus area")
    parser.add_argument("--status", action="store_true", help="Show cowork state")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.daemon:
        await run_daemon(interval=args.interval, focus=args.focus)
    else:
        await run_cycle(focus=args.focus)


if __name__ == "__main__":
    asyncio.run(main())
