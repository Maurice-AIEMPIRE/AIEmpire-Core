from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

from automation.core.config import load_router_config, load_system_config
from automation.core.router import Router
from automation.core.runner import Runner
from automation.utils.files import timestamp_id
from automation.workflows.notes_ingest import export_notes_applescript, ingest_notes, load_notes_from_folder



def append_ingested_log(folder: Path, notes) -> None:
    log_path = folder / "INGESTED.md"
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"\n## {ts}"]
    for note in notes:
        lines.append(f"- {note.note_id}")
    log_path.write_text(log_path.read_text(encoding="utf-8") + "\n" + "\n".join(lines) + "\n", encoding="utf-8") if log_path.exists() else log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest notes and extract gold nuggets")
    parser.add_argument("--source", choices=["notes", "folder"], default="folder")
    parser.add_argument("--path", default=None, help="Folder path for source=folder")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of notes")
    parser.add_argument("--since-days", type=int, default=0, help="Only notes modified in the last N days (notes source)")
    parser.add_argument("--execute", action="store_true", help="Execute LLM calls (otherwise dry-run)")
    parser.add_argument("--nuggets", type=int, default=8, help="Max nuggets per note")
    parser.add_argument("--max-chars", type=int, default=12000, help="Max chars per note body")
    parser.add_argument("--router-config", default=None)
    parser.add_argument("--run-id", default=None)

    args = parser.parse_args()

    system_cfg = load_system_config()
    router_cfg_path = Path(args.router_config) if args.router_config else None
    router_cfg = load_router_config(router_cfg_path)
    router = Router(router_cfg)

    run_id = args.run_id or timestamp_id()
    log_path = Path("automation") / "runs" / f"ingest_{run_id}" / "router_log.json"
    runner = Runner(router, execute=args.execute, run_id=run_id, log_path=log_path)

    if args.source == "notes":
        notes = export_notes_applescript(limit=args.limit, since_days=args.since_days)
        folder = None
    else:
        folder = Path(args.path) if args.path else Path(system_cfg.get("intake_dir", ROOT / "claude_intake"))
        notes = load_notes_from_folder(folder, limit=args.limit)

    if not notes:
        print("No notes found.")
        return 0

    json_path, md_path = ingest_notes(
        notes=notes,
        runner=runner,
        nugget_count=args.nuggets,
        max_chars=args.max_chars,
        run_id=run_id,
    )

    if folder is not None:
        append_ingested_log(folder, notes)

    runner.write_log()

    print(f"OK: Nuggets JSON -> {json_path}")
    print(f"OK: Nuggets MD   -> {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
