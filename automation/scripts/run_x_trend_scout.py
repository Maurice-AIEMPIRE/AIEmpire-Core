#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.workflows.nugget_merge import merge_nuggets_registry
from automation.workflows.x_trend_scout import run_x_scout
from automation.workflows.x_feed_text_ingest import ingest_x_feed_text
from automation.n8n_events import post_n8n_event


def _parse_queries(raw: str) -> List[str]:
    return [p.strip() for p in str(raw or "").split(",") if p.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run X trend scout and merge extracted nuggets into registry")
    parser.add_argument("--export-path", default=None, help="Path to tweets.js/json export")
    parser.add_argument("--queries", default=None, help="Comma-separated search queries")
    parser.add_argument("--bearer-token", default=None, help="X API bearer token (fallback to env X_BEARER_TOKEN)")
    parser.add_argument("--x-feed-dir", default=None, help="Optional x_feed_text folder (txt/md dumps)")
    parser.add_argument("--skip-x-feed", action="store_true")
    args = parser.parse_args()

    export_path = Path(args.export_path) if args.export_path else None
    bearer = str(args.bearer_token or os.environ.get("X_BEARER_TOKEN", "")).strip()
    queries = _parse_queries(args.queries or os.environ.get("X_SCOUT_QUERIES", ""))

    result = run_x_scout(
        export_path=export_path,
        bearer_token=bearer,
        search_queries=queries or None,
    )

    x_feed_enabled = not args.skip_x_feed and str(os.environ.get("X_FEED_TEXT_ENABLED", "1")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    x_feed_ok = False
    if x_feed_enabled:
        try:
            source_dir = Path(args.x_feed_dir).expanduser().resolve() if args.x_feed_dir else None
            notes, normalized = ingest_x_feed_text(source_dir=source_dir)
            x_feed_ok = len(notes) > 0
            print(
                json.dumps(
                    {
                        "x_feed_text_ingest": "ok",
                        "notes": len(notes),
                        "normalized_path": str(normalized),
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        except Exception as exc:
            print(json.dumps({"x_feed_text_ingest": "error", "error": str(exc)}, indent=2, ensure_ascii=False))

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if str(result.get("status") or "") == "success" or x_feed_ok:
        registry_path, backlog_path, count = merge_nuggets_registry()
        post_n8n_event(
            event_type="x_trend_scout_run",
            source="automation.scripts.run_x_trend_scout",
            payload={
                "result": result,
                "x_feed_ingested": x_feed_ok,
                "registry": str(registry_path),
                "backlog": str(backlog_path),
                "registry_count": count,
            },
        )
        print(
            json.dumps(
                {
                    "registry": str(registry_path),
                    "backlog": str(backlog_path),
                    "registry_count": count,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
