from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from automation.utils.files import ensure_dir, write_text

ROOT = Path(__file__).resolve().parents[1]
NUGGET_DIR = ROOT / "ai-vault" / "nuggets"
RUNS_DIR = ROOT / "automation" / "runs"
REPORT_DIR = ROOT / "ai-vault" / "reports"


def _latest_file(path: Path, pattern: str) -> Optional[Path]:
    files = list(path.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def _read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_latest_nuggets() -> Tuple[Optional[Path], Dict]:
    latest = _latest_file(NUGGET_DIR, "nuggets_*.json")
    if not latest:
        return None, {}
    return latest, _read_json(latest)


def collect_usage() -> Dict[str, int]:
    usage_totals: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for log in RUNS_DIR.glob("run_*.json"):
        try:
            data = _read_json(log)
        except Exception:
            continue
        for event in data.get("events", []):
            usage = event.get("usage") or {}
            if not isinstance(usage, dict):
                continue
            prompt = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
            completion = usage.get("completion_tokens") or usage.get("output_tokens") or 0
            total = usage.get("total_tokens") or 0
            if total == 0:
                total = prompt + completion
            usage_totals["prompt_tokens"] += int(prompt)
            usage_totals["completion_tokens"] += int(completion)
            usage_totals["total_tokens"] += int(total)
    return usage_totals


def collect_latest_runs(limit: int = 5) -> List[str]:
    logs = list(RUNS_DIR.glob("run_*.json"))
    logs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [log.name for log in logs[:limit]]


def render_report() -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [f"AI Empire Status Report — {now}", ""]

    nuggets_path, nuggets_data = collect_latest_nuggets()
    if nuggets_path:
        results = nuggets_data.get("results", []) if isinstance(nuggets_data, dict) else []
        note_count = len(results)
        nugget_count = 0
        nugget_items: List[Dict] = []
        for item in results:
            items = item.get("nuggets", []) if isinstance(item, dict) else []
            nugget_count += len(items) if isinstance(items, list) else 0
            for nug in items:
                if isinstance(nug, dict):
                    nugget_items.append(nug)
        nugget_items.sort(key=lambda n: int(n.get("score", 0)), reverse=True)

        lines.append("Notes Ingest:")
        lines.append(f"- latest: {nuggets_path.name}")
        lines.append(f"- notes: {note_count}")
        lines.append(f"- nuggets: {nugget_count}")
        lines.append("")

        if nugget_items:
            lines.append("Top Nuggets:")
            for idx, nug in enumerate(nugget_items[:5]):
                insight = str(nug.get("insight", ""))
                action = str(nug.get("action", ""))
                if action:
                    lines.append(f"{idx + 1}) {insight} — Action: {action}")
                else:
                    lines.append(f"{idx + 1}) {insight}")
            lines.append("")
    else:
        lines.append("Notes Ingest: no nuggets yet.")
        lines.append("")

    usage = collect_usage()
    lines.append("Usage (from router logs):")
    lines.append(f"- prompt_tokens: {usage['prompt_tokens']}")
    lines.append(f"- completion_tokens: {usage['completion_tokens']}")
    lines.append(f"- total_tokens: {usage['total_tokens']}")
    lines.append("")

    recent_runs = collect_latest_runs()
    if recent_runs:
        lines.append("Recent runs:")
        for name in recent_runs:
            lines.append(f"- {name}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def send_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in env")

    # keep it under Telegram 4096 char limit
    if len(message) > 3500:
        message = message[:3490] + "\n..."

    payload = {
        "chat_id": chat_id,
        "text": message,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate status report and optionally send to Telegram")
    parser.add_argument("--send", action="store_true", help="Send report via Telegram")
    parser.add_argument("--output", default=None, help="Write report to file")

    args = parser.parse_args()
    report = render_report()
    if args.output:
        out_path = Path(args.output)
    else:
        ensure_dir(REPORT_DIR)
        out_path = REPORT_DIR / f"status_{dt.datetime.now().strftime('%Y%m%d_%H%M')}.md"
    write_text(out_path, report)

    if args.send:
        send_telegram(report)

    print(f"OK: Report -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
