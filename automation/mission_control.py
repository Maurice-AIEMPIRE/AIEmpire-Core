from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from automation.core.config import load_router_config
from automation.core.providers import ProviderError, provider_from_dict
from automation.core.router import ModelSpec, Router
from automation.utils.files import ensure_dir, timestamp_id, write_json, write_text


ROOT = Path(__file__).resolve().parents[1]
MISSION_CONFIG_PATH = ROOT / "automation" / "config" / "mission_control.json"
MISSION_STATE_PATH = ROOT / "ai-vault" / "mission_control_state.json"
RUNS_DIR = ROOT / "automation" / "runs"
DEFAULT_TRANSCRIBE_CLI = Path.home() / ".codex" / "skills" / "transcribe" / "scripts" / "transcribe_diarize.py"


def _now_iso() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_mission_config(path: Optional[Path] = None) -> Dict[str, Any]:
    cfg_path = path or MISSION_CONFIG_PATH
    return _load_json(cfg_path)


def default_state() -> Dict[str, Any]:
    return {
        "created_at": _now_iso(),
        "revenue_entries": [],
        "wins": [],
        "notes": [],
        "last_voice_command": {},
    }


def load_state(path: Optional[Path] = None) -> Dict[str, Any]:
    state_path = path or MISSION_STATE_PATH
    raw = _load_json(state_path)
    if not raw:
        return default_state()
    base = default_state()
    base.update(raw)
    if not isinstance(base.get("revenue_entries"), list):
        base["revenue_entries"] = []
    if not isinstance(base.get("wins"), list):
        base["wins"] = []
    if not isinstance(base.get("notes"), list):
        base["notes"] = []
    return base


def save_state(state: Dict[str, Any], path: Optional[Path] = None) -> Path:
    state_path = path or MISSION_STATE_PATH
    write_json(state_path, state)
    return state_path


def _parse_iso_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def _safe_parse_date(value: str) -> Optional[dt.date]:
    try:
        return _parse_iso_date(value)
    except Exception:
        return None


