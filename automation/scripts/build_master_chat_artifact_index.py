#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
CHAT_ARTIFACTS_DIR = ROOT_DIR / "00_SYSTEM" / "chat_artifacts"

DATE_RE = re.compile(r"(20\d{2})[-_](\d{2})[-_](\d{2})")

CATEGORY_RULES = [
    ("revenue_assets", ("gumroad_products", "pricing", "offer", "proposal", "vault", "product")),
    ("revenue_operational_logs", ("shorts_revenue_autopilot", "income_stream", "run_summary", "session_", "ops_maintenance")),
    ("revenue_sales", ("revenue", "stripe", "gumroad", "sales", "income", "client")),
    ("handoff_summary", ("handoff", "summary", "session", "chronik", "report")),
    ("prompts_systems", ("prompt", "vault", "system", "orchestrator")),
    ("automation_runtime", ("automation", "workflow", "run_", "runs/", "state")),
    ("threads_conversations", ("thread", "threads", "conversation", "chat", "transcript")),
]

PLATFORM_RULES = [
    ("chatgpt_atlas", ("chatgpt", "atlas")),
    ("codex", ("codex",)),
    ("claude", ("claude",)),
    ("openclaw_ollama", ("openclaw", "ollama")),
    ("youtube_tiktok_x", ("youtube", "tiktok", "x_", "twitter")),
    ("notion", ("notion",)),
]

