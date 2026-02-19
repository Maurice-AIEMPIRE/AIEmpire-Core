#!/usr/bin/env python3
"""
Content Scheduler - AIEmpire Content Pipeline

Reads content_queue.json from publish_ready/ and formats content
for TikTok, Instagram, and X/Twitter. Saves platform-ready versions
to publish/formatted/.

Usage:
    python3 src/content_scheduler.py                # Process all queued content
    python3 src/content_scheduler.py --platform x   # Only format for X/Twitter
    python3 src/content_scheduler.py --dry-run      # Preview without writing files
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Project root (one level up from src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUEUE_FILE = PROJECT_ROOT / "publish_ready" / "content_queue.json"
OUTPUT_DIR = PROJECT_ROOT / "publish" / "formatted"

# Platform character limits and formatting rules
PLATFORM_CONFIG = {
    "tiktok": {
        "max_caption": 2200,
        "max_hashtags": 8,
        "format": "caption",
        "suffix": "_tiktok.txt",
    },
    "instagram": {
        "max_caption": 2200,
        "max_hashtags": 30,
        "format": "caption",
        "suffix": "_instagram.txt",
    },
    "x": {
        "max_chars": 280,
        "max_hashtags": 3,
        "format": "thread",
        "suffix": "_x.txt",
    },
}


def load_queue() -> list[dict]:
    """Load content queue from JSON file."""
    if not QUEUE_FILE.exists():
        print(f"[INFO] No queue file found at {QUEUE_FILE}")
        print("[INFO] Creating sample content_queue.json...")
        create_sample_queue()
        return load_queue()

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return []


def create_sample_queue():
    """Create a sample content_queue.json with example entries."""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)

    sample = {
        "version": "1.0",
        "created": datetime.now(timezone.utc).isoformat(),
        "items": [
            {
                "id": "post-001",
                "title": "Why AI Agents Will Replace 80% of Manual Tasks by 2027",
                "body": "Most businesses still do things manually that AI agents handle in seconds. Here's what I learned building 100+ agents: The secret isn't the AI model - it's the SYSTEM around it. Router + Verification + Knowledge Store = unstoppable automation. Start with ONE agent. Automate ONE task. Then scale.",
                "hashtags": ["AIAgents", "Automation", "AI", "Business", "Productivity", "Tech", "Future", "Entrepreneur"],
                "category": "thought_leadership",
                "platforms": ["tiktok", "instagram", "x"],
                "status": "queued",
                "priority": 1,
            },
            {
                "id": "post-002",
                "title": "Fire Alarm Systems + AI = The Future of Building Safety",
                "body": "16 years in BMA (Brandmeldeanlagen) taught me one thing: documentation kills productivity. So I built AI agents to handle it. Now inspection reports that took 3 hours take 30 minutes. The checklists? Automated. The compliance tracking? Automated. This is what happens when domain expertise meets AI.",
                "hashtags": ["BMA", "FireSafety", "AI", "Automation", "FacilityManagement", "Tech", "Innovation"],
                "category": "niche_expertise",
                "platforms": ["tiktok", "instagram", "x"],
                "status": "queued",
                "priority": 2,
            },
            {
                "id": "post-003",
                "title": "Build Your First AI Agent in 15 Minutes",
                "body": "You don't need a CS degree. You don't need expensive APIs. Here's how: 1) Install Ollama (free, local AI). 2) Pick a task you do daily. 3) Write a simple prompt. 4) Connect it to your workflow. 5) Let it run. That's it. Your first agent is live. Now repeat 99 more times.",
                "hashtags": ["AIAgents", "Tutorial", "Ollama", "LocalAI", "NoCode", "Automation", "StartupLife"],
                "category": "tutorial",
                "platforms": ["tiktok", "instagram", "x"],
                "status": "queued",
                "priority": 1,
            },
        ],
    }

    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2, ensure_ascii=False)
    print(f"[OK] Created sample queue at {QUEUE_FILE}")


def format_for_tiktok(item: dict) -> str:
    """Format content for TikTok caption."""
    title = item.get("title", "")
    body = item.get("body", "")
    hashtags = item.get("hashtags", [])

    caption = f"{title}\n\n{body}"

    # Add hashtags (max 8 for TikTok)
    tags = hashtags[:PLATFORM_CONFIG["tiktok"]["max_hashtags"]]
    tag_str = " ".join(f"#{t}" for t in tags)

    full = f"{caption}\n\n{tag_str}"

    # Truncate if over limit
    max_len = PLATFORM_CONFIG["tiktok"]["max_caption"]
    if len(full) > max_len:
        available = max_len - len(tag_str) - 4  # 4 for \n\n..
        full = f"{caption[:available]}...\n\n{tag_str}"

    return full


def format_for_instagram(item: dict) -> str:
    """Format content for Instagram caption."""
    title = item.get("title", "")
    body = item.get("body", "")
    hashtags = item.get("hashtags", [])

    # Instagram format: title as hook, body with line breaks, hashtags block
    paragraphs = body.split(". ")
    formatted_body = ".\n".join(paragraphs)

    caption = f"{title}\n\n{formatted_body}"

    # Instagram allows up to 30 hashtags
    tags = hashtags[:PLATFORM_CONFIG["instagram"]["max_hashtags"]]
    tag_str = " ".join(f"#{t}" for t in tags)

    full = f"{caption}\n\n.\n.\n.\n\n{tag_str}"

    max_len = PLATFORM_CONFIG["instagram"]["max_caption"]
    if len(full) > max_len:
        available = max_len - len(tag_str) - 10
        full = f"{caption[:available]}...\n\n.\n.\n.\n\n{tag_str}"

    return full


def format_for_x(item: dict) -> str:
    """Format content as X/Twitter thread."""
    title = item.get("title", "")
    body = item.get("body", "")
    hashtags = item.get("hashtags", [])

    max_chars = PLATFORM_CONFIG["x"]["max_chars"]
    max_tags = PLATFORM_CONFIG["x"]["max_hashtags"]

    # Build thread
    tweets = []

    # Tweet 1: Hook (title)
    tags = hashtags[:max_tags]
    tag_str = " ".join(f"#{t}" for t in tags)
    hook = f"{title}\n\n{tag_str}"
    if len(hook) > max_chars:
        hook = f"{title[:max_chars - len(tag_str) - 5]}...\n\n{tag_str}"
    tweets.append(hook)

    # Split body into tweet-sized chunks
    sentences = [s.strip() for s in body.split(". ") if s.strip()]
    current_tweet = ""

    for sentence in sentences:
        candidate = f"{current_tweet} {sentence}.".strip() if current_tweet else f"{sentence}."
        if len(candidate) <= max_chars:
            current_tweet = candidate
        else:
            if current_tweet:
                tweets.append(current_tweet)
            current_tweet = f"{sentence}."
            if len(current_tweet) > max_chars:
                current_tweet = current_tweet[: max_chars - 3] + "..."

    if current_tweet:
        tweets.append(current_tweet)

    # Format as numbered thread
    lines = [f"--- Tweet {i + 1}/{len(tweets)} ---\n{tweet}" for i, tweet in enumerate(tweets)]
    return "\n\n".join(lines)


FORMATTERS = {
    "tiktok": format_for_tiktok,
    "instagram": format_for_instagram,
    "x": format_for_x,
}


def process_queue(platform_filter: str | None = None, dry_run: bool = False) -> dict:
    """Process the content queue and generate platform-ready files."""
    queue = load_queue()

    if not queue:
        print("[INFO] Content queue is empty.")
        return {"processed": 0, "files": []}

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    stats = {"processed": 0, "files": [], "skipped": 0}

    for item in queue:
        if item.get("status") not in ("queued", None):
            stats["skipped"] += 1
            continue

        item_id = item.get("id", f"item-{stats['processed']}")
        platforms = item.get("platforms", list(PLATFORM_CONFIG.keys()))

        if platform_filter:
            platforms = [p for p in platforms if p == platform_filter]

        for platform in platforms:
            if platform not in FORMATTERS:
                print(f"[WARN] Unknown platform: {platform}, skipping")
                continue

            formatter = FORMATTERS[platform]
            formatted = formatter(item)

            suffix = PLATFORM_CONFIG[platform]["suffix"]
            filename = f"{item_id}{suffix}"
            filepath = OUTPUT_DIR / filename

            if dry_run:
                print(f"\n[DRY RUN] Would write: {filepath}")
                print(f"--- Preview ({platform}) ---")
                print(formatted[:500])
                if len(formatted) > 500:
                    print(f"... ({len(formatted)} chars total)")
                print("---")
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(formatted)
                print(f"[OK] {filepath}")

            stats["files"].append(str(filepath))

        stats["processed"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="AIEmpire Content Scheduler - Format content for social platforms"
    )
    parser.add_argument(
        "--platform",
        choices=["tiktok", "instagram", "x"],
        help="Only format for a specific platform",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview formatted content without writing files",
    )

    args = parser.parse_args()

    print("=" * 50)
    print("AIEmpire Content Scheduler")
    print(f"Queue: {QUEUE_FILE}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 50)

    stats = process_queue(
        platform_filter=args.platform,
        dry_run=args.dry_run,
    )

    print(f"\nProcessed: {stats['processed']} items")
    print(f"Files created: {len(stats['files'])}")
    print(f"Skipped: {stats.get('skipped', 0)}")

    if stats["files"] and not args.dry_run:
        print(f"\nOutput directory: {OUTPUT_DIR}")
        print("Files:")
        for f in stats["files"]:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