def _month_bounds(day: dt.date) -> Tuple[dt.date, dt.date]:
    first = day.replace(day=1)
    if day.month == 12:
        last = dt.date(day.year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        last = dt.date(day.year, day.month + 1, 1) - dt.timedelta(days=1)
    return first, last


def _months_between(start: dt.date, end: dt.date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def _current_month_revenue(entries: Sequence[Dict[str, Any]], today: dt.date) -> float:
    first_day, last_day = _month_bounds(today)
    total = 0.0
    for entry in entries:
        date_raw = str(entry.get("date", ""))
        amount = float(entry.get("amount_eur", 0) or 0)
        date = _safe_parse_date(date_raw)
        if date is None:
            continue
        if first_day <= date <= last_day:
            total += amount
    return total


def _all_time_revenue(entries: Sequence[Dict[str, Any]]) -> float:
    total = 0.0
    for entry in entries:
        total += float(entry.get("amount_eur", 0) or 0)
    return total


def _active_target(config: Dict[str, Any], created_at: str, today: dt.date) -> Dict[str, Any]:
    targets = config.get("revenue_targets", [])
    if not isinstance(targets, list) or not targets:
        return {
            "phase": "fallback",
            "month_start": 1,
            "month_end": 12,
            "monthly_min_eur": 5000,
            "monthly_stretch_eur": 10000,
        }

    created_date = _safe_parse_date(created_at[:10]) or today
    month_index = _months_between(created_date, today) + 1

    for target in targets:
        month_start = int(target.get("month_start", 1))
        month_end = int(target.get("month_end", 999))
        if month_start <= month_index <= month_end:
            return target

    return targets[-1]


def _latest_files(pattern: str, limit: int = 5) -> List[Path]:
    items = list(RUNS_DIR.glob(pattern))
    items.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return items[:limit]


def _deliverable_status() -> List[Tuple[str, str]]:
    targets = [
        ROOT / "content_factory" / "deliverables" / "threads_50.md",
        ROOT / "content_factory" / "deliverables" / "tweets_300.md",
        ROOT / "content_factory" / "deliverables" / "premium_prompts_400.md",
        ROOT / "content_factory" / "deliverables" / "monetization_strategy.md",
    ]
    out: List[Tuple[str, str]] = []
    for path in targets:
        if not path.exists():
            out.append((path.name, "missing"))
            continue
        mtime = dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        out.append((path.name, f"ok ({mtime})"))
    return out


def build_status_report(config: Dict[str, Any], state: Dict[str, Any]) -> str:
    today = dt.date.today()
    revenue_entries = state.get("revenue_entries", [])
    if not isinstance(revenue_entries, list):
        revenue_entries = []

    active_target = _active_target(config, str(state.get("created_at", _now_iso())), today)
    month_revenue = _current_month_revenue(revenue_entries, today)
    all_time_revenue = _all_time_revenue(revenue_entries)

    monthly_min = float(active_target.get("monthly_min_eur", 5000) or 5000)
    monthly_stretch = float(active_target.get("monthly_stretch_eur", monthly_min) or monthly_min)
    gap_min = max(0.0, monthly_min - month_revenue)
    gap_stretch = max(0.0, monthly_stretch - month_revenue)

    latest_parallel = _latest_files("parallel_chat_*.json", limit=3)
    latest_voice = _latest_files("voice_*/voice_event.json", limit=3)
    latest_runs = _latest_files("run_*.json", limit=3)

    lines: List[str] = []
    lines.append(f"# Mission Control Status ({today.isoformat()})")
    lines.append("")
    lines.append("## Revenue")
    lines.append(f"- current_month_eur: {month_revenue:.2f}")
    lines.append(f"- target_min_eur: {monthly_min:.2f}")
    lines.append(f"- target_stretch_eur: {monthly_stretch:.2f}")
    lines.append(f"- gap_to_min_eur: {gap_min:.2f}")
    lines.append(f"- gap_to_stretch_eur: {gap_stretch:.2f}")
    lines.append(f"- all_time_eur: {all_time_revenue:.2f}")
    lines.append("")
    lines.append("## Delivery System")
    for name, status in _deliverable_status():
        lines.append(f"- {name}: {status}")
    lines.append("")
    lines.append("## Automation Activity")
    lines.append("- latest_content_runs:")
    for path in latest_runs:
        lines.append(f"  - {path.name}")
    if not latest_runs:
        lines.append("  - none")
    lines.append("- latest_parallel_chat_runs:")
    for path in latest_parallel:
        lines.append(f"  - {path.name}")
    if not latest_parallel:
        lines.append("  - none")
    lines.append("- latest_voice_events:")
    for path in latest_voice:
        lines.append(f"  - {path}")
    if not latest_voice:
        lines.append("  - none")
    lines.append("")
    lines.append("## Think and Grow Rich Execution")
    principles = config.get("think_and_grow_rich_execution", [])
    if isinstance(principles, list) and principles:
        for item in principles[:5]:
            principle = str(item.get("principle", "")).strip()
            daily_action = str(item.get("daily_action", "")).strip()
            if principle and daily_action:
                lines.append(f"- {principle}: {daily_action}")
    else:
        lines.append("- no principle map configured")
    lines.append("")
    lines.append("## Next Moves")
    if gap_min > 0:
        lines.append("- Build one offer sprint and book sales calls daily until gap closes.")
    else:
        lines.append("- Keep retention and upsell cadence active to protect baseline revenue.")
    lines.append("- Run `multi-chat` daily for offer, outreach and objection handling.")
    lines.append("- Capture voice decisions so orchestration does not depend on memory.")
    lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_output_if_requested(content: str, out_path: Optional[str]) -> Optional[Path]:
    if not out_path:
        return None
    target = Path(out_path)
    write_text(target, content)
    return target


@dataclass
class ParallelChatResult:
    agent_id: int
    provider: str
    model: str
    ok: bool
    latency_sec: float
    text: str
    usage: Dict[str, Any]
    error: str = ""


def _dedupe_specs(specs: Sequence[ModelSpec]) -> List[ModelSpec]:
    seen = set()
    unique: List[ModelSpec] = []
    for spec in specs:
        key = (spec.provider, spec.model)
        if key in seen:
            continue
        seen.add(key)
        unique.append(spec)
    return unique


def _build_agent_specs(base_specs: Sequence[ModelSpec], agent_count: int) -> List[Tuple[int, ModelSpec]]:
    if not base_specs:
        return []
    if agent_count <= 0:
        agent_count = len(base_specs)
    jobs: List[Tuple[int, ModelSpec]] = []
    for idx in range(agent_count):
        spec = base_specs[idx % len(base_specs)]
        jobs.append((idx + 1, spec))
    return jobs


def run_parallel_chat(
    router: Router,
    prompt: str,
    task_type: str,
    tier: Optional[str],
    agent_count: int,
    execute: bool,
    temperature: Optional[float],
    max_output_tokens: Optional[int],
    diversify: bool,
) -> List[ParallelChatResult]:
    specs = _dedupe_specs(router.select_models(task_type, override_tier=tier))
    jobs = _build_agent_specs(specs, agent_count)

    if not jobs:
        return [
            ParallelChatResult(
                agent_id=1,
                provider="",
                model="",
                ok=False,
                latency_sec=0.0,
                text="",
                usage={},
                error=f"No models configured for task_type={task_type}.",
            )
        ]

    if not execute:
        return [
            ParallelChatResult(
                agent_id=agent_id,
                provider=spec.provider,
                model=spec.model,
                ok=True,
                latency_sec=0.0,
                text=f"[DRY RUN] Agent {agent_id} would run on {spec.provider}/{spec.model}",
                usage={},
            )
            for agent_id, spec in jobs
        ]

    results: List[ParallelChatResult] = []

    def _worker(agent_id: int, spec: ModelSpec) -> ParallelChatResult:
        started = time.time()
        provider_cfg = router.provider_config(spec.provider)
        provider = provider_from_dict(spec.provider, provider_cfg)
        agent_prompt = prompt
        if diversify:
            agent_prompt = (
                prompt.strip()
                + f"\n\n[Agent Variation]\nDu bist Agent {agent_id}. "
                "Gib einen eigenen, konkret umsetzbaren Angle ohne Wiederholung."
            )
        try:
            response = provider.chat(
                model=spec.model,
                messages=[{"role": "user", "content": agent_prompt}],
                system_prompt=(
                    "Du bist ein pragmatischer Operator. "
                    "Antworte konkret in Schritten mit Zahlen und klaren Prioritaeten."
                ),
                temperature=temperature if temperature is not None else spec.temperature,
                max_output_tokens=max_output_tokens or spec.max_output_tokens,
            )
            return ParallelChatResult(
                agent_id=agent_id,
                provider=spec.provider,
                model=spec.model,
                ok=True,
                latency_sec=round(time.time() - started, 3),
                text=str(response.get("text", "")),
                usage=response.get("usage", {}) if isinstance(response, dict) else {},
            )
        except ProviderError as exc:
            return ParallelChatResult(
                agent_id=agent_id,
                provider=spec.provider,
                model=spec.model,
                ok=False,
                latency_sec=round(time.time() - started, 3),
                text="",
                usage={},
                error=str(exc),
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            return ParallelChatResult(
                agent_id=agent_id,
                provider=spec.provider,
                model=spec.model,
                ok=False,
                latency_sec=round(time.time() - started, 3),
                text="",
                usage={},
                error=f"Unexpected error: {exc}",
            )

    env_max_workers = 0
    try:
        env_raw = os.getenv("MISSION_MAX_WORKERS", "").strip()
        if env_raw:
            env_max_workers = int(env_raw)
    except Exception:
        env_max_workers = 0

    if env_max_workers > 0:
        max_workers = min(max(1, env_max_workers), len(jobs))
    else:
        max_workers = min(max(1, len(jobs)), 12)
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_worker, agent_id, spec) for agent_id, spec in jobs]
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda item: item.agent_id)
    return results


