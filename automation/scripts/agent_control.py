#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "00_SYSTEM" / "agent_control"
STATE_PATH = STATE_DIR / "queue.json"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_state() -> Dict[str, Any]:
    return {
        "updated_at": _now(),
        "tasks": [],
        "agents": {},
    }


def _load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return _default_state()
    try:
        payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _default_state()
    if not isinstance(payload, dict):
        return _default_state()
    payload.setdefault("tasks", [])
    payload.setdefault("agents", {})
    payload["updated_at"] = _now()
    return payload


def _save_state(state: Dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = _now()
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_add(args: argparse.Namespace) -> int:
    state = _load_state()
    task = {
        "id": f"tsk_{uuid.uuid4().hex[:10]}",
        "title": args.title.strip(),
        "details": args.details.strip(),
        "cmd": args.cmd.strip(),
        "priority": int(args.priority),
        "status": "open",
        "created_at": _now(),
        "claimed_by": "",
        "claimed_at": "",
        "done_at": "",
        "note": "",
    }
    state["tasks"].append(task)
    _save_state(state)
    print(task["id"])
    return 0


def _sorted_open(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    open_tasks = [t for t in tasks if str(t.get("status")) == "open"]
    return sorted(open_tasks, key=lambda t: (-int(t.get("priority", 3)), str(t.get("created_at", ""))))


def cmd_claim(args: argparse.Namespace) -> int:
    state = _load_state()
    tasks = _sorted_open(state.get("tasks", []))
    if not tasks:
        print("none")
        return 0
    task = tasks[0]
    task["status"] = "in_progress"
    task["claimed_by"] = args.agent
    task["claimed_at"] = _now()
    state["agents"][args.agent] = {"last_seen": _now(), "status": f"working:{task['id']}"}
    _save_state(state)
    print(json.dumps(task, ensure_ascii=False))
    return 0


def cmd_done(args: argparse.Namespace) -> int:
    state = _load_state()
    found = False
    for task in state.get("tasks", []):
        if str(task.get("id")) != args.id:
            continue
        task["status"] = "done"
        task["done_at"] = _now()
        task["note"] = args.note.strip()
        found = True
        break
    if not found:
        raise SystemExit(f"task not found: {args.id}")
    state["agents"][args.agent] = {"last_seen": _now(), "status": f"done:{args.id}"}
    _save_state(state)
    print("ok")
    return 0


def cmd_fail(args: argparse.Namespace) -> int:
    state = _load_state()
    found = False
    for task in state.get("tasks", []):
        if str(task.get("id")) != args.id:
            continue
        task["status"] = "failed"
        task["done_at"] = _now()
        task["note"] = args.note.strip()
        found = True
        break
    if not found:
        raise SystemExit(f"task not found: {args.id}")
    state["agents"][args.agent] = {"last_seen": _now(), "status": f"failed:{args.id}"}
    _save_state(state)
    print("ok")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    state = _load_state()
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


def cmd_heartbeat(args: argparse.Namespace) -> int:
    state = _load_state()
    state["agents"][args.agent] = {"last_seen": _now(), "status": args.status.strip()}
    _save_state(state)
    print("ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Lightweight multi-agent queue for parallel terminal models")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--details", default="")
    p_add.add_argument("--cmd", default="")
    p_add.add_argument("--priority", type=int, default=3)
    p_add.set_defaults(func=cmd_add)

    p_claim = sub.add_parser("claim")
    p_claim.add_argument("--agent", required=True)
    p_claim.set_defaults(func=cmd_claim)

    p_done = sub.add_parser("done")
    p_done.add_argument("--agent", required=True)
    p_done.add_argument("--id", required=True)
    p_done.add_argument("--note", default="")
    p_done.set_defaults(func=cmd_done)

    p_fail = sub.add_parser("fail")
    p_fail.add_argument("--agent", required=True)
    p_fail.add_argument("--id", required=True)
    p_fail.add_argument("--note", default="")
    p_fail.set_defaults(func=cmd_fail)

    p_list = sub.add_parser("list")
    p_list.set_defaults(func=cmd_list)

    p_hb = sub.add_parser("heartbeat")
    p_hb.add_argument("--agent", required=True)
    p_hb.add_argument("--status", default="idle")
    p_hb.set_defaults(func=cmd_heartbeat)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