REVENUE_KEYWORDS = (
    "revenue",
    "stripe",
    "gumroad",
    "offer",
    "outreach",
    "sales",
    "client",
    "income",
    "deal",
    "product",
    "pipeline",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build MASTER_CHAT_ARTIFACTS_INDEX.md from pull manifest")
    parser.add_argument(
        "--pull-dir",
        default="",
        help="Absolute pull directory (defaults to latest PULL_* in 00_SYSTEM/chat_artifacts)",
    )
    parser.add_argument(
        "--output",
        default=str(CHAT_ARTIFACTS_DIR / "MASTER_CHAT_ARTIFACTS_INDEX.md"),
        help="Absolute output markdown path",
    )
    parser.add_argument("--priority-limit", type=int, default=40, help="How many priority items to include")
    return parser.parse_args()


def pick_latest_pull() -> Path:
    pulls = [p for p in CHAT_ARTIFACTS_DIR.glob("PULL_*") if p.is_dir()]
    if not pulls:
        raise FileNotFoundError(f"No PULL_* directory found in {CHAT_ARTIFACTS_DIR}")
    pulls.sort(key=lambda p: p.stat().st_mtime)
    return pulls[-1]


def classify_category(path_text: str) -> str:
    lowered = path_text.lower()
    for name, words in CATEGORY_RULES:
        if any(word in lowered for word in words):
            return name
    return "other"


def detect_platform(path_text: str) -> str:
    lowered = path_text.lower()
    for name, words in PLATFORM_RULES:
        if any(word in lowered for word in words):
            return name
    return "mixed_other"


def extract_date(path_text: str) -> str:
    match = DATE_RE.search(path_text)
    if not match:
        return "n/a"
    year, month, day = match.groups()
    return f"{year}-{month}-{day}"


def is_revenue_relevant(path_text: str) -> bool:
    lowered = path_text.lower()
    return any(word in lowered for word in REVENUE_KEYWORDS)


def safe_name(path_text: str) -> str:
    return Path(path_text).name or path_text


def score_entry(entry: dict[str, str]) -> int:
    score = 0
    if entry["revenue_relevant"] == "yes":
        score += 3
    if entry["category"] == "revenue_assets":
        score += 6
    if entry["category"] == "revenue_sales":
        score += 4
    if entry["category"] == "revenue_operational_logs":
        score += 1
    if entry["category"] == "handoff_summary":
        score += 2
    if entry["category"] == "threads_conversations":
        score += 2
    if entry["platform"] in {"chatgpt_atlas", "codex", "claude"}:
        score += 1
    if entry["date_guess"] != "n/a":
        score += 1
    name = entry.get("artifact_name", "").lower()
    if name.endswith(".log"):
        score -= 4
    if "run_summary" in name:
        score -= 2
    return score


def read_manifest_rows(manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with manifest_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for raw in reader:
            if len(raw) < 4:
                continue
            entry_type, source_bucket, source_path, mirror_path = raw[:4]
            if entry_type.strip().upper() != "LINK":
                continue
            combined_text = source_path
            rows.append(
                {
                    "source_bucket": source_bucket,
                    "source_path": source_path,
                    "mirror_path": mirror_path,
                    "artifact_name": safe_name(source_path),
                    "category": classify_category(combined_text),
                    "platform": detect_platform(combined_text),
                    "date_guess": extract_date(combined_text),
                    "revenue_relevant": "yes" if is_revenue_relevant(combined_text) else "no",
                    "priority_score": "0",
                }
            )
    return rows


def to_markdown(
    *,
    rows: list[dict[str, str]],
    output_path: Path,
    pull_dir: Path,
    manifest_path: Path,
    priority_limit: int,
) -> str:
    now = dt.datetime.now().astimezone().replace(microsecond=0).isoformat()
    source_counts = Counter(r["source_bucket"] for r in rows)
    category_counts = Counter(r["category"] for r in rows)
    platform_counts = Counter(r["platform"] for r in rows)
    revenue_count = sum(1 for r in rows if r["revenue_relevant"] == "yes")

    by_date = Counter(r["date_guess"] for r in rows if r["date_guess"] != "n/a")
    top_dates = by_date.most_common(8)

    for row in rows:
        row["priority_score"] = str(score_entry(row))

    sorted_priority = sorted(
        rows,
        key=lambda r: (
            int(r["priority_score"]),
            r["date_guess"],
            r["artifact_name"].lower(),
        ),
        reverse=True,
    )
    priority_rows = sorted_priority[: max(0, priority_limit)]

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["source_bucket"]].append(row)

    lines: list[str] = []
    lines.append("# MASTER_CHAT_ARTIFACTS_INDEX")
    lines.append("")
    lines.append(f"- Generated at: {now}")
    lines.append(f"- Pull source: `{pull_dir}`")
    lines.append(f"- Manifest: `{manifest_path}`")
    lines.append(f"- Output: `{output_path}`")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Total artifacts: **{len(rows)}**")
    lines.append(f"- Revenue-relevant artifacts: **{revenue_count}**")
    lines.append("")
    lines.append("### Source Buckets")
    lines.append("")
    for name, count in source_counts.most_common():
        lines.append(f"- `{name}`: {count}")
    lines.append("")
    lines.append("### Categories")
    lines.append("")
    for name, count in category_counts.most_common():
        lines.append(f"- `{name}`: {count}")
    lines.append("")
    lines.append("### Platforms")
    lines.append("")
    for name, count in platform_counts.most_common():
        lines.append(f"- `{name}`: {count}")
    lines.append("")
    lines.append("### Top Date Clusters")
    lines.append("")
    if top_dates:
        for date_key, count in top_dates:
            lines.append(f"- `{date_key}`: {count}")
    else:
        lines.append("- n/a")
    lines.append("")
    lines.append("## Priority Queue (Revenue + Control)")
    lines.append("")
    lines.append("| Score | Source | Category | Date | Artifact | Path |")
    lines.append("|---:|---|---|---|---|---|")
    for row in priority_rows:
        lines.append(
            "| "
            f"{row['priority_score']} | "
            f"{row['source_bucket']} | "
            f"{row['category']} | "
            f"{row['date_guess']} | "
            f"{row['artifact_name']} | "
            f"`{row['mirror_path']}` |"
        )
    lines.append("")
    lines.append("## Full Registry")
    lines.append("")
    for bucket in sorted(grouped.keys()):
        lines.append(f"### {bucket}")
        lines.append("")
        lines.append("| Category | Platform | Date | Revenue | Artifact | Path |")
        lines.append("|---|---|---|---|---|---|")
        for row in sorted(grouped[bucket], key=lambda r: (r["category"], r["artifact_name"].lower())):
            lines.append(
                "| "
                f"{row['category']} | "
                f"{row['platform']} | "
                f"{row['date_guess']} | "
                f"{row['revenue_relevant']} | "
                f"{row['artifact_name']} | "
                f"`{row['mirror_path']}` |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    pull_dir = Path(args.pull_dir).expanduser().resolve() if args.pull_dir else pick_latest_pull()
    manifest_path = pull_dir / "MANIFEST.tsv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    rows = read_manifest_rows(manifest_path)
    if not rows:
        raise RuntimeError(f"No LINK rows found in {manifest_path}")

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = to_markdown(
        rows=rows,
        output_path=output_path,
        pull_dir=pull_dir,
        manifest_path=manifest_path,
        priority_limit=args.priority_limit,
    )
    output_path.write_text(content, encoding="utf-8")
    print(f"[master-chat-index] rows={len(rows)} output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
