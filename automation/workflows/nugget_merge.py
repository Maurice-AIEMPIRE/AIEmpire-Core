from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from automation.utils.files import ensure_dir, write_json, write_text


ROOT = Path(__file__).resolve().parents[2]
NUGGET_DIR = ROOT / "ai-vault" / "nuggets"
REGISTRY_PATH = NUGGET_DIR / "nugget_registry.json"
BACKLOG_PATH = NUGGET_DIR / "nugget_backlog_ranked.md"
X_FEED_IMPORTS_DIR = ROOT / "external" / "imports" / "x_feed_text"
CHATGPT_EXPORTS_DIR = ROOT / "external" / "imports" / "chatgpt_exports"

ALLOWED_ASSET_TYPES = {"hook", "angle", "offer", "process", "metric", "story"}
WEIGHTS = {
    "impact": 0.40,
    "novelty": 0.25,
    "execution_ease": 0.20,
    "time_relevance": 0.15,
}
NEAR_DEDUPE_THRESHOLD = 0.85

TOPIC_KEYWORDS = {
    "short",
    "shorts",
    "youtube",
    "hook",
    "viral",
    "trend",
    "automation",
    "ai",
    "prompt",
    "offer",
    "vault",
    "funnel",
    "conversion",
    "cta",
    "views",
    "retention",
    "comment",
    "like",
}

STOPWORDS = {
    "der",
    "die",
    "das",
    "und",
    "oder",
    "the",
    "for",
    "you",
    "mit",
    "von",
    "ein",
    "eine",
    "auf",
    "ist",
    "sind",
    "this",
    "that",
    "have",
    "with",
    "nicht",
    "kein",
    "einer",
    "einem",
    "your",
}


@dataclass
class RawNugget:
    insight: str
    why: str
    action: str
    tags: List[str]
    asset_type: str
    score: int
    note_title: str
    note_date: str
    source_file: str
    run_id: str


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_dt(value: str) -> Optional[dt.datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if len(raw) == 10:
            d = dt.date.fromisoformat(raw)
            return dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc)
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except ValueError:
        return None


def _normalize_asset_type(value: str) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return "process"
    if raw == "framework":
        return "process"
    if raw in {"angle", "hook", "offer", "process", "metric", "story"}:
        return raw
    return "process"


def _normalize_tags(tags: Any) -> List[str]:
    if not isinstance(tags, list):
        return []
    out = []
    for tag in tags:
        value = str(tag or "").strip().lower()
        if not value:
            continue
        out.append(value)
    # stable order unique
    seen = set()
    uniq = []
    for tag in out:
        if tag in seen:
            continue
        seen.add(tag)
        uniq.append(tag)
    return uniq


def _normalize_text(value: Any, max_len: int = 600) -> str:
    text = " ".join(str(value or "").replace("\r", "\n").split()).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 13].rstrip() + " [TRUNCATED]"


def _nugget_id(insight: str, action: str, asset_type: str) -> str:
    payload = f"{_normalize_text(insight, 300)}|{_normalize_text(action, 300)}|{asset_type}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def _tokenize(text: str) -> List[str]:
    tokens = [t.lower() for t in re.findall(r"[A-Za-zÄÖÜäöüß0-9]{3,}", str(text or ""))]
    return [t for t in tokens if t not in STOPWORDS]


def _token_set(text: str) -> set[str]:
    return set(_tokenize(text))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return inter / union


def _keywords_overlap(text: str) -> int:
    tokens = set(_tokenize(text))
    return sum(1 for key in TOPIC_KEYWORDS if key in tokens)


def _infer_asset_type(text: str) -> str:
    low = str(text or "").lower()
    if any(x in low for x in ["cta", "offer", "produkt", "vault", "preis", "checkout", "gumroad", "stripe"]):
        return "offer"
    if any(x in low for x in ["hook", "stop scrolling", "attention", "pattern interrupt"]):
        return "hook"
    if any(x in low for x in ["story", "ich ", "my story", "case study"]):
        return "story"
    if any(x in low for x in ["views", "vph", "retention", "rate", "%", "ctr", "conversion"]):
        return "metric"
    if any(x in low for x in ["steps", "schritt", "prozess", "workflow", "anleitung", "how to"]):
        return "process"
    if any(x in low for x in ["contrarian", "angle", "myth", "falsch", "gegen"]):
        return "angle"
    return "process"


