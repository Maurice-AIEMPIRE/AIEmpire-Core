#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.workflows.chatgpt_export_ingest import ingest_chatgpt_export
from automation.workflows.nugget_merge import merge_nuggets_registry
from automation.workflows.shorts_strategy_state import refresh_strategy_from_latest
from automation.workflows.x_feed_text_ingest import ingest_x_feed_text


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main() -> int:
    parser = argparse.ArgumentParser(description="Run lightweight degrade-mode maintenance (ingest + merge + strategy refresh)")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--conversation-limit", type=int, default=None)
    parser.add_argument("--since-date", default=None)
    parser.add_argument("--x-feed-dir", default=None)
    parser.add_argument("--skip-chat-export", action="store_true")
    parser.add_argument("--skip-x-feed", action="store_true")
    args = parser.parse_args()

    summary: Dict[str, Any] = {"status": "ok", "steps": []}
    run_id = args.run_id
    conversation_limit = (
        args.conversation_limit
        if args.conversation_limit is not None
        else _to_int(os.environ.get("CHATGPT_CONVERSATION_LIMIT", "0"), 0)
    )
    since_date = args.since_date or str(os.environ.get("CHATGPT_SINCE_DATE", "")).strip() or None

    if not args.skip_chat_export:
        try:
            notes, normalized = ingest_chatgpt_export(
                run_id=run_id,
                export_zip=None,
                export_dir=None,
                conversation_limit=max(0, conversation_limit),
                since_date=since_date,
            )
            summary["steps"].append(
                {
                    "step": "chatgpt_export_ingest",
                    "notes": len(notes),
                    "normalized_path": str(normalized),
                }
            )
        except Exception as exc:
            summary["steps"].append({"step": "chatgpt_export_ingest", "error": str(exc)})

    if not args.skip_x_feed:
        try:
            source_dir = Path(args.x_feed_dir).expanduser().resolve() if args.x_feed_dir else None
            x_notes, x_path = ingest_x_feed_text(run_id=run_id, source_dir=source_dir, file_limit=0)
            summary["steps"].append(
                {
                    "step": "x_feed_text_ingest",
                    "notes": len(x_notes),
                    "normalized_path": str(x_path),
                }
            )
        except Exception as exc:
            summary["steps"].append({"step": "x_feed_text_ingest", "error": str(exc)})

    registry_path, backlog_path, count = merge_nuggets_registry()
    summary["steps"].append(
        {
            "step": "nugget_merge",
            "registry": str(registry_path),
            "backlog": str(backlog_path),
            "count": count,
        }
    )

    strategy_refresh = refresh_strategy_from_latest()
    summary["steps"].append({"step": "strategy_refresh", **strategy_refresh})

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
