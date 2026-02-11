#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


TIMESTAMP_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2}T[0-9:.]+Z)\s+(?P<body>.*)$")


@dataclass
class RunEntry:
    job_id: str
    ts: datetime
    status: str
    duration_ms: int
    error: Optional[str]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso_utc(raw: str) -> Optional[datetime]:
    value = raw.strip()
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except ValueError:
        return None


def parse_epoch_ms(raw: Any) -> Optional[datetime]:
    try:
        ms = int(raw)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def classify_error(message: str) -> str:
    lower = message.lower()
    if "no api key found" in lower:
        return "auth_missing"
    if "rate_limit" in lower or "429" in lower or "cooldown" in lower:
        return "rate_limit"
    if "delivery target is missing" in lower:
        return "delivery_target_missing"
    if "billing error" in lower or "insufficient balance" in lower:
        return "billing"
    if "provider returned error" in lower:
        return "provider_error"
    return "other"


def p95(values: List[int]) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    idx = int(round(0.95 * (len(ordered) - 1)))
    return ordered[idx]


def load_runs(runs_dir: Path, cutoff: datetime) -> List[RunEntry]:
    entries: List[RunEntry] = []
    for path in sorted(runs_dir.glob("*.jsonl")):
        for row in iter_jsonl(path):
            if row.get("action") != "finished":
                continue
            ts = parse_epoch_ms(row.get("ts")) or parse_epoch_ms(row.get("runAtMs"))
            if ts is None or ts < cutoff:
                continue
            entries.append(
                RunEntry(
                    job_id=str(row.get("jobId", "")),
                    ts=ts,
                    status=str(row.get("status", "unknown")),
                    duration_ms=int(row.get("durationMs") or 0),
                    error=str(row.get("error")) if row.get("error") else None,
                )
            )
    entries.sort(key=lambda item: item.ts)
    return entries


def parse_gateway_models(log_path: Path, cutoff: datetime) -> Counter[str]:
    models: Counter[str] = Counter()
    if not log_path.exists():
        return models
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = TIMESTAMP_RE.match(line.rstrip("\n"))
            if not match:
                continue
            ts = parse_iso_utc(match.group("ts"))
            if ts is None or ts < cutoff:
                continue
            body = match.group("body")
            if "agent model:" in body:
                model = body.split("agent model:", 1)[1].strip()
                if model:
                    models[model] += 1
    return models


def parse_gateway_errors(log_path: Path, cutoff: datetime) -> Counter[str]:
    categories: Counter[str] = Counter()
    if not log_path.exists():
        return categories
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = TIMESTAMP_RE.match(line.rstrip("\n"))
            if not match:
                continue
            ts = parse_iso_utc(match.group("ts"))
            if ts is None or ts < cutoff:
                continue
            body = match.group("body")
            if "[diagnostic] lane task error" not in body:
                continue
            err_idx = body.find('error="')
            if err_idx >= 0:
                snippet = body[err_idx + 7 :]
                if snippet.endswith('"'):
                    snippet = snippet[:-1]
                categories[classify_error(snippet)] += 1
            else:
                categories["other"] += 1
    return categories


