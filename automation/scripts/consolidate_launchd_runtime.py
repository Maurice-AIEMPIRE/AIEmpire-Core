#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UID = os.getuid()

FUNCTION_GROUPS = {
    "orchestrator": {"canonical": "com.ai-empire.autonomy", "fallback": "com.ai-empire.master-chat-controller"},
    "watchdog": {"canonical": "com.ai-empire.watchdog", "fallback": None},
    "openclaw_gateway": {"canonical": "ai.openclaw.gateway", "fallback": "com.aiempire.guardian"},
    "telegram_router": {"canonical": "com.ai-empire.telegram-router", "fallback": "com.empire.telegrambot"},
    "youtube_autopilot": {"canonical": "ai-empire.youtube-automation.godmode", "fallback": "com.empire.youtube.producer"},
    "n8n": {"canonical": "com.ai-empire.n8n", "fallback": None},
    "snapshot": {"canonical": "com.ai-empire.snapshot", "fallback": "com.ai-empire.openclaw-snapshot"},
    "infra_audit": {"canonical": "com.ai-empire.infra-audit-daily", "fallback": None},
}


def run(cmd: list[str], timeout: int = 8) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def all_labels() -> list[str]:
    code, out, _ = run(["launchctl", "list"])
    if code != 0:
        return []
    labels = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            labels.append(parts[-1])
    return sorted(set(labels))


def labels_for_group(group: str, labels: list[str]) -> list[str]:
    token_map = {
        "orchestrator": ["autonomy", "master-chat-controller"],
        "watchdog": ["watchdog"],
        "openclaw_gateway": ["openclaw", "aiempire.guardian"],
        "telegram_router": ["telegram"],
        "youtube_autopilot": ["youtube", "shorts"],
        "n8n": ["n8n"],
        "snapshot": ["snapshot"],
        "infra_audit": ["infra-audit"],
    }
    tokens = token_map.get(group, [])
    out = []
    for label in labels:
        lowered = label.lower()
        if any(tok in lowered for tok in tokens):
            out.append(label)
    return out


def disable_label(label: str, dry_run: bool) -> str:
    if dry_run:
        return "dry_run_skip"
    run(["launchctl", "disable", f"gui/{UID}/{label}"])
    run(["launchctl", "bootout", f"gui/{UID}/{label}"])
    return "disabled"


def main() -> int:
    parser = argparse.ArgumentParser(description="Disable shadow/stale launchd jobs, keep canonical per function group")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--output",
        default=str(ROOT / "00_SYSTEM/infra/LAUNCHD_CONSOLIDATION_REPORT_2026-02-18.md"),
    )
    args = parser.parse_args()

    labels = all_labels()
    rows = []
    for group, cfg in FUNCTION_GROUPS.items():
        group_labels = labels_for_group(group, labels)
        canonical = cfg["canonical"]
        fallback = cfg["fallback"]
        for label in group_labels:
            if label == canonical:
                rows.append((group, label, "canonical", "keep"))
                continue
            if fallback and label == fallback:
                rows.append((group, label, "fallback", "keep_as_fallback"))
                continue
            action = disable_label(label, args.dry_run)
            rows.append((group, label, "shadow", action))

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().astimezone().replace(microsecond=0).isoformat()
    lines = [
        "# LAUNCHD Consolidation Report",
        "",
        f"- Generated: {now}",
        f"- Mode: {'dry-run' if args.dry_run else 'apply'}",
        "",
        "| Function Group | Label | Role | Action |",
        "|---|---|---|---|",
    ]
    for group, label, role, action in rows:
        lines.append(f"| {group} | `{label}` | {role} | {action} |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
