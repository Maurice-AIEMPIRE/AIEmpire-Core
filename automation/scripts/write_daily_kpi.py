#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KPI_DIR = ROOT / "00_SYSTEM/revenue_system/kpi"
STRIPE_PATH = ROOT / "content_factory/deliverables/revenue/stripe/latest.json"
SHORTS_PATH = ROOT / "content_factory/deliverables/shorts_revenue/latest.json"
PREFLIGHT_PATH = ROOT / "automation/runs/preflight/latest.json"


def read_json(path: Path) -> dict:
    if not path.exists() or not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def parse_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_kpi(day: dt.date) -> dict:
    stripe = read_json(STRIPE_PATH)
    shorts = read_json(SHORTS_PATH)
    preflight = read_json(PREFLIGHT_PATH)

    runtime_incidents = 0
    if preflight and preflight.get("decision") != "run":
        runtime_incidents += 1

    return {
        "date": day.isoformat(),
        "leads": 0,
        "replies": 0,
        "calls": 0,
        "offers": 0,
        "closes": 0,
        "cash_eur": parse_float(stripe.get("real_revenue_eur", stripe.get("net_revenue_eur", 0.0))),
        "published_shorts": parse_int(shorts.get("published_count", 0)),
        "runtime_incidents": runtime_incidents,
        "sources": {
            "stripe": str(STRIPE_PATH),
            "shorts": str(SHORTS_PATH),
            "preflight": str(PREFLIGHT_PATH),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write daily KPI JSON for revenue operating system")
    parser.add_argument("--date", default="")
    parser.add_argument("--output-dir", default=str(KPI_DIR))
    args = parser.parse_args()

    day = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    kpi = build_kpi(day)
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"daily_kpi_{day.isoformat()}.json"
    out_path.write_text(json.dumps(kpi, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