def write_parallel_chat_outputs(
    run_id: str,
    prompt: str,
    task_type: str,
    tier: Optional[str],
    execute: bool,
    results: Sequence[ParallelChatResult],
) -> Tuple[Path, Path]:
    ensure_dir(RUNS_DIR)
    json_path = RUNS_DIR / f"parallel_chat_{run_id}.json"
    md_path = RUNS_DIR / f"parallel_chat_{run_id}.md"

    payload = {
        "run_id": run_id,
        "task_type": task_type,
        "tier": tier,
        "execute": execute,
        "prompt": prompt,
        "results": [asdict(item) for item in results],
        "created_at": _now_iso(),
    }
    write_json(json_path, payload)

    lines = [f"# Parallel Chat Run ({run_id})", ""]
    lines.append(f"- task_type: {task_type}")
    lines.append(f"- tier: {tier or 'auto'}")
    lines.append(f"- execute: {execute}")
    lines.append("")
    lines.append("## Prompt")
    lines.append(prompt.strip())
    lines.append("")
    lines.append("## Agent Outputs")
    for item in results:
        header = f"### Agent {item.agent_id} ({item.provider}/{item.model})"
        lines.append(header)
        lines.append(f"- ok: {item.ok}")
        lines.append(f"- latency_sec: {item.latency_sec}")
        if item.error:
            lines.append(f"- error: {item.error}")
        lines.append("")
        if item.text.strip():
            lines.append(item.text.strip())
        else:
            lines.append("[empty]")
        lines.append("")
    write_text(md_path, "\n".join(lines).strip() + "\n")
    return json_path, md_path


