#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


ROOT = Path(__file__).resolve().parents[2]
HANDOFF_DIR = ROOT / "00_SYSTEM" / "thread_handoffs"
CHRONIK_PATH = ROOT / "00_SYSTEM" / "project_chronik.md"


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def _timestamp_local() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _latest_by_glob(pattern: str) -> Optional[Path]:
    files = list(ROOT.glob(pattern))
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def _cmd(args: list[str]) -> str:
    try:
        out = subprocess.check_output(args, cwd=ROOT, stderr=subprocess.STDOUT, text=True)
        return out.strip()
    except Exception:
        return ""


def _build_resume_prompt(
    handoff_path: Path,
    shorts_summary: Dict[str, Any],
    yt_summary: Dict[str, Any],
) -> str:
    return (
        "Neuer Thread-Start:\\n"
        f"1) Lies zuerst {handoff_path}.\\n"
        "2) Setze die offenen TODOs von oben nach unten um.\\n"
        "3) Bleibe im Local-first strict Modus.\\n"
        "4) Halte Review-vor-Publish bei.\\n"
        f"5) Letzter shorts_revenue run: {shorts_summary.get('run_id', 'n/a')} | "
        f"letzter youtube_shorts run: {yt_summary.get('run_id', 'n/a')}"
    )


def write_handoff(note: str = "") -> Path:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    if not CHRONIK_PATH.exists():
        CHRONIK_PATH.parent.mkdir(parents=True, exist_ok=True)
        CHRONIK_PATH.write_text("# Projekt Chronik\n\n", encoding="utf-8")

    now = _now()
    shorts_summary = _read_json(ROOT / "content_factory" / "deliverables" / "shorts_revenue" / "latest.json")
    yt_summary = _read_json(ROOT / "content_factory" / "deliverables" / "youtube_shorts" / "latest.json")

    git_status = _cmd(["git", "status", "--short", "--branch"])
    git_head = _cmd(["git", "log", "--oneline", "-n", "5"])

    latest_daemon_log = _latest_by_glob("automation/runs/daemon/*.log")
    latest_autopilot_log = _latest_by_glob("automation/runs/shorts_revenue_autopilot/*.log")
    latest_ingest_log = _latest_by_glob("automation/runs/ingest_*/router_log.json")

    todo: list[str] = []
    if git_status and any(line and not line.startswith("##") for line in git_status.splitlines()):
        todo.append("Uncommitted changes reviewen, dann gezielt committen.")
    if not shorts_summary:
        todo.append("shorts_revenue Run starten und latest.json erzeugen.")
    if not yt_summary:
        todo.append("youtube_shorts Run starten und latest.json erzeugen.")
    if not todo:
        todo.append("Nächsten Optimierungszyklus fahren (Trends -> Drafts -> KPI -> Strategy-Update).")

    handoff_name = f"handoff_{_timestamp_local()}.md"
    handoff_path = HANDOFF_DIR / handoff_name

    lines = [
        f"# Thread Handoff ({now.isoformat().replace('+00:00', 'Z')})",
        "",
        "## Current State",
        f"- shorts_revenue latest: {shorts_summary.get('run_id', 'n/a')}",
        f"- youtube_shorts latest: {yt_summary.get('run_id', 'n/a')}",
        f"- latest daemon log: {latest_daemon_log or 'n/a'}",
        f"- latest autopilot log: {latest_autopilot_log or 'n/a'}",
        f"- latest ingest log: {latest_ingest_log or 'n/a'}",
        "",
        "## Open TODO",
    ]
    for item in todo:
        lines.append(f"- {item}")

    if note.strip():
        lines.extend(["", "## Operator Note", f"- {note.strip()}"])

    lines.extend(
        [
            "",
            "## Git Status",
            "```",
            git_status or "n/a",
            "```",
            "",
            "## Recent Commits",
            "```",
            git_head or "n/a",
            "```",
        ]
    )

    write_preview = _build_resume_prompt(handoff_path, shorts_summary, yt_summary)
    lines.extend(["", "## Next Thread Prompt", "```", write_preview, "```", ""])
    handoff_path.write_text("\n".join(lines), encoding="utf-8")

    chronik_append = [
        f"## {now.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"- Handoff: {handoff_path}",
        f"- shorts_revenue latest: {shorts_summary.get('run_id', 'n/a')}",
        f"- youtube_shorts latest: {yt_summary.get('run_id', 'n/a')}",
        f"- TODO count: {len(todo)}",
        "",
    ]
    with CHRONIK_PATH.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(chronik_append))

    return handoff_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Write compact thread handoff + update project chronik")
    parser.add_argument("--note", default="", help="Optional operator note to include")
    args = parser.parse_args()
    out = write_handoff(note=args.note)
    print(f"OK: Handoff -> {out}")
    print(f"OK: Chronik -> {CHRONIK_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
