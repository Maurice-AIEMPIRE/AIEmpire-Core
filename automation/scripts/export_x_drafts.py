#!/usr/bin/env python3
"""Export best tweets/threads into AI Empire X scheduler draft JSON.

Input: content_factory/deliverables/tweets_300.md and threads_50.md
Output: JSON lists compatible with external/ai-empire/automation/core/x_scheduler.py

This script does NOT post to X. It only writes draft files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


TWEET_PREFIX_RE = re.compile(r"^\s*(\d+)\)\s*(.+?)\s*$")
THREAD_HEADER_RE = re.compile(r"^\s*THREAD\s+(\d+)\s*:\s*$", re.IGNORECASE)
THREAD_LINE_RE = re.compile(r"^\s*(\d+)\)\s*(.+?)\s*$")


@dataclass
class Scored:
    score: float
    text: str
    source_id: str


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _normalize(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9€$% ]+", "", t)
    return t


def _score_tweet(text: str) -> float:
    t = text.strip()
    n = len(t)

    # Length: prefer 110..240 characters, penalize extremes
    score = 0.0
    if 110 <= n <= 240:
        score += 3.0
    elif 80 <= n <= 280:
        score += 1.5
    else:
        score -= 1.0

    if n > 280:
        score -= 4.0

    # Signal tokens
    if re.search(r"\d", t):
        score += 1.0
    if "€" in t or "$" in t:
        score += 0.8
    if "?" in t:
        score += 0.6

    # CTA (light weight)
    if re.search(r"\b(dm|schreib|kommentier|antwort)\b", t, re.IGNORECASE):
        score += 0.5

    # Penalize boilerplate repetition
    boilerplate = [
        "ohne system bleibt es zufall",
        "kopiere den flow",
        "planbar wird es",
    ]
    nt = _normalize(t)
    for bp in boilerplate:
        if bp in nt:
            score -= 0.6

    # Strong framing words
    if re.search(r"\b(fehl(er)?|fix|framework|system|prozess|entscheidung)\b", t, re.IGNORECASE):
        score += 0.4

    return score


def _score_thread(lines: List[str]) -> float:
    if not lines:
        return -999.0

    first = lines[0]
    score = 0.0

    # Hook quality heuristic
    score += _score_tweet(first) * 0.9

    # Prefer 5..9 tweets in a thread
    length = len(lines)
    if 5 <= length <= 9:
        score += 2.0
    elif 3 <= length <= 12:
        score += 1.0
    else:
        score -= 0.5

    # CTA at the end
    last = lines[-1]
    if re.search(r"\b(dm|schreib|kommentier|antwort)\b", last, re.IGNORECASE):
        score += 0.8

    # Penalize if many lines are near-duplicates
    uniq = len({_normalize(x) for x in lines})
    if uniq < max(3, int(length * 0.7)):
        score -= 1.0

    return score


def parse_tweets(md_path: Path) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    for line in _read_text(md_path).splitlines():
        m = TWEET_PREFIX_RE.match(line)
        if not m:
            continue
        idx = m.group(1)
        text = m.group(2).strip()
        if text:
            items.append((idx, text))
    return items


def parse_threads(md_path: Path) -> List[Tuple[str, List[str]]]:
    threads: List[Tuple[str, List[str]]] = []
    current_id: Optional[str] = None
    current_lines: List[str] = []

    for raw in _read_text(md_path).splitlines():
        header = THREAD_HEADER_RE.match(raw)
        if header:
            if current_id and current_lines:
                threads.append((current_id, current_lines))
            current_id = header.group(1)
            current_lines = []
            continue

        m = THREAD_LINE_RE.match(raw)
        if m and current_id:
            # Keep the original "1)" prefix so x_scheduler can split reliably
            current_lines.append(f"{m.group(1)}) {m.group(2).strip()}")

    if current_id and current_lines:
        threads.append((current_id, current_lines))

    return threads


def pick_best_tweets(
    tweets: List[Tuple[str, str]],
    limit: int,
    min_score: float,
) -> List[Scored]:
    scored: List[Scored] = []
    seen = set()
    for idx, text in tweets:
        nt = _normalize(text)
        if nt in seen:
            continue
        seen.add(nt)
        s = _score_tweet(text)
        if s >= min_score:
            scored.append(Scored(score=s, text=text.strip(), source_id=idx))

    scored.sort(key=lambda x: (x.score, len(x.text)), reverse=True)
    return scored[:limit]


def pick_best_threads(
    threads: List[Tuple[str, List[str]]],
    limit: int,
    min_score: float,
) -> List[Tuple[float, str, List[str]]]:
    scored: List[Tuple[float, str, List[str]]] = []
    seen_hooks = set()

    for tid, lines in threads:
        if not lines:
            continue
        hook_norm = _normalize(lines[0])
        if hook_norm in seen_hooks:
            continue
        seen_hooks.add(hook_norm)

        s = _score_thread(lines)
        if s >= min_score:
            scored.append((s, tid, lines))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]


def write_drafts_json(out_dir: Path, kind: str, payload: List[dict]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _now_stamp()
    path = out_dir / f"{kind}_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_drafts_txt(out_dir: Path, kind: str, lines: Iterable[str]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _now_stamp()
    path = out_dir / f"{kind}_{stamp}.txt"
    path.write_text("\n\n".join(lines).strip() + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tweets-md",
        default="content_factory/deliverables/tweets_300.md",
        help="Path to tweets markdown",
    )
    parser.add_argument(
        "--threads-md",
        default="content_factory/deliverables/threads_50.md",
        help="Path to threads markdown",
    )
    parser.add_argument(
        "--outdir",
        default="external/ai-empire/04_OUTPUT/content_pipeline/drafts",
        help="Draft output directory (AI Empire workspace)",
    )
    parser.add_argument("--limit-tweets", type=int, default=60)
    parser.add_argument("--limit-threads", type=int, default=10)
    parser.add_argument("--min-score-tweet", type=float, default=1.0)
    parser.add_argument("--min-score-thread", type=float, default=2.0)

    args = parser.parse_args()

    tweets_path = Path(args.tweets_md)
    threads_path = Path(args.threads_md)
    out_dir = Path(args.outdir)

    if not tweets_path.exists():
        raise SystemExit(f"Missing tweets file: {tweets_path}")
    if not threads_path.exists():
        raise SystemExit(f"Missing threads file: {threads_path}")

    tweets = parse_tweets(tweets_path)
    threads = parse_threads(threads_path)

    best_tweets = pick_best_tweets(tweets, args.limit_tweets, args.min_score_tweet)
    best_threads = pick_best_threads(threads, args.limit_threads, args.min_score_thread)

    tweet_payload = []
    tweet_txt = []
    for item in best_tweets:
        tweet_payload.append(
            {
                "id": f"tweet_{item.source_id}",
                "content_type": "tweet",
                "platform": "x",
                "content": item.text,
                "metadata": {
                    "source": str(tweets_path),
                    "source_id": item.source_id,
                    "score": round(item.score, 3),
                },
            }
        )
        tweet_txt.append(item.text)

    thread_payload = []
    thread_txt = []
    for score, tid, lines in best_threads:
        content = "\n".join(lines).strip()
        thread_payload.append(
            {
                "id": f"thread_{tid}",
                "content_type": "thread",
                "platform": "x",
                "content": content,
                "metadata": {
                    "source": str(threads_path),
                    "source_id": tid,
                    "score": round(score, 3),
                },
            }
        )
        thread_txt.append(content)

    tweets_json = write_drafts_json(out_dir, "tweets", tweet_payload)
    threads_json = write_drafts_json(out_dir, "threads", thread_payload)

    # Also write human-readable txt siblings
    write_drafts_txt(out_dir, "tweets", tweet_txt)
    write_drafts_txt(out_dir, "threads", thread_txt)

    print(f"Exported tweets:   {len(tweet_payload)} -> {tweets_json}")
    print(f"Exported threads:  {len(thread_payload)} -> {threads_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