def _days_left_in_month(today: dt.date) -> int:
    _, month_end = _month_bounds(today)
    return max(1, (month_end - today).days + 1)


def build_sprint_plan(
    config: Dict[str, Any],
    state: Dict[str, Any],
    target_eur: Optional[float],
    avg_deal_eur: Optional[float],
    close_rate: Optional[float],
    meeting_rate: Optional[float],
) -> str:
    assumptions = config.get("sales_assumptions", {})
    today = dt.date.today()
    current_revenue = _current_month_revenue(state.get("revenue_entries", []), today)
    active_target = _active_target(config, str(state.get("created_at", _now_iso())), today)

    target_value = float(target_eur if target_eur is not None else active_target.get("monthly_min_eur", 5000))
    avg_deal = float(avg_deal_eur if avg_deal_eur is not None else assumptions.get("default_avg_deal_eur", 2500))
    close = float(close_rate if close_rate is not None else assumptions.get("default_close_rate", 0.2))
    meeting = float(meeting_rate if meeting_rate is not None else assumptions.get("default_meeting_rate", 0.3))

    close = max(0.01, min(close, 1.0))
    meeting = max(0.01, min(meeting, 1.0))
    avg_deal = max(100.0, avg_deal)

    revenue_gap = max(0.0, target_value - current_revenue)
    deals_needed = int(math.ceil(revenue_gap / avg_deal)) if revenue_gap > 0 else 0
    calls_needed = int(math.ceil(deals_needed / close)) if deals_needed > 0 else 0
    leads_needed = int(math.ceil(calls_needed / meeting)) if calls_needed > 0 else 0

    days_left = _days_left_in_month(today)
    daily_leads = int(math.ceil(leads_needed / days_left)) if leads_needed > 0 else 0
    daily_calls = int(math.ceil(calls_needed / max(1, days_left // 7 or 1))) if calls_needed > 0 else 0

    principles = config.get("think_and_grow_rich_execution", [])
    lines: List[str] = []
    lines.append(f"# 7-Day Sprint Plan ({today.isoformat()})")
    lines.append("")
    lines.append("## Revenue Math")
    lines.append(f"- current_month_eur: {current_revenue:.2f}")
    lines.append(f"- target_month_eur: {target_value:.2f}")
    lines.append(f"- revenue_gap_eur: {revenue_gap:.2f}")
    lines.append(f"- avg_deal_eur: {avg_deal:.2f}")
    lines.append(f"- deals_needed: {deals_needed}")
    lines.append(f"- calls_needed: {calls_needed}")
    lines.append(f"- leads_needed: {leads_needed}")
    lines.append(f"- days_left_in_month: {days_left}")
    lines.append(f"- daily_lead_target: {daily_leads}")
    lines.append(f"- weekly_call_target: {daily_calls}")
    lines.append("")
    lines.append("## Offer Ladder")
    offers = config.get("offer_stack", [])
    if isinstance(offers, list) and offers:
        for item in offers:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- {item.get('name', 'offer')}: {item.get('price_eur', 'n/a')} EUR | {item.get('promise', '')}"
            )
    else:
        lines.append("- no offer stack configured")
    lines.append("")
    lines.append("## Daily Operating Rhythm")
    lines.append("1. Morning: run `status`, set one numeric goal, choose one offer.")
    lines.append("2. Build: run `multi-chat` for hooks, objections, and proposal copy.")
    lines.append("3. Sell: execute outreach blocks until daily lead target is done.")
    lines.append("4. Close: run one call block and send same-day proposal.")
    lines.append("5. Night: log revenue/win and update next-day priority.")
    lines.append("")
    lines.append("## Think and Grow Rich -> Execution")
    if isinstance(principles, list) and principles:
        for item in principles:
            if not isinstance(item, dict):
                continue
            principle = str(item.get("principle", "")).strip()
            daily_action = str(item.get("daily_action", "")).strip()
            weekly_control = str(item.get("weekly_control", "")).strip()
            if not principle:
                continue
            lines.append(f"- {principle}: {daily_action} | Weekly check: {weekly_control}")
    else:
        lines.append("- no principle execution map configured")
    lines.append("")
    return "\n".join(lines).strip() + "\n"


def add_revenue_entry(state: Dict[str, Any], amount_eur: float, source: str, date: str, note: str) -> Dict[str, Any]:
    entry = {
        "date": date,
        "amount_eur": round(amount_eur, 2),
        "source": source.strip() or "unspecified",
        "note": note.strip(),
        "created_at": _now_iso(),
    }
    entries = state.setdefault("revenue_entries", [])
    if not isinstance(entries, list):
        state["revenue_entries"] = []
        entries = state["revenue_entries"]
    entries.append(entry)
    return entry


def add_win(state: Dict[str, Any], win: str) -> Dict[str, Any]:
    item = {
        "text": win.strip(),
        "created_at": _now_iso(),
    }
    wins = state.setdefault("wins", [])
    if not isinstance(wins, list):
        state["wins"] = []
        wins = state["wins"]
    wins.append(item)
    return item


def _print(msg: str) -> None:
    sys.stdout.write(msg.rstrip() + "\n")


def _resolve_transcribe_cli(custom_path: Optional[str]) -> Path:
    if custom_path:
        return Path(custom_path)
    env_path = os.environ.get("TRANSCRIBE_CLI")
    if env_path:
        return Path(env_path)
    return DEFAULT_TRANSCRIBE_CLI


def transcribe_audio(audio_path: Path, out_dir: Path, language: Optional[str], cli_path: Path) -> Path:
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")
    if not cli_path.exists():
        raise SystemExit(
            f"Transcribe CLI not found: {cli_path}\n"
            "Set TRANSCRIBE_CLI or pass --transcribe-cli to point to transcribe_diarize.py."
        )
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is missing. Export key first, then retry voice intake.")

    ensure_dir(out_dir)
    transcript_path = out_dir / f"{audio_path.stem}.transcript.txt"
    cmd = [
        sys.executable,
        str(cli_path),
        str(audio_path),
        "--response-format",
        "text",
        "--out",
        str(transcript_path),
    ]
    if language:
        cmd.extend(["--language", language])

    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0:
        raise SystemExit(f"Voice transcription failed:\n{process.stderr.strip()}")
    if not transcript_path.exists():
        raise SystemExit("Transcription finished without transcript file.")
    return transcript_path


def infer_voice_intent(text: str) -> Dict[str, Any]:
    raw = text.strip()
    lower = raw.lower()

    if not raw:
        return {"intent": "empty", "action": "none", "args": []}

    if "status" in lower or "lage" in lower:
        return {"intent": "status", "action": "status", "args": []}

    if "plan" in lower or "sprint" in lower or "wochenplan" in lower:
        return {"intent": "plan", "action": "plan", "args": []}

    if "threads" in lower:
        return {"intent": "workflow", "action": "workflow", "args": ["threads"]}

    if "tweets" in lower:
        return {"intent": "workflow", "action": "workflow", "args": ["tweets"]}

    if "prompts" in lower:
        return {"intent": "workflow", "action": "workflow", "args": ["prompts"]}

    if "monet" in lower:
        return {"intent": "workflow", "action": "workflow", "args": ["monetization"]}

    if "full" in lower or "komplett" in lower or "alles" in lower:
        return {"intent": "workflow", "action": "workflow", "args": ["full"]}

    if "multi" in lower or "parallel" in lower or "mehrere" in lower:
        return {"intent": "multi-chat", "action": "multi-chat", "args": []}

    return {"intent": "note", "action": "none", "args": []}


def dispatch_voice_intent(
    intent: Dict[str, Any],
    transcript_text: str,
    router: Router,
    execute: bool,
    agent_count: int,
    task_type: str,
    tier: Optional[str],
) -> Dict[str, Any]:
    action = intent.get("action")
    if action == "status":
        config = load_mission_config()
        state = load_state()
        report = build_status_report(config, state)
        return {"action": "status", "report": report}

    if action == "plan":
        config = load_mission_config()
        state = load_state()
        plan = build_sprint_plan(config, state, None, None, None, None)
        return {"action": "plan", "report": plan}

    if action == "workflow":
        workflow = "full"
        args = intent.get("args", [])
        if isinstance(args, list) and args:
            workflow = str(args[0])
        command = [sys.executable, "-m", "automation", "run", "--workflow", workflow]
        if execute:
            command.append("--execute")
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return {
            "action": "workflow",
            "workflow": workflow,
            "command": command,
            "exit_code": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
        }

    if action == "multi-chat":
        results = run_parallel_chat(
            router=router,
            prompt=transcript_text,
            task_type=task_type,
            tier=tier,
            agent_count=agent_count,
            execute=execute,
            temperature=None,
            max_output_tokens=None,
            diversify=True,
        )
        return {"action": "multi-chat", "results": [asdict(r) for r in results]}

    return {"action": "none", "note": transcript_text}


def cmd_status(args: argparse.Namespace) -> int:
    config = load_mission_config(Path(args.config) if args.config else None)
    state = load_state(Path(args.state) if args.state else None)
    report = build_status_report(config, state)
    _print(report)
    out = write_output_if_requested(report, args.out)
    if out:
        _print(f"Wrote {out}")
    return 0


def cmd_revenue_add(args: argparse.Namespace) -> int:
    state_path = Path(args.state) if args.state else None
    state = load_state(state_path)
    date = args.date or dt.date.today().isoformat()
    if _safe_parse_date(date) is None:
        raise SystemExit(f"Invalid --date: {date}. Expected YYYY-MM-DD.")
    entry = add_revenue_entry(
        state,
        amount_eur=float(args.amount),
        source=args.source,
        date=date,
        note=args.note or "",
    )
    path = save_state(state, state_path)
    _print(f"Added revenue entry: {entry}")
    _print(f"State saved: {path}")
    return 0


def cmd_revenue_list(args: argparse.Namespace) -> int:
    state = load_state(Path(args.state) if args.state else None)
    entries = state.get("revenue_entries", [])
    if not isinstance(entries, list) or not entries:
        _print("No revenue entries.")
        return 0
    entries_sorted = sorted(entries, key=lambda x: str(x.get("date", "")), reverse=True)
    for item in entries_sorted[: args.limit]:
        _print(
            f"{item.get('date', 'n/a')} | {float(item.get('amount_eur', 0)):.2f} EUR | "
            f"{item.get('source', 'n/a')} | {item.get('note', '')}"
        )
    return 0


def cmd_win_add(args: argparse.Namespace) -> int:
    state_path = Path(args.state) if args.state else None
    state = load_state(state_path)
    item = add_win(state, args.text)
    path = save_state(state, state_path)
    _print(f"Added win: {item}")
    _print(f"State saved: {path}")
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    config = load_mission_config(Path(args.config) if args.config else None)
    state = load_state(Path(args.state) if args.state else None)
    plan = build_sprint_plan(
        config=config,
        state=state,
        target_eur=args.target,
        avg_deal_eur=args.avg_deal,
        close_rate=args.close_rate,
        meeting_rate=args.meeting_rate,
    )
    _print(plan)
    out = write_output_if_requested(plan, args.out)
    if out:
        _print(f"Wrote {out}")
    return 0


def _prompt_from_args(prompt: Optional[str], prompt_file: Optional[str]) -> str:
    if prompt and prompt.strip():
        return prompt.strip()
    if prompt_file:
        path = Path(prompt_file)
        if not path.exists():
            raise SystemExit(f"Prompt file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
    raise SystemExit("Missing prompt. Use --prompt or --prompt-file.")


def cmd_multi_chat(args: argparse.Namespace) -> int:
    prompt = _prompt_from_args(args.prompt, args.prompt_file)
    router_cfg = load_router_config(Path(args.router_config) if args.router_config else None)
    router = Router(router_cfg)
    run_id = args.run_id or timestamp_id()
    results = run_parallel_chat(
        router=router,
        prompt=prompt,
        task_type=args.task_type,
        tier=args.tier,
        agent_count=args.agents,
        execute=args.execute,
        temperature=args.temperature,
        max_output_tokens=args.max_output_tokens,
        diversify=args.diversify,
    )
    json_path, md_path = write_parallel_chat_outputs(
        run_id=run_id,
        prompt=prompt,
        task_type=args.task_type,
        tier=args.tier,
        execute=args.execute,
        results=results,
    )
    ok_count = sum(1 for item in results if item.ok)
    _print(f"Parallel chat finished: {ok_count}/{len(results)} successful")
    _print(f"JSON: {json_path}")
    _print(f"MD:   {md_path}")
    return 0


def cmd_voice(args: argparse.Namespace) -> int:
    router_cfg = load_router_config(Path(args.router_config) if args.router_config else None)
    router = Router(router_cfg)
    run_id = args.run_id or timestamp_id()
    run_dir = RUNS_DIR / f"voice_{run_id}"
    ensure_dir(run_dir)

    cli_path = _resolve_transcribe_cli(args.transcribe_cli)
    transcript_path = transcribe_audio(
        audio_path=Path(args.audio),
        out_dir=run_dir,
        language=args.language,
        cli_path=cli_path,
    )
    transcript = transcript_path.read_text(encoding="utf-8").strip()
    intent = infer_voice_intent(transcript)

    event: Dict[str, Any] = {
        "run_id": run_id,
        "audio": str(args.audio),
        "transcript_file": str(transcript_path),
        "transcript": transcript,
        "intent": intent,
        "created_at": _now_iso(),
    }

    dispatch_data: Dict[str, Any] = {}
    if args.dispatch:
        dispatch_data = dispatch_voice_intent(
            intent=intent,
            transcript_text=transcript,
            router=router,
            execute=args.execute,
            agent_count=args.agents,
            task_type=args.task_type,
            tier=args.tier,
        )
        event["dispatch"] = dispatch_data
        if isinstance(dispatch_data, dict) and dispatch_data.get("action") in {"status", "plan"}:
            report_text = str(dispatch_data.get("report", ""))
            if report_text.strip():
                write_text(run_dir / f"{dispatch_data['action']}.md", report_text)

    write_json(run_dir / "voice_event.json", event)

    state = load_state(Path(args.state) if args.state else None)
    state["last_voice_command"] = {
        "run_id": run_id,
        "transcript": transcript,
        "intent": intent,
        "created_at": _now_iso(),
    }
    save_state(state, Path(args.state) if args.state else None)

    _print(f"Transcript: {transcript_path}")
    _print(f"Intent: {json.dumps(intent, ensure_ascii=False)}")
    _print(f"Event: {run_dir / 'voice_event.json'}")
    if args.dispatch:
        _print(f"Dispatch action: {dispatch_data.get('action', 'none')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mission control for AI orchestration + revenue execution")
    parser.add_argument("--config", default=None, help="Path to mission control config JSON")
    parser.add_argument("--state", default=None, help="Path to mission control state JSON")

    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="Show mission control status")
    p_status.add_argument("--out", default=None, help="Write report to file")
    p_status.set_defaults(func=cmd_status)

    p_rev_add = sub.add_parser("revenue-add", help="Add revenue entry")
    p_rev_add.add_argument("--amount", type=float, required=True, help="Revenue amount in EUR")
    p_rev_add.add_argument("--source", default="client", help="Revenue source label")
    p_rev_add.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today)")
    p_rev_add.add_argument("--note", default="", help="Optional note")
    p_rev_add.set_defaults(func=cmd_revenue_add)

    p_rev_list = sub.add_parser("revenue-list", help="List revenue entries")
    p_rev_list.add_argument("--limit", type=int, default=30, help="Number of entries to show")
    p_rev_list.set_defaults(func=cmd_revenue_list)

    p_win_add = sub.add_parser("win-add", help="Log a daily/weekly win")
    p_win_add.add_argument("text", help="Win text")
    p_win_add.set_defaults(func=cmd_win_add)

    p_plan = sub.add_parser("plan", help="Build 7-day sprint plan")
    p_plan.add_argument("--target", type=float, default=None, help="Monthly revenue target EUR")
    p_plan.add_argument("--avg-deal", type=float, default=None, help="Average deal size EUR")
    p_plan.add_argument("--close-rate", type=float, default=None, help="Close rate (0-1)")
    p_plan.add_argument("--meeting-rate", type=float, default=None, help="Lead->meeting rate (0-1)")
    p_plan.add_argument("--out", default=None, help="Write plan to file")
    p_plan.set_defaults(func=cmd_plan)

    p_chat = sub.add_parser("multi-chat", help="Run many AI chats in parallel")
    p_chat.add_argument("--prompt", default=None, help="Prompt text")
    p_chat.add_argument("--prompt-file", default=None, help="Path to prompt file")
    p_chat.add_argument("--task-type", default="strategy", help="Routing task type")
    p_chat.add_argument("--tier", default=None, help="Force model tier (cheap|balanced|premium)")
    p_chat.add_argument("--agents", type=int, default=6, help="Number of parallel agents")
    p_chat.add_argument("--execute", action="store_true", help="Execute API calls (default: dry-run)")
    p_chat.add_argument("--temperature", type=float, default=None)
    p_chat.add_argument("--max-output-tokens", type=int, default=None)
    p_chat.add_argument("--diversify", action="store_true", help="Add per-agent variation instruction")
    p_chat.add_argument("--router-config", default=None, help="Override router config path")
    p_chat.add_argument("--run-id", default=None, help="Override run id")
    p_chat.set_defaults(func=cmd_multi_chat)

    p_voice = sub.add_parser("voice", help="Transcribe voice command and optional dispatch")
    p_voice.add_argument("--audio", required=True, help="Path to audio file")
    p_voice.add_argument("--language", default="de", help="Language hint for transcription")
    p_voice.add_argument("--dispatch", action="store_true", help="Dispatch inferred command")
    p_voice.add_argument("--execute", action="store_true", help="Execute dispatched actions (default dry-run)")
    p_voice.add_argument("--agents", type=int, default=6, help="Agent count for inferred multi-chat")
    p_voice.add_argument("--task-type", default="strategy", help="Task type for inferred multi-chat")
    p_voice.add_argument("--tier", default=None, help="Tier for inferred multi-chat")
    p_voice.add_argument("--router-config", default=None, help="Override router config path")
    p_voice.add_argument("--transcribe-cli", default=None, help="Path to transcribe_diarize.py")
    p_voice.add_argument("--run-id", default=None, help="Override run id")
    p_voice.set_defaults(func=cmd_voice)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