def build_markdown(
    *,
    generated_at: datetime,
    hours: int,
    jobs: List[Dict[str, Any]],
    runs: List[RunEntry],
    models: Counter[str],
    gateway_error_categories: Counter[str],
) -> str:
    total_runs = len(runs)
    ok_runs = sum(1 for run in runs if run.status == "ok")
    err_runs = total_runs - ok_runs
    error_rate = (err_runs / total_runs * 100.0) if total_runs else 0.0
    durations = [run.duration_ms for run in runs if run.duration_ms > 0]
    avg_duration = int(sum(durations) / len(durations)) if durations else 0
    p95_duration = p95(durations)

    by_job: Dict[str, List[RunEntry]] = defaultdict(list)
    for run in runs:
        by_job[run.job_id].append(run)

    job_rows = []
    for job in jobs:
        job_id = str(job.get("id", ""))
        job_name = str(job.get("name", ""))
        job_runs = by_job.get(job_id, [])
        j_total = len(job_runs)
        j_ok = sum(1 for item in job_runs if item.status == "ok")
        j_err = j_total - j_ok
        j_avg = int(sum(item.duration_ms for item in job_runs) / j_total) if j_total else 0
        last_status = str(job.get("state", {}).get("lastStatus") or "n/a")
        job_rows.append((job_name, j_total, j_ok, j_err, j_avg, last_status))

    lines: List[str] = []
    lines.append("# OpenClaw Monitoring (24h)")
    lines.append("")
    lines.append(f"- generated_at_utc: {generated_at.isoformat()}")
    lines.append(f"- window_hours: {hours}")
    lines.append(f"- configured_jobs: {len(jobs)}")
    lines.append("")
    lines.append("## Run Metrics")
    lines.append(f"- total_finished_runs: {total_runs}")
    lines.append(f"- successful_runs: {ok_runs}")
    lines.append(f"- failed_runs: {err_runs}")
    lines.append(f"- error_rate_percent: {error_rate:.2f}")
    lines.append(f"- avg_duration_ms: {avg_duration}")
    lines.append(f"- p95_duration_ms: {p95_duration}")
    lines.append("")
    lines.append("## Gateway Model Usage (log-based)")
    if models:
        for model, count in models.most_common():
            lines.append(f"- {model}: {count}")
    else:
        lines.append("- no model switches found in the selected window")
    lines.append("")
    lines.append("## Error Categories (gateway diagnostics)")
    if gateway_error_categories:
        for category, count in gateway_error_categories.most_common():
            lines.append(f"- {category}: {count}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Jobs")
    lines.append("| job | runs_24h | ok | error | avg_ms | last_status |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for name, j_total, j_ok, j_err, j_avg, last_status in job_rows:
        safe_name = name.replace("|", "/")
        lines.append(f"| {safe_name} | {j_total} | {j_ok} | {j_err} | {j_avg} | {last_status} |")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a 24h OpenClaw monitoring report.")
    parser.add_argument("--hours", type=int, default=24, help="Lookback window in hours (default: 24)")
    parser.add_argument("--state-dir", default="~/.openclaw", help="OpenClaw state directory")
    parser.add_argument("--log-dir", default="/tmp/openclaw", help="OpenClaw log directory")
    parser.add_argument(
        "--out-dir",
        default="reports/openclaw_monitoring",
        help="Output directory for markdown/json reports",
    )
    args = parser.parse_args()

    now = now_utc()
    cutoff = now - timedelta(hours=max(1, args.hours))

    state_dir = Path(args.state_dir).expanduser()
    log_dir = Path(args.log_dir).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs_path = state_dir / "cron" / "jobs.json"
    runs_dir = state_dir / "cron" / "runs"
    gateway_out_path = log_dir / "gateway.launchd.out.log"
    gateway_err_path = log_dir / "gateway.launchd.err.log"

    if not jobs_path.exists():
        raise SystemExit(f"Missing jobs file: {jobs_path}")
    if not runs_dir.exists():
        raise SystemExit(f"Missing runs directory: {runs_dir}")

    jobs_doc = read_json(jobs_path)
    jobs = list(jobs_doc.get("jobs") or [])
    runs = load_runs(runs_dir, cutoff)
    models = parse_gateway_models(gateway_out_path, cutoff)
    gateway_error_categories = parse_gateway_errors(gateway_err_path, cutoff)

    markdown = build_markdown(
        generated_at=now,
        hours=max(1, args.hours),
        jobs=jobs,
        runs=runs,
        models=models,
        gateway_error_categories=gateway_error_categories,
    )

    payload = {
        "generated_at_utc": now.isoformat(),
        "window_hours": max(1, args.hours),
        "cutoff_utc": cutoff.isoformat(),
        "configured_jobs": len(jobs),
        "runs_24h": [
            {
                "job_id": item.job_id,
                "ts": item.ts.isoformat(),
                "status": item.status,
                "duration_ms": item.duration_ms,
                "error": item.error,
            }
            for item in runs
        ],
        "gateway_model_usage": dict(models),
        "gateway_error_categories": dict(gateway_error_categories),
        "jobs": jobs,
    }

    stamp = now.strftime("%Y%m%d_%H%M%S")
    md_path = out_dir / f"openclaw_monitor_{stamp}.md"
    json_path = out_dir / f"openclaw_monitor_{stamp}.json"
    latest_md = out_dir / "latest.md"
    latest_json = out_dir / "latest.json"

    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    latest_md.write_text(markdown, encoding="utf-8")
    latest_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    print(f"[ok] markdown: {md_path}")
    print(f"[ok] json: {json_path}")
    print(f"[ok] latest markdown: {latest_md}")
    print(f"[ok] latest json: {latest_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