def _infer_score(text: str, engagement_hint: str = "") -> int:
    score = 2
    overlap = _keywords_overlap(text)
    if overlap >= 4:
        score += 2
    elif overlap >= 2:
        score += 1
    if re.search(r"\b\d+(\.\d+)?[kKmM]?\b", text):
        score += 1
    if engagement_hint and re.search(r"\b(view|like|retweet|reply|comment)\b", engagement_hint, re.IGNORECASE):
        score += 1
    return max(1, min(score, 5))


def _iter_jsonl_files(base_dir: Path, pattern: str, limit_runs: int = 0) -> List[Path]:
    if not base_dir.exists():
        return []
    files = sorted(base_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if limit_runs > 0:
        files = files[:limit_runs]
    return files


def _load_raw_from_x_feed_text(limit_runs: int = 0) -> List[RawNugget]:
    out: List[RawNugget] = []
    files = _iter_jsonl_files(X_FEED_IMPORTS_DIR, "*/x_feed_text_normalized.jsonl", limit_runs=limit_runs)
    for path in files:
        run_id = path.parent.name
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(item, dict):
                continue
            content = _normalize_text(item.get("content"), 500)
            if len(content) < 20:
                continue
            engagement_hint = _normalize_text(item.get("engagement_hints"), 200)
            query = _normalize_text(item.get("query"), 80)
            author = _normalize_text(item.get("author"), 80)
            out.append(
                RawNugget(
                    insight=content,
                    why=_normalize_text(f"x_feed_text author={author} query={query}", 280),
                    action=_normalize_text(
                        "Convert this into a fresh DE AI-Automation short hook + one actionable CTA.",
                        280,
                    ),
                    tags=_normalize_tags(["x", "shorts", query.replace(" ", "_")]),
                    asset_type=_normalize_asset_type(_infer_asset_type(content)),
                    score=_infer_score(content, engagement_hint),
                    note_title=f"x_feed_text:{author}",
                    note_date=_now_iso(),
                    source_file=str(path),
                    run_id=run_id,
                )
            )
    return out


def _load_raw_from_chatgpt_jsonl(limit_runs: int = 0) -> List[RawNugget]:
    out: List[RawNugget] = []
    files = _iter_jsonl_files(CHATGPT_EXPORTS_DIR, "*/normalized_messages.jsonl", limit_runs=limit_runs)
    for path in files:
        run_id = path.parent.name
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip().lower()
            content = _normalize_text(item.get("content"), 500)
            if len(content) < 40:
                continue
            if role not in {"assistant", "user"}:
                continue
            if _keywords_overlap(content) < 2:
                continue
            out.append(
                RawNugget(
                    insight=content,
                    why=_normalize_text(
                        f"chatgpt_export role={role} conversation={item.get('conversation_id')}",
                        280,
                    ),
                    action=_normalize_text(
                        "Extract one reusable hook/angle/process and turn it into a short script skeleton.",
                        280,
                    ),
                    tags=_normalize_tags(["chatgpt_export", role]),
                    asset_type=_normalize_asset_type(_infer_asset_type(content)),
                    score=_infer_score(content),
                    note_title=f"chatgpt_export:{item.get('conversation_id')}",
                    note_date=str(item.get("created_at") or _now_iso()),
                    source_file=str(path),
                    run_id=run_id,
                )
            )
    return out


def _merge_duplicate_items(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    target["seen_count"] = _safe_int(target.get("seen_count"), 0) + _safe_int(source.get("seen_count"), 0)
    target["base_score"] = max(_safe_int(target.get("base_score"), 1), _safe_int(source.get("base_score"), 1))
    target["first_seen"] = min(str(target.get("first_seen") or ""), str(source.get("first_seen") or "")) or str(
        target.get("first_seen") or source.get("first_seen") or _now_iso()
    )
    target["last_seen"] = max(str(target.get("last_seen") or ""), str(source.get("last_seen") or ""))
    target["tags"] = _normalize_tags((target.get("tags") or []) + (source.get("tags") or []))

    runs = target.get("runs") if isinstance(target.get("runs"), list) else []
    for run in source.get("runs") if isinstance(source.get("runs"), list) else []:
        if run not in runs:
            runs.append(run)
    target["runs"] = runs

    sources = target.get("sources") if isinstance(target.get("sources"), list) else []
    for src in source.get("sources") if isinstance(source.get("sources"), list) else []:
        if src not in sources:
            sources.append(src)
    target["sources"] = sources


def _near_dedupe_items(items: List[Dict[str, Any]], threshold: float = NEAR_DEDUPE_THRESHOLD) -> List[Dict[str, Any]]:
    sorted_items = sorted(
        items,
        key=lambda item: (
            item.get("status") != "active",
            -float(item.get("priority_score") or 0.0),
            -_safe_int(item.get("seen_count"), 0),
        ),
    )
    kept: List[Dict[str, Any]] = []
    kept_tokens: List[set[str]] = []
    for item in sorted_items:
        tokens = _token_set(f"{item.get('insight')} {item.get('action')}")
        if not tokens:
            kept.append(item)
            kept_tokens.append(tokens)
            continue
        duplicate_idx = -1
        for idx, prev_tokens in enumerate(kept_tokens):
            if _jaccard(tokens, prev_tokens) >= threshold:
                duplicate_idx = idx
                break
        if duplicate_idx == -1:
            kept.append(item)
            kept_tokens.append(tokens)
            continue
        _merge_duplicate_items(kept[duplicate_idx], item)
    return kept


def _iter_nugget_files(limit_runs: int = 0) -> List[Path]:
    if not NUGGET_DIR.exists():
        return []
    files = sorted(NUGGET_DIR.glob("nuggets_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if limit_runs > 0:
        files = files[:limit_runs]
    return files


def _load_raw_nuggets(limit_runs: int = 0) -> List[RawNugget]:
    out: List[RawNugget] = []
    for path in _iter_nugget_files(limit_runs=limit_runs):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        run_id = str(payload.get("run_id") or path.stem.replace("nuggets_", ""))
        results = payload.get("results")
        if not isinstance(results, list):
            continue

        for item in results:
            if not isinstance(item, dict):
                continue
            note_title = str(item.get("note_title") or "")
            note_date = str(item.get("note_date") or "")
            nuggets = item.get("nuggets")
            if not isinstance(nuggets, list):
                continue
            for nug in nuggets:
                if not isinstance(nug, dict):
                    continue
                insight = _normalize_text(nug.get("insight"), 500)
                action = _normalize_text(nug.get("action"), 400)
                if not insight:
                    continue
                out.append(
                    RawNugget(
                        insight=insight,
                        why=_normalize_text(nug.get("why"), 400),
                        action=action,
                        tags=_normalize_tags(nug.get("tags")),
                        asset_type=_normalize_asset_type(str(nug.get("asset_type") or "")),
                        score=max(1, min(_safe_int(nug.get("score"), 1), 5)),
                        note_title=note_title,
                        note_date=note_date,
                        source_file=str(path),
                        run_id=run_id,
                    )
                )

    # Additional source: x_trends_<run_id>.json produced by x_trend_scout.py
    x_files = sorted(NUGGET_DIR.glob("x_trends_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if limit_runs > 0:
        x_files = x_files[:limit_runs]
    for path in x_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        run_id = str(payload.get("run_id") or path.stem.replace("x_trends_", ""))
        nuggets = payload.get("nuggets")
        if not isinstance(nuggets, list):
            continue
        for nug in nuggets:
            if not isinstance(nug, dict):
                continue
            insight = _normalize_text(nug.get("content"), 500)
            if not insight:
                continue
            ranking = nug.get("ranking") if isinstance(nug.get("ranking"), dict) else {}
            impact = _safe_int(ranking.get("impact"), 5)
            score = max(1, min(5, int(round(impact / 2))))
            action = _normalize_text(
                f"Adapt angle={((nug.get('meta') or {}).get('angle_type') if isinstance(nug.get('meta'), dict) else 'general')} "
                f"mit Viral-Signalen: {((nug.get('viral_signals') or {}).get('score') if isinstance(nug.get('viral_signals'), dict) else '')}",
                300,
            )
            out.append(
                RawNugget(
                    insight=insight,
                    why=_normalize_text(nug.get("full_context"), 400),
                    action=action,
                    tags=_normalize_tags(((nug.get("meta") or {}).get("hashtags") if isinstance(nug.get("meta"), dict) else [])),
                    asset_type=_normalize_asset_type(str(nug.get("asset_type") or "")),
                    score=score,
                    note_title="x_trend_scout",
                    note_date=_now_iso(),
                    source_file=str(path),
                    run_id=run_id,
                )
            )
    out.extend(_load_raw_from_x_feed_text(limit_runs=limit_runs))
    out.extend(_load_raw_from_chatgpt_jsonl(limit_runs=limit_runs))
    return out


def _impact(raw: RawNugget) -> float:
    base = raw.score / 5.0
    if raw.asset_type in {"offer", "metric"}:
        base += 0.1
    return max(0.0, min(base, 1.0))


def _execution_ease(raw: RawNugget) -> float:
    action_len = len(raw.action or "")
    base = 0.7
    if raw.asset_type in {"hook", "angle"}:
        base += 0.2
    if raw.asset_type in {"process", "story"}:
        base -= 0.1
    if action_len > 180:
        base -= 0.2
    elif action_len > 110:
        base -= 0.1
    elif action_len < 70:
        base += 0.1
    return max(0.0, min(base, 1.0))


def _time_relevance(last_seen: str) -> float:
    last_dt = _parse_dt(last_seen)
    if not last_dt:
        return 0.5
    age_days = max(0.0, (dt.datetime.now(dt.timezone.utc) - last_dt).total_seconds() / 86400.0)
    if age_days <= 1:
        return 1.0
    if age_days <= 7:
        return 0.9
    if age_days <= 30:
        return 0.7
    if age_days <= 90:
        return 0.5
    return 0.3


def _score_registry_item(item: Dict[str, Any]) -> None:
    asset = _normalize_asset_type(str(item.get("asset_type") or ""))
    item["asset_type"] = asset
    if asset not in ALLOWED_ASSET_TYPES:
        item["status"] = "excluded"
    else:
        item["status"] = "active"

    base_score = max(1, min(_safe_int(item.get("base_score"), 1), 5))
    seen_count = max(1, _safe_int(item.get("seen_count"), 1))
    novelty = 1.0 / seen_count

    pseudo_raw = RawNugget(
        insight=str(item.get("insight") or ""),
        why=str(item.get("why") or ""),
        action=str(item.get("action") or ""),
        tags=_normalize_tags(item.get("tags")),
        asset_type=asset,
        score=base_score,
        note_title="",
        note_date=str(item.get("last_seen") or ""),
        source_file="",
        run_id="",
    )
    impact = _impact(pseudo_raw)
    execution_ease = _execution_ease(pseudo_raw)
    time_relevance = _time_relevance(str(item.get("last_seen") or ""))

    item["impact"] = round(impact, 4)
    item["novelty"] = round(novelty, 4)
    item["execution_ease"] = round(execution_ease, 4)
    item["time_relevance"] = round(time_relevance, 4)
    priority = (
        impact * WEIGHTS["impact"]
        + novelty * WEIGHTS["novelty"]
        + execution_ease * WEIGHTS["execution_ease"]
        + time_relevance * WEIGHTS["time_relevance"]
    )
    item["priority_score"] = round(priority * 100, 2)


def _render_backlog(items: List[Dict[str, Any]], top_n: int = 120) -> str:
    lines: List[str] = []
    lines.append("# Nugget Backlog (Ranked)")
    lines.append("")
    lines.append(f"Updated: {_now_iso()}")
    lines.append("")
    lines.append("Allowed asset types: hook, angle, offer, process, metric, story")
    lines.append("")

    active_items = [item for item in items if item.get("asset_type") in ALLOWED_ASSET_TYPES and item.get("status") == "active"]
    top_24h = sorted(
        active_items,
        key=lambda item: (
            -float(item.get("priority_score") or 0.0),
            -float(item.get("time_relevance") or 0.0),
            -_safe_int(item.get("seen_count"), 0),
        ),
    )[:10]
    lines.append("## Top 10 fuer naechste 24h")
    lines.append("")
    if top_24h:
        for idx, item in enumerate(top_24h, start=1):
            lines.append(
                f"{idx}. [{item.get('asset_type')}] {_normalize_text(item.get('insight'), 140)} "
                f"(score={item.get('priority_score')}, relevance={item.get('time_relevance')})"
            )
    else:
        lines.append("- Keine priorisierten Nuggets vorhanden.")
    lines.append("")

    rank = 0
    for item in items:
        if item.get("asset_type") not in ALLOWED_ASSET_TYPES:
            continue
        rank += 1
        if rank > top_n:
            break
        lines.append(f"## {rank}. [{item.get('asset_type')}] {item.get('insight')}")
        lines.append(f"- Priority score: {item.get('priority_score')}")
        lines.append(f"- Action: {item.get('action')}")
        if item.get("why"):
            lines.append(f"- Why: {item.get('why')}")
        tags = item.get("tags") or []
        if tags:
            lines.append(f"- Tags: {', '.join(tags)}")
        lines.append(f"- Seen: {item.get('seen_count')} | Last seen: {item.get('last_seen')}")
        sources = item.get("sources") or []
        if sources:
            lines.append(f"- Sources: {', '.join(sources[:4])}")
        lines.append("")

    if rank == 0:
        lines.append("_No allowed nuggets found yet. Run ingest first._")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def merge_nuggets_registry(limit_runs: int = 0) -> Tuple[Path, Path, int]:
    ensure_dir(NUGGET_DIR)
    now_iso = _now_iso()
    raw_nuggets = _load_raw_nuggets(limit_runs=limit_runs)

    existing: Dict[str, Dict[str, Any]] = {}
    if REGISTRY_PATH.exists():
        try:
            payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            for item in payload.get("items", []) if isinstance(payload, dict) else []:
                if not isinstance(item, dict):
                    continue
                nugget_id = str(item.get("id") or "")
                if nugget_id:
                    existing[nugget_id] = item
        except json.JSONDecodeError:
            existing = {}

    merged: Dict[str, Dict[str, Any]] = dict(existing)
    for raw in raw_nuggets:
        nugget_id = _nugget_id(raw.insight, raw.action, raw.asset_type)
        item = merged.get(nugget_id)
        if item is None:
            item = {
                "id": nugget_id,
                "insight": raw.insight,
                "why": raw.why,
                "action": raw.action,
                "tags": raw.tags,
                "asset_type": raw.asset_type,
                "base_score": raw.score,
                "first_seen": raw.note_date or now_iso,
                "last_seen": raw.note_date or now_iso,
                "seen_count": 0,
                "runs": [],
                "sources": [],
            }
            merged[nugget_id] = item

        item["base_score"] = max(_safe_int(item.get("base_score"), 1), raw.score)
        item["insight"] = item.get("insight") or raw.insight
        item["why"] = item.get("why") or raw.why
        item["action"] = item.get("action") or raw.action
        item["asset_type"] = _normalize_asset_type(str(item.get("asset_type") or raw.asset_type))

        tags = _normalize_tags((item.get("tags") or []) + raw.tags)
        item["tags"] = tags

        seen_count = _safe_int(item.get("seen_count"), 0) + 1
        item["seen_count"] = seen_count

        last_seen = str(item.get("last_seen") or "")
        if raw.note_date and (not last_seen or raw.note_date > last_seen):
            item["last_seen"] = raw.note_date
        elif not last_seen:
            item["last_seen"] = now_iso

        runs = item.get("runs")
        if not isinstance(runs, list):
            runs = []
        if raw.run_id not in runs:
            runs.append(raw.run_id)
        item["runs"] = runs

        sources = item.get("sources")
        if not isinstance(sources, list):
            sources = []
        source_key = Path(raw.source_file).name
        if source_key not in sources:
            sources.append(source_key)
        item["sources"] = sources

    items = list(merged.values())
    for item in items:
        _score_registry_item(item)

    items = _near_dedupe_items(items, threshold=NEAR_DEDUPE_THRESHOLD)
    for item in items:
        _score_registry_item(item)

    items.sort(
        key=lambda item: (
            item.get("status") != "active",
            -float(item.get("priority_score") or 0.0),
            -_safe_int(item.get("seen_count"), 0),
        )
    )

    write_json(
        REGISTRY_PATH,
        {
            "updated_at": now_iso,
            "weights": WEIGHTS,
            "allowed_asset_types": sorted(ALLOWED_ASSET_TYPES),
            "count": len(items),
            "items": items,
        },
    )
    write_text(BACKLOG_PATH, _render_backlog(items))
    return REGISTRY_PATH, BACKLOG_PATH, len(items)
