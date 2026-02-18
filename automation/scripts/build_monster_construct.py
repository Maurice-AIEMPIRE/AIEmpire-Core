#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MD_OUTPUT = ROOT / "00_SYSTEM/MONSTER_CONSTRUCT_MASTER.md"
DEFAULT_JSON_OUTPUT = ROOT / "00_SYSTEM/MONSTER_CONSTRUCT_MASTER.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def pick_latest(glob_pattern: str) -> Path | None:
    candidates = sorted(ROOT.glob(glob_pattern), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def load_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists() or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return data if isinstance(data, dict) else {}


def load_text(path: Path | None) -> str:
    if not path or not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:  # noqa: BLE001
        return ""


def parse_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def job_healthy(job: dict[str, Any]) -> bool:
    state = str(job.get("state") or "").lower()
    exit_code = str(job.get("last_exit_code") or "")
    return state == "running" or exit_code in {"0", "(never exited)"}


def summarize_jobs(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(jobs)
    running = 0
    healthy = 0
    exit_78 = 0
    nonzero = 0
    jobs_by_label: dict[str, dict[str, Any]] = {}
    active_by_group: dict[str, list[str]] = {}

    for job in jobs:
        label = str(job.get("label") or "")
        group = str(job.get("function_group") or "other")
        state = str(job.get("state") or "").lower()
        exit_code = str(job.get("last_exit_code") or "")
        jobs_by_label[label] = job

        if state == "running":
            running += 1
        if job_healthy(job):
            healthy += 1
            active_by_group.setdefault(group, []).append(label)
        if "78" in exit_code:
            exit_78 += 1
        if exit_code and exit_code not in {"0", "(never exited)"}:
            nonzero += 1

    duplicates = [
        {
            "function_group": group,
            "active_labels": labels,
        }
        for group, labels in sorted(active_by_group.items())
        if len(labels) > 1 and group != "other"
    ]

    return {
        "total": total,
        "running": running,
        "healthy": healthy,
        "exit_78": exit_78,
        "nonzero_exits": nonzero,
        "jobs_by_label": jobs_by_label,
        "active_duplicates": duplicates,
    }


def parse_master_index_counts(index_text: str) -> dict[str, int]:
    total = 0
    revenue = 0
    total_match = re.search(r"Total artifacts:\s*\*\*(\d+)\*\*", index_text)
    revenue_match = re.search(r"Revenue-relevant artifacts:\s*\*\*(\d+)\*\*", index_text)
    if total_match:
        total = parse_int(total_match.group(1))
    if revenue_match:
        revenue = parse_int(revenue_match.group(1))
    return {"total_artifacts": total, "revenue_relevant_artifacts": revenue}


def canonical_rows(runtime_map: dict[str, Any], jobs_by_label: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    entries = runtime_map.get("entries", [])
    if not isinstance(entries, list):
        return []
    rows: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("canonical_label") or "")
        job = jobs_by_label.get(label, {})
        if job:
            health = "healthy" if job_healthy(job) else "degraded"
            state = job.get("state")
            last_exit = job.get("last_exit_code")
        else:
            health = "missing"
            state = "missing"
            last_exit = None
        rows.append(
            {
                "function_group": entry.get("function_group"),
                "canonical_label": label,
                "fallback_label": entry.get("fallback_label"),
                "owner": entry.get("owner"),
                "schedule_window": entry.get("schedule_window"),
                "verification_command": entry.get("verification_command"),
                "state": state,
                "last_exit_code": last_exit,
                "health": health,
            }
        )
    return rows


def extract_top_gaps(gaps: list[dict[str, Any]], *, limit: int = 8) -> list[dict[str, Any]]:
    if not isinstance(gaps, list):
        return []
    ordered = sorted(
        [g for g in gaps if isinstance(g, dict)],
        key=lambda g: (
            {"P0": 0, "P1": 1, "P2": 2}.get(str(g.get("priority", "P2")), 3),
            str(g.get("type", "")),
            str(g.get("id", "")),
        ),
    )
    return ordered[: max(0, limit)]


def build_actions(
    *,
    health_score: int,
    endpoints_down: list[str],
    duplicates: list[dict[str, Any]],
    runtime_blockers: list[dict[str, Any]],
    revenue_blockers: list[dict[str, Any]],
    kpi: dict[str, Any],
    canonical: list[dict[str, Any]],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []

    if endpoints_down:
        actions.append(
            {
                "priority": "P0_RUNTIME_BREAK",
                "action": "Restore all critical local endpoints before heavy automation.",
                "owner": "Ops",
                "eta": "today",
                "impact": "Stops crash/degrade loops and re-enables execution.",
                "risk": "High if skipped.",
                "verification_command": "python3 automation/scripts/preflight_gate.py",
            }
        )

    if duplicates:
        actions.append(
            {
                "priority": "P0_RUNTIME_BREAK",
                "action": "Disable shadow LaunchAgents and keep only canonical labels per function group.",
                "owner": "Ops",
                "eta": "today",
                "impact": "Removes drift and conflicting orchestration.",
                "risk": "High if skipped.",
                "verification_command": "python3 automation/scripts/consolidate_launchd_runtime.py --dry-run",
            }
        )

    if runtime_blockers:
        actions.append(
            {
                "priority": "P0_RUNTIME_BREAK",
                "action": "Repair canonical jobs with non-zero exits and validate log/workdir paths.",
                "owner": "Ops",
                "eta": "today",
                "impact": "Moves critical jobs to stable `running/healthy`.",
                "risk": "High if skipped.",
                "verification_command": "python3 automation/scripts/audit_infra_runtime.py --mode snapshot --redact-secrets true",
            }
        )

    has_stripe_blocker = any("stripe" in str(b.get("id", "")).lower() for b in revenue_blockers)
    if has_stripe_blocker:
        actions.append(
            {
                "priority": "P1_REVENUE_BLOCKER",
                "action": "Set Stripe key and run sync to create real-cash source-of-truth JSON.",
                "owner": "Revenue Ops",
                "eta": "today",
                "impact": "Switches from projection-only to real revenue tracking.",
                "risk": "High if skipped.",
                "verification_command": "automation/scripts/run_stripe_sync.sh",
            }
        )

    has_publish_blocker = any("shorts" in str(b.get("id", "")).lower() for b in revenue_blockers)
    if has_publish_blocker:
        actions.append(
            {
                "priority": "P1_REVENUE_BLOCKER",
                "action": "Fix YouTube/TikTok OAuth and publish gate until `published_count > 0` in live runs.",
                "owner": "Distribution",
                "eta": "48h",
                "impact": "Activates 30% autopilot channel output.",
                "risk": "Medium if skipped.",
                "verification_command": "automation/scripts/run_shorts_revenue_autopilot.sh 1 30",
            }
        )

    leads = parse_int(kpi.get("leads", 0))
    offers = parse_int(kpi.get("offers", 0))
    if leads == 0 or offers == 0:
        actions.append(
            {
                "priority": "P1_REVENUE_BLOCKER",
                "action": "Run daily service-outbound block (LinkedIn + email) with fixed quotas.",
                "owner": "Sales",
                "eta": "daily",
                "impact": "Unlocks 70% service-cashflow lane.",
                "risk": "High if skipped.",
                "verification_command": "python3 automation/scripts/write_daily_kpi.py",
            }
        )

    if health_score < 70:
        actions.append(
            {
                "priority": "P2_QUALITY_DRIFT",
                "action": "Run daily monster construct audit and use degrade mode outside 08:00-23:00.",
                "owner": "Ops",
                "eta": "daily",
                "impact": "Stabilizes compute and reduces machine crash risk.",
                "risk": "Medium if skipped.",
                "verification_command": "automation/scripts/run_monster_construct.sh",
            }
        )

    missing_canonical = [row for row in canonical if row.get("health") == "missing"]
    if missing_canonical:
        actions.append(
            {
                "priority": "P2_QUALITY_DRIFT",
                "action": "Register missing canonical runtimes or disable their function groups explicitly.",
                "owner": "Ops",
                "eta": "72h",
                "impact": "Enforces strict no-shadow runtime policy.",
                "risk": "Medium if skipped.",
                "verification_command": "cat 00_SYSTEM/infra/RUNTIME_CANONICAL_MAP_2026-02-18.json",
            }
        )

    return actions[:8]


def build_report(
    *,
    inventory_path: Path | None,
    runtime_map_path: Path | None,
    kpi_path: Path | None,
    chat_index_path: Path | None,
    inventory: dict[str, Any],
    runtime_map: dict[str, Any],
    kpi: dict[str, Any],
    chat_counts: dict[str, int],
) -> tuple[str, dict[str, Any]]:
    jobs = inventory.get("jobs", [])
    endpoints = inventory.get("endpoints", [])
    gaps = inventory.get("gaps", [])
    runtime_blockers = inventory.get("runtime_blockers", [])
    revenue_blockers = inventory.get("revenue_blockers", [])

    job_summary = summarize_jobs(jobs if isinstance(jobs, list) else [])
    canonical = canonical_rows(runtime_map, job_summary["jobs_by_label"])

    endpoints_down = [str(e.get("name")) for e in endpoints if isinstance(e, dict) and not e.get("ok")]
    endpoints_up_count = sum(1 for e in endpoints if isinstance(e, dict) and e.get("ok"))

    revenue = inventory.get("revenue", {})
    real_revenue = parse_float(revenue.get("real_revenue_eur"))
    projected_revenue = parse_float(revenue.get("projected_revenue_eur_24h"))
    published = parse_int((revenue.get("publish_counts") or {}).get("shorts_published_this_run", 0))
    health_score = parse_int(inventory.get("health_score"), 0)
    top_gaps = extract_top_gaps(gaps, limit=10)

    actions = build_actions(
        health_score=health_score,
        endpoints_down=endpoints_down,
        duplicates=job_summary["active_duplicates"],
        runtime_blockers=runtime_blockers if isinstance(runtime_blockers, list) else [],
        revenue_blockers=revenue_blockers if isinstance(revenue_blockers, list) else [],
        kpi=kpi,
        canonical=canonical,
    )

    model = {
        "generated_at": utc_now(),
        "sources": {
            "inventory": str(inventory_path) if inventory_path else None,
            "runtime_map": str(runtime_map_path) if runtime_map_path else None,
            "daily_kpi": str(kpi_path) if kpi_path else None,
            "chat_artifact_index": str(chat_index_path) if chat_index_path else None,
        },
        "summary": {
            "health_score": health_score,
            "jobs_total": job_summary["total"],
            "jobs_running": job_summary["running"],
            "jobs_healthy": job_summary["healthy"],
            "jobs_exit_78": job_summary["exit_78"],
            "runtime_blockers": len(runtime_blockers) if isinstance(runtime_blockers, list) else 0,
            "revenue_blockers": len(revenue_blockers) if isinstance(revenue_blockers, list) else 0,
            "endpoints_total": len(endpoints) if isinstance(endpoints, list) else 0,
            "endpoints_up": endpoints_up_count,
            "endpoints_down": endpoints_down,
            "real_revenue_eur": real_revenue,
            "projected_revenue_eur_24h": projected_revenue,
            "shorts_published_this_run": published,
            "chat_artifacts_total": chat_counts["total_artifacts"],
            "chat_artifacts_revenue_relevant": chat_counts["revenue_relevant_artifacts"],
            "daily_kpi": kpi,
        },
        "canonical_runtime_status": canonical,
        "active_duplicate_groups": job_summary["active_duplicates"],
        "top_gaps": top_gaps,
        "actions": actions,
    }

    lines: list[str] = []
    lines.append("# MONSTER_CONSTRUCT_MASTER")
    lines.append("")
    lines.append(f"- Generated at (UTC): {model['generated_at']}")
    lines.append(f"- Inventory source: `{model['sources']['inventory']}`")
    lines.append(f"- Runtime map source: `{model['sources']['runtime_map']}`")
    lines.append(f"- Daily KPI source: `{model['sources']['daily_kpi']}`")
    lines.append(f"- Chat artifacts source: `{model['sources']['chat_artifact_index']}`")
    lines.append("")
    lines.append("## Executive Status")
    lines.append("")
    lines.append(f"- Health score: **{health_score}/100**")
    lines.append(f"- Jobs: total **{job_summary['total']}**, running **{job_summary['running']}**, healthy **{job_summary['healthy']}**")
    lines.append(f"- Runtime blockers: **{len(runtime_blockers) if isinstance(runtime_blockers, list) else 0}**")
    lines.append(f"- Revenue blockers: **{len(revenue_blockers) if isinstance(revenue_blockers, list) else 0}**")
    lines.append(f"- Endpoints up/down: **{endpoints_up_count}/{len(endpoints) - endpoints_up_count if isinstance(endpoints, list) else 0}**")
    lines.append(f"- Real revenue (EUR): **{real_revenue:.2f}**")
    lines.append(f"- Projected 24h revenue (EUR): **{projected_revenue:.2f}**")
    lines.append(f"- Shorts published (latest run): **{published}**")
    lines.append("")
    lines.append("## Runtime Canonical Map")
    lines.append("")
    lines.append("| Function Group | Canonical Label | State | Last Exit | Health | Window | Owner |")
    lines.append("|---|---|---|---|---|---|---|")
    for row in canonical:
        lines.append(
            "| {group} | `{label}` | {state} | {exit_code} | {health} | {window} | {owner} |".format(
                group=row.get("function_group"),
                label=row.get("canonical_label"),
                state=row.get("state"),
                exit_code=row.get("last_exit_code"),
                health=row.get("health"),
                window=row.get("schedule_window"),
                owner=row.get("owner"),
            )
        )
    lines.append("")
    lines.append("## No Shadow Systems Check")
    lines.append("")
    if job_summary["active_duplicates"]:
        for dup in job_summary["active_duplicates"]:
            labels = ", ".join(f"`{x}`" for x in dup.get("active_labels", []))
            lines.append(f"- DUPLICATE `{dup.get('function_group')}`: {labels}")
    else:
        lines.append("- No active duplicate function groups detected.")
    lines.append("")
    lines.append("## Endpoint Gate")
    lines.append("")
    lines.append("| Endpoint | Status | HTTP | Error |")
    lines.append("|---|---|---|---|")
    for e in endpoints:
        if not isinstance(e, dict):
            continue
        status = "ok" if e.get("ok") else "down"
        lines.append(f"| {e.get('name')} | {status} | {e.get('status_code')} | {e.get('error')} |")
    lines.append("")
    lines.append("## Revenue + KPI Control")
    lines.append("")
    lines.append(f"- Chat artifacts total: **{chat_counts['total_artifacts']}**")
    lines.append(f"- Chat artifacts revenue-relevant: **{chat_counts['revenue_relevant_artifacts']}**")
    lines.append(f"- KPI date: **{kpi.get('date', 'n/a')}**")
    lines.append(
        "- KPI values: leads={leads}, replies={replies}, calls={calls}, offers={offers}, closes={closes}, cash_eur={cash}, published_shorts={shorts}, runtime_incidents={incidents}".format(
            leads=parse_int(kpi.get("leads", 0)),
            replies=parse_int(kpi.get("replies", 0)),
            calls=parse_int(kpi.get("calls", 0)),
            offers=parse_int(kpi.get("offers", 0)),
            closes=parse_int(kpi.get("closes", 0)),
            cash=parse_float(kpi.get("cash_eur", 0.0)),
            shorts=parse_int(kpi.get("published_shorts", 0)),
            incidents=parse_int(kpi.get("runtime_incidents", 0)),
        )
    )
    lines.append("")
    lines.append("## Top Gaps")
    lines.append("")
    for gap in top_gaps:
        lines.append(
            f"- {gap.get('priority')} [{gap.get('type')}]: {gap.get('summary')} (`{gap.get('id')}`)"
        )
    if not top_gaps:
        lines.append("- No gaps detected.")
    lines.append("")
    lines.append("## Execution Queue")
    lines.append("")
    lines.append("| Priority | Action | Owner | ETA | Impact | Risk | Verification Command |")
    lines.append("|---|---|---|---|---|---|---|")
    for action in actions:
        lines.append(
            "| {priority} | {action} | {owner} | {eta} | {impact} | {risk} | `{cmd}` |".format(
                priority=action["priority"],
                action=action["action"],
                owner=action["owner"],
                eta=action["eta"],
                impact=action["impact"],
                risk=action["risk"],
                cmd=action["verification_command"],
            )
        )
    if not actions:
        lines.append("| P2_QUALITY_DRIFT | Maintain current cadence with daily monster audit. | Ops | daily | Keeps system stable. | Low | `automation/scripts/run_monster_construct.sh` |")
    lines.append("")
    lines.append("## One-Command Control")
    lines.append("")
    lines.append("- Full refresh (safe dry-run consolidation):")
    lines.append("```bash")
    lines.append("automation/scripts/run_monster_construct.sh")
    lines.append("```")
    lines.append("")
    lines.append("- Full refresh with aggressive apply consolidation:")
    lines.append("```bash")
    lines.append("automation/scripts/run_monster_construct.sh --apply-consolidation")
    lines.append("```")
    lines.append("")

    return "\n".join(lines) + "\n", model


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a single master control artifact from all AI Empire core snapshots.")
    parser.add_argument("--inventory", default="", help="Path to SYSTEM_INVENTORY json (default: latest by mtime).")
    parser.add_argument("--runtime-map", default="", help="Path to runtime canonical map json (default: latest by mtime).")
    parser.add_argument("--daily-kpi", default="", help="Path to daily KPI json (default: latest by mtime).")
    parser.add_argument("--chat-index", default="", help="Path to MASTER_CHAT_ARTIFACTS_INDEX.md (default: canonical path).")
    parser.add_argument("--output", default=str(DEFAULT_MD_OUTPUT), help="Markdown output path.")
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT), help="JSON output path.")
    args = parser.parse_args()

    inventory_path = Path(args.inventory).expanduser() if args.inventory else pick_latest("00_SYSTEM/infra/SYSTEM_INVENTORY_*.json")
    runtime_map_path = Path(args.runtime_map).expanduser() if args.runtime_map else pick_latest("00_SYSTEM/infra/RUNTIME_CANONICAL_MAP_*.json")
    kpi_path = Path(args.daily_kpi).expanduser() if args.daily_kpi else pick_latest("00_SYSTEM/revenue_system/kpi/daily_kpi_*.json")
    chat_index_path = (
        Path(args.chat_index).expanduser()
        if args.chat_index
        else ROOT / "00_SYSTEM/chat_artifacts/MASTER_CHAT_ARTIFACTS_INDEX.md"
    )

    inventory = load_json(inventory_path)
    runtime_map = load_json(runtime_map_path)
    kpi = load_json(kpi_path)
    chat_counts = parse_master_index_counts(load_text(chat_index_path))

    markdown, model = build_report(
        inventory_path=inventory_path,
        runtime_map_path=runtime_map_path,
        kpi_path=kpi_path,
        chat_index_path=chat_index_path if chat_index_path.exists() else None,
        inventory=inventory,
        runtime_map=runtime_map,
        kpi=kpi,
        chat_counts=chat_counts,
    )

    md_path = Path(args.output).expanduser().resolve()
    json_path = Path(args.json_output).expanduser().resolve()
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[monster] markdown={md_path}")
    print(f"[monster] json={json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
