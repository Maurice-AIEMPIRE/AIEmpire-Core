from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from automation.n8n_events import post_n8n_event
from automation.utils.files import write_text


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "ai-vault" / "reports"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _latest_publish_summary(workflow: str) -> Dict[str, Any]:
    base = ROOT / "content_factory" / "deliverables" / workflow
    if not base.exists():
        return {}
    summaries = sorted(base.glob("*/publish_run_summary.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not summaries:
        return {}
    return _read_json(summaries[0])


def _load_stripe_latest() -> Dict[str, Any]:
    latest = ROOT / "content_factory" / "deliverables" / "revenue" / "stripe" / "latest.json"
    payload = _read_json(latest)
    if not payload:
        return {}
    run_path = Path(str(payload.get("path") or ""))
    snapshot = _read_json(run_path) if run_path.exists() else {}
    if snapshot:
        return snapshot
    return payload


def _load_shorts_projection() -> Dict[str, Any]:
    latest = _read_json(ROOT / "content_factory" / "deliverables" / "shorts_revenue" / "latest.json")
    run_id = str(latest.get("run_id") or "").strip()
    if not run_id:
        return {}
    run_dir = ROOT / "content_factory" / "deliverables" / "shorts_revenue" / run_id
    money = _read_json(run_dir / "money_model.json")
    yt = _read_json(run_dir / "youtube_metrics.json")
    return {
        "run_id": run_id,
        "projection": (money.get("projection") if isinstance(money, dict) else {}) or {},
        "yt_summary": (yt.get("summary") if isinstance(yt, dict) else {}) or {},
    }


def render_income_stream_message() -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    stripe = _load_stripe_latest()
    shorts = _load_shorts_projection()
    pub_sr = _latest_publish_summary("shorts_revenue")
    pub_ys = _latest_publish_summary("youtube_shorts")

    stripe_totals = (stripe.get("totals") if isinstance(stripe, dict) else {}) or {}
    real_net = float(stripe_totals.get("net_eur") or 0.0)
    real_gross = float(stripe_totals.get("gross_eur") or 0.0)
    paid_count = int(stripe_totals.get("charges_paid") or 0)

    projection = shorts.get("projection") or {}
    proj_rev = float(projection.get("projected_revenue_eur") or 0.0)
    proj_views = float(projection.get("projected_views_24h") or 0.0)
    yt_summary = shorts.get("yt_summary") or {}
    avg_vph = float(yt_summary.get("avg_views_per_hour") or 0.0)
    avg_like = float(yt_summary.get("avg_like_rate") or 0.0)
    avg_comment = float(yt_summary.get("avg_comment_rate") or 0.0)

    sr_published = int(pub_sr.get("published_count") or 0)
    ys_published = int(pub_ys.get("published_count") or 0)
    sr_mode = str(pub_sr.get("effective_mode") or pub_sr.get("mode") or "n/a")
    ys_mode = str(pub_ys.get("effective_mode") or pub_ys.get("mode") or "n/a")

    lines = [
        f"Income Stream Update | {now}",
        "",
        "REAL CASH (Stripe):",
        f"- Net revenue (lookback): EUR {real_net:.2f}",
        f"- Gross revenue (lookback): EUR {real_gross:.2f}",
        f"- Successful payments: {paid_count}",
        "",
        "Shorts + Distribution:",
        f"- shorts_revenue published this run: {sr_published} (mode={sr_mode})",
        f"- youtube_shorts published this run: {ys_published} (mode={ys_mode})",
        "",
        "Live KPI + Projection:",
        f"- projected revenue 24h: EUR {proj_rev:.2f}",
        f"- projected views 24h: {proj_views:.0f}",
        f"- avg views/hour: {avg_vph:.2f}",
        f"- avg like rate: {avg_like:.4f}",
        f"- avg comment rate: {avg_comment:.4f}",
    ]
    return "\n".join(lines).strip() + "\n"


def send_telegram(message: str) -> None:
    token = str(os.environ.get("TELEGRAM_BOT_TOKEN", "")).strip()
    chat_id = str(os.environ.get("TELEGRAM_CHAT_ID", "")).strip()
    if not token or not chat_id:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Send income stream update (Stripe real cash + shorts KPIs) to Telegram")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    message = render_income_stream_message()
    report_path = Path(args.output) if args.output else (REPORT_DIR / f"income_stream_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(report_path, message)

    if args.send:
        send_telegram(message)
    post_n8n_event(
        event_type="income_stream_report",
        source="automation.income_stream",
        payload={
            "report_path": str(report_path),
            "telegram_sent": bool(args.send),
            "message_preview": message[:800],
        },
    )
    print(str(report_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
