from __future__ import annotations

import csv
import datetime as dt
import json
import math
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation.core.runner import Runner
from automation.gemini_video import GeminiVideoRequest, render_video_with_gemini
from automation.n8n_events import post_n8n_event
from automation.utils.files import ensure_dir, env_or_default, slugify, timestamp_id, write_json, write_text
from automation.workflows.shorts_strategy_state import (
    build_strategy_prompt_context,
    load_strategy_state,
    load_top_nuggets,
    save_strategy_state,
    update_strategy_from_metrics,
)


ROOT = Path(__file__).resolve().parents[2]
DELIVERABLES_DIR = ROOT / "content_factory" / "deliverables" / "youtube_shorts"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


DEFAULT_BANNED_TERMS = [
    "racist",
    "racism",
    "nazi",
    "hitler",
    "white supremacy",
    "antisemit",
    "ethnic cleansing",
    "hate crime",
    "genocide",
    "lynching",
    "kkk",
    "xenophob",
    "neo-nazi",
    "aryan",
    "apartheid",
]


@dataclass
class TrendItem:
    video_id: str
    title: str
    channel: str
    published_at: str
    duration_seconds: int
    views: int
    likes: int
    comments: int
    tags: List[str] = field(default_factory=list)
    source_query: str = ""
    virality_score: float = 0.0


@dataclass
class ShortsDraft:
    title: str
    hook: str
    script: str
    cta: str
    hashtags: List[str]
    tone: str
    source_video_id: str
    safety_notes: str = "safe"
    video_file: str = ""
    video_status: str = "not_requested"
    video_operation: str = ""
    video_error: str = ""


@dataclass
class WorkflowConfig:
    run_id: str
    execute: bool
    youtube_api_key: str = ""
    channel_id: str = ""
    region: str = "US"
    language: str = "de"
    lookback_hours: int = 24
    drafts_per_run: int = 6
    min_views_per_hour_target: float = 120.0
    queries: List[str] = field(default_factory=list)
    banned_terms: List[str] = field(default_factory=lambda: DEFAULT_BANNED_TERMS.copy())
    gemini_api_key: str = ""
    gemini_video_enabled: bool = True
    gemini_model: str = "veo-3.1-fast-generate-preview"
    gemini_aspect_ratio: str = "9:16"
    gemini_resolution: str = "720p"
    gemini_duration_seconds: int = 8
    gemini_negative_prompt: str = ""
    gemini_max_renders_per_run: int = 3
    gemini_poll_interval_seconds: int = 10
    gemini_max_poll_attempts: int = 90


def _iso_utc_hours_ago(hours: int) -> str:
    ts = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=max(1, hours))
    return ts.isoformat().replace("+00:00", "Z")


def _to_int(value: Any) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _json_get(url: str, params: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": "ai-empire-youtube/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = resp.read().decode("utf-8")
    return json.loads(payload)


def _parse_iso8601_duration(raw: str) -> int:
    # Parse subset like PT34S, PT1M20S, PT2H1M5S
    if not raw or not raw.startswith("PT"):
        return 0
    hours = minutes = seconds = 0
    m = re.search(r"(\d+)H", raw)
    if m:
        hours = int(m.group(1))
    m = re.search(r"(\d+)M", raw)
    if m:
        minutes = int(m.group(1))
    m = re.search(r"(\d+)S", raw)
    if m:
        seconds = int(m.group(1))
    return hours * 3600 + minutes * 60 + seconds


def _contains_banned_terms(text: str, banned_terms: List[str]) -> bool:
    low = text.lower()
    return any(term in low for term in banned_terms)


def _safe_trim(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _extract_json_array(raw: str) -> Optional[List[Dict[str, Any]]]:
    raw = raw.strip()
    if not raw:
        return None

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    except json.JSONDecodeError:
        pass

    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return None

    snippet = raw[start : end + 1]
    try:
        parsed = json.loads(snippet)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    except json.JSONDecodeError:
        return None
    return None


def _score_trend(views: int, likes: int, comments: int, age_hours: float) -> float:
    age_hours = max(age_hours, 1.0)
    velocity = views / age_hours
    like_rate = likes / views if views > 0 else 0.0
    comment_rate = comments / views if views > 0 else 0.0
    return velocity * 0.7 + (like_rate * 1000) * 0.2 + (comment_rate * 1000) * 0.1


def _hours_since_iso(raw: str) -> float:
    if not raw:
        return 48.0
    try:
        dt_value = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return 48.0
    now = dt.datetime.now(dt.timezone.utc)
    delta = now - dt_value.astimezone(dt.timezone.utc)
    return max(delta.total_seconds() / 3600.0, 1.0)


def _load_fallback_trends(config: WorkflowConfig) -> List[TrendItem]:
    fallback = [
        "AI News in 30 seconds",
        "Motivation and self-discipline",
        "Insane productivity hacks",
        "Money mindset myths",
        "Story-driven mini lessons",
        "Fun facts that sound fake but true",
    ]
    items: List[TrendItem] = []
    for idx, topic in enumerate(fallback, start=1):
        items.append(
            TrendItem(
                video_id=f"fallback_{idx}",
                title=topic,
                channel="fallback",
                published_at=dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                duration_seconds=35,
                views=1000 - idx * 50,
                likes=120 - idx * 7,
                comments=25 - idx,
                tags=["#shorts", "#motivation", "#ai"],
                source_query="fallback",
                virality_score=900 - idx * 20,
            )
        )
    return items


def fetch_trends_from_youtube(config: WorkflowConfig) -> List[TrendItem]:
    if not config.youtube_api_key:
        return _load_fallback_trends(config)

    published_after = _iso_utc_hours_ago(config.lookback_hours)
    queries = config.queries or [
        "funny shorts",
        "inspiring shorts",
        "ai news shorts",
        "success mindset shorts",
    ]

    all_candidates: Dict[str, Dict[str, Any]] = {}
    for query in queries:
        params = {
            "part": "snippet",
            "type": "video",
            "videoDuration": "short",
            "maxResults": 15,
            "order": "viewCount",
            "publishedAfter": published_after,
            "q": query,
            "regionCode": config.region,
            "relevanceLanguage": config.language,
            "key": config.youtube_api_key,
        }
        try:
            payload = _json_get(YOUTUBE_SEARCH_URL, params)
        except Exception:
            continue

        for item in payload.get("items", []):
            video_id = ((item.get("id") or {}).get("videoId") or "").strip()
            if not video_id:
                continue
            snippet = item.get("snippet") or {}
            title = str(snippet.get("title") or "")
            if _contains_banned_terms(title, config.banned_terms):
                continue
            if video_id not in all_candidates:
                all_candidates[video_id] = {
                    "video_id": video_id,
                    "title": title,
                    "channel": str(snippet.get("channelTitle") or ""),
                    "published_at": str(snippet.get("publishedAt") or ""),
                    "source_query": query,
                }

    if not all_candidates:
        return _load_fallback_trends(config)

    video_ids = ",".join(all_candidates.keys())
    stats_params = {
        "part": "snippet,statistics,contentDetails",
        "id": video_ids,
        "maxResults": 50,
        "key": config.youtube_api_key,
    }

    try:
        stats_payload = _json_get(YOUTUBE_VIDEOS_URL, stats_params)
    except Exception:
        return _load_fallback_trends(config)

    trends: List[TrendItem] = []
    for item in stats_payload.get("items", []):
        video_id = str(item.get("id") or "")
        if video_id not in all_candidates:
            continue

        stats = item.get("statistics") or {}
        details = item.get("contentDetails") or {}
        snippet = item.get("snippet") or {}

        duration = _parse_iso8601_duration(str(details.get("duration") or ""))
        if duration <= 0 or duration > 65:
            continue

        title = str(snippet.get("title") or all_candidates[video_id]["title"])
        if _contains_banned_terms(title, config.banned_terms):
            continue

        views = _to_int(stats.get("viewCount"))
        likes = _to_int(stats.get("likeCount"))
        comments = _to_int(stats.get("commentCount"))
        published_at = str(snippet.get("publishedAt") or all_candidates[video_id]["published_at"])
        age_hours = _hours_since_iso(published_at)

        trend = TrendItem(
            video_id=video_id,
            title=title,
            channel=str(snippet.get("channelTitle") or all_candidates[video_id]["channel"]),
            published_at=published_at,
            duration_seconds=duration,
            views=views,
            likes=likes,
            comments=comments,
            tags=[str(tag) for tag in (snippet.get("tags") or [])[:8]],
            source_query=str(all_candidates[video_id]["source_query"]),
            virality_score=_score_trend(views, likes, comments, age_hours),
        )
        trends.append(trend)

    trends.sort(key=lambda x: x.virality_score, reverse=True)
    if not trends:
        return _load_fallback_trends(config)
    return trends[:20]


def _drafts_from_fallback(trends: List[TrendItem], draft_count: int) -> List[ShortsDraft]:
    out: List[ShortsDraft] = []
    for idx, trend in enumerate(trends[:draft_count], start=1):
        title = _safe_trim(f"{trend.title} | 35s Breakdown", 88)
        hook = _safe_trim(f"Stop scrolling: {trend.title} in 30 seconds.", 110)
        script = (
            f"Hook: {hook}\n"
            f"Main: Kurzer Kontext zu '{trend.title}', 3 klare Punkte, 1 konkreter Nutzen fuer heute.\n"
            "Close: Sag in 1 Satz, was die Zuschauer als naechstes tun sollen."
        )
        cta = "Schreib 'MEHR' in die Kommentare fuer den naechsten Teil."
        hashtags = ["#shorts", "#motivation", "#mindset", "#ai"]
        out.append(
            ShortsDraft(
                title=title,
                hook=hook,
                script=script,
                cta=cta,
                hashtags=hashtags,
                tone="inspiriert + direkt",
                source_video_id=trend.video_id,
                safety_notes="safe",
            )
        )
    return out


def _trim_to_words(text: str, max_words: int) -> str:
    words = [w for w in re.split(r"\s+", str(text or "").strip()) if w]
    if max_words <= 0 or len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).strip()


def _apply_adaptive_rules(draft: ShortsDraft, strategy_state: Dict[str, Any]) -> None:
    adaptive = strategy_state.get("adaptive") if isinstance(strategy_state.get("adaptive"), dict) else {}
    low_streak = int(adaptive.get("low_vph_streak") or 0)
    cta_binary_required = bool(adaptive.get("cta_binary_required"))
    emotional_boost = bool(adaptive.get("emotional_framing_boost"))
    hook_intensity = int(adaptive.get("hook_intensity") or 1)
    cap = int(adaptive.get("script_hook_setup_word_cap") or 120)
    force_new_angle = bool(adaptive.get("force_new_angle_cluster"))

    if low_streak >= 2:
        draft.hook = _safe_trim(f"Stop! {draft.hook}", 120)
        draft.script = _trim_to_words(draft.script, max_words=max(30, min(cap, 120)))

    if emotional_boost and "wahrheit" not in draft.hook.lower():
        draft.hook = _safe_trim(f"Die harte Wahrheit: {draft.hook}", 120)

    if cta_binary_required:
        draft.cta = "Kommentiere nur EIN Wort: JA oder NEIN?"

    if hook_intensity >= 4 and not draft.hook.strip().endswith("?"):
        draft.hook = _safe_trim(draft.hook + " Wirklich?", 120)

    if force_new_angle:
        # Marker for downstream analysis that this draft belongs to a forced new-angle cluster.
        if "#newangle" not in [t.lower() for t in draft.hashtags]:
            draft.hashtags.insert(0, "#newangle")


def generate_shorts_drafts(
    runner: Runner,
    config: WorkflowConfig,
    trends: List[TrendItem],
    strategy_context: str = "",
    strategy_state: Optional[Dict[str, Any]] = None,
) -> List[ShortsDraft]:
    if not trends:
        return []

    trend_lines = []
    for idx, trend in enumerate(trends[:12], start=1):
        trend_lines.append(
            f"{idx}. title={trend.title} | views={trend.views} | likes={trend.likes} | comments={trend.comments} | vid={trend.video_id}"
        )

    prompt = (
        "Erstelle virale, sichere YouTube-Shorts-Drafts auf Deutsch.\n"
        "Regeln:\n"
        "- Keine rassistischen, diskriminierenden oder hetzerischen Inhalte.\n"
        "- Keine 1:1 Kopie von Vorlagen, nur Struktur adaptieren.\n"
        "- Fokus: humorvoll, inspirierend, spannend, hoher emotionaler Impact.\n"
        "- Keine unpruefbaren Einkommensversprechen (kein 'garantierter Verdienst', kein 'sicher reich werden').\n"
        "- Dauer je Short: 25-45 Sekunden.\n"
        "- Gib AUSSCHLIESSLICH JSON-Liste zurueck, ohne Markdown.\n"
        "Schema je Element:\n"
        "{\"title\":\"...\",\"hook\":\"...\",\"script\":\"...\",\"cta\":\"...\",\"hashtags\":[\"#shorts\"],\"tone\":\"...\",\"source_video_id\":\"...\"}\n"
        f"Anzahl: {config.drafts_per_run}\n"
        + (strategy_context.strip() + "\n" if strategy_context.strip() else "")
        + "\n"
        "Trend-Inputs:\n"
        + "\n".join(trend_lines)
    )

    result = runner.run_task("writer_shorts", prompt)
    raw = result.text or ""

    parsed = _extract_json_array(raw)
    if not parsed:
        return _drafts_from_fallback(trends, config.drafts_per_run)

    drafts: List[ShortsDraft] = []
    for item in parsed:
        title = _safe_trim(str(item.get("title") or ""), 88)
        hook = _safe_trim(str(item.get("hook") or ""), 120)
        script = str(item.get("script") or "").strip()
        cta = _safe_trim(str(item.get("cta") or ""), 120)
        hashtags = item.get("hashtags") or []
        tone = str(item.get("tone") or "")
        source_video_id = str(item.get("source_video_id") or "")

        if not title or not hook or not script or not cta:
            continue
        if _contains_banned_terms(" ".join([title, hook, script, cta]), config.banned_terms):
            continue

        clean_tags = []
        for tag in hashtags:
            t = str(tag).strip()
            if not t:
                continue
            if not t.startswith("#"):
                t = "#" + t.replace(" ", "")
            clean_tags.append(t)

        if "#shorts" not in [t.lower() for t in clean_tags]:
            clean_tags.insert(0, "#shorts")

        drafts.append(
            ShortsDraft(
                title=title,
                hook=hook,
                script=script,
                cta=cta,
                hashtags=clean_tags[:8],
                tone=tone or "direkt",
                source_video_id=source_video_id,
                safety_notes="safe",
            )
        )

    if not drafts:
        return _drafts_from_fallback(trends, config.drafts_per_run)

    if isinstance(strategy_state, dict):
        for draft in drafts:
            _apply_adaptive_rules(draft, strategy_state)

    return drafts[: config.drafts_per_run]


def _video_prompt_for_draft(draft: ShortsDraft, trend_title: str) -> str:
    return (
        "Create a cinematic, social-first vertical short video for YouTube Shorts/TikTok.\n"
        "Output requirements:\n"
        "- Aspect ratio 9:16, dynamic camera motion, high contrast lighting.\n"
        "- No logos, no watermarks, no subtitles burned in.\n"
        "- Emotionally strong first second, clear narrative progression.\n"
        "- Visuals must match this script and stay safe-for-work.\n"
        f"Topic context: {trend_title}\n"
        f"Hook: {draft.hook}\n"
        f"Script core: {draft.script}\n"
        f"CTA mood: {draft.cta}\n"
        "Return only the generated video."
    )


def render_drafts_with_gemini(config: WorkflowConfig, drafts: List[ShortsDraft], trends: List[TrendItem], run_dir: Path) -> Dict[str, Any]:
    trend_map = {t.video_id: t for t in trends}
    videos_dir = run_dir / "videos"
    ensure_dir(videos_dir)

    rendered = 0
    records: List[Dict[str, Any]] = []

    for idx, draft in enumerate(drafts, start=1):
        if idx > max(0, config.gemini_max_renders_per_run):
            draft.video_status = "skipped"
            draft.video_error = "render_limit_reached"
            records.append(
                {
                    "slot": idx,
                    "title": draft.title,
                    "status": draft.video_status,
                    "error": draft.video_error,
                    "video_file": "",
                    "operation_name": "",
                }
            )
            continue

        slug = slugify(draft.title)
        output_path = videos_dir / f"{idx:02d}_{slug}.mp4"
        trend_title = (trend_map.get(draft.source_video_id).title if trend_map.get(draft.source_video_id) else draft.title)
        prompt = _video_prompt_for_draft(draft, trend_title)

        if not config.execute:
            draft.video_status = "planned"
            draft.video_file = str(output_path)
            records.append(
                {
                    "slot": idx,
                    "title": draft.title,
                    "status": draft.video_status,
                    "error": "",
                    "video_file": draft.video_file,
                    "operation_name": "",
                    "provider": "gemini",
                }
            )
            continue

        if not config.gemini_video_enabled:
            draft.video_status = "skipped"
            draft.video_error = "gemini_video_disabled"
            records.append(
                {
                    "slot": idx,
                    "title": draft.title,
                    "status": draft.video_status,
                    "error": draft.video_error,
                    "video_file": "",
                    "operation_name": "",
                    "provider": "gemini",
                }
            )
            continue

        request = GeminiVideoRequest(
            prompt=prompt,
            output_path=output_path,
            api_key=config.gemini_api_key,
            model=config.gemini_model,
            aspect_ratio=config.gemini_aspect_ratio,
            resolution=config.gemini_resolution,
            duration_seconds=config.gemini_duration_seconds,
            negative_prompt=config.gemini_negative_prompt,
            poll_interval_seconds=config.gemini_poll_interval_seconds,
            max_poll_attempts=config.gemini_max_poll_attempts,
        )
        result = render_video_with_gemini(request)

        draft.video_status = str(result.get("status") or "failed")
        draft.video_file = str(result.get("output_file") or "")
        draft.video_operation = str(result.get("operation_name") or "")
        draft.video_error = str(result.get("error") or "")
        if bool(result.get("ok")):
            rendered += 1

        records.append(
            {
                "slot": idx,
                "title": draft.title,
                "status": draft.video_status,
                "error": draft.video_error,
                "video_file": draft.video_file,
                "operation_name": draft.video_operation,
                "video_uri": str(result.get("video_uri") or ""),
                "provider": "gemini",
            }
        )

    return {
        "provider": "gemini",
        "enabled": bool(config.gemini_video_enabled),
        "execute": bool(config.execute),
        "model": config.gemini_model,
        "render_limit": int(max(0, config.gemini_max_renders_per_run)),
        "rendered_count": rendered,
        "items": records,
    }


def collect_channel_shorts_metrics(config: WorkflowConfig) -> Dict[str, Any]:
    empty = {
        "videos": [],
        "summary": {
            "count": 0,
            "avg_views": 0,
            "avg_views_per_hour": 0,
            "avg_like_rate": 0,
            "avg_comment_rate": 0,
        },
    }

    if not config.youtube_api_key or not config.channel_id:
        return empty

    params = {
        "part": "snippet",
        "channelId": config.channel_id,
        "type": "video",
        "order": "date",
        "maxResults": 20,
        "key": config.youtube_api_key,
    }
    try:
        search_payload = _json_get(YOUTUBE_SEARCH_URL, params)
    except Exception:
        return empty

    ids = []
    for item in search_payload.get("items", []):
        vid = ((item.get("id") or {}).get("videoId") or "").strip()
        if vid:
            ids.append(vid)

    if not ids:
        return empty

    stats_params = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(ids),
        "maxResults": 50,
        "key": config.youtube_api_key,
    }

    try:
        payload = _json_get(YOUTUBE_VIDEOS_URL, stats_params)
    except Exception:
        return empty

    videos = []
    for item in payload.get("items", []):
        details = item.get("contentDetails") or {}
        duration = _parse_iso8601_duration(str(details.get("duration") or ""))
        if duration <= 0 or duration > 65:
            continue

        stats = item.get("statistics") or {}
        snippet = item.get("snippet") or {}
        views = _to_int(stats.get("viewCount"))
        likes = _to_int(stats.get("likeCount"))
        comments = _to_int(stats.get("commentCount"))
        published_at = str(snippet.get("publishedAt") or "")
        age_hours = _hours_since_iso(published_at)

        videos.append(
            {
                "video_id": str(item.get("id") or ""),
                "title": str(snippet.get("title") or ""),
                "published_at": published_at,
                "views": views,
                "likes": likes,
                "comments": comments,
                "duration_seconds": duration,
                "views_per_hour": round(views / age_hours, 2),
                "like_rate": round((likes / views) if views else 0.0, 4),
                "comment_rate": round((comments / views) if views else 0.0, 4),
            }
        )

    if not videos:
        return empty

    count = len(videos)
    avg_views = sum(v["views"] for v in videos) / count
    avg_vph = sum(v["views_per_hour"] for v in videos) / count
    avg_like_rate = sum(v["like_rate"] for v in videos) / count
    avg_comment_rate = sum(v["comment_rate"] for v in videos) / count

    videos.sort(key=lambda x: x["views_per_hour"], reverse=True)

    return {
        "videos": videos,
        "winners": videos[:3],
        "laggards": videos[-3:],
        "summary": {
            "count": count,
            "avg_views": round(avg_views, 2),
            "avg_views_per_hour": round(avg_vph, 2),
            "avg_like_rate": round(avg_like_rate, 4),
            "avg_comment_rate": round(avg_comment_rate, 4),
        },
    }


def build_feedback_plan(config: WorkflowConfig, metrics: Dict[str, Any], drafts: List[ShortsDraft]) -> str:
    summary = metrics.get("summary") or {}
    avg_vph = float(summary.get("avg_views_per_hour") or 0.0)
    avg_like = float(summary.get("avg_like_rate") or 0.0)
    avg_comment = float(summary.get("avg_comment_rate") or 0.0)

    lines = [
        "# YouTube Shorts Feedback Plan",
        "",
        f"- Target views/hour: {config.min_views_per_hour_target}",
        f"- Current avg views/hour: {avg_vph}",
        f"- Current avg like rate: {avg_like}",
        f"- Current avg comment rate: {avg_comment}",
        "",
        "## Actions for next run",
    ]

    if avg_vph <= 0:
        lines.append("- No channel metrics available. Publish first batch and collect IDs for 2h/6h/24h checks.")
    elif avg_vph < config.min_views_per_hour_target:
        lines.append("- Increase hook intensity in first 2 seconds (question + strong claim).")
        lines.append("- Cut script length by 15% and force visual change every 2-3 seconds.")
        lines.append("- Pause low-performing topic clusters and test 2 new topic angles.")
    else:
        lines.append("- Keep winning format and publish 2 additional variants with same narrative pattern.")
        lines.append("- Reuse best performing hooks with new context, do not clone text.")

    if avg_like < 0.03:
        lines.append("- Add clearer emotional framing and direct value statement before second 5.")
    if avg_comment < 0.005:
        lines.append("- Improve CTA specificity (ask for one-word opinion or binary choice).")

    lines.append("")
    lines.append("## Drafts generated this run")
    for idx, draft in enumerate(drafts, start=1):
        lines.append(f"- {idx}. {draft.title}")

    return "\n".join(lines).strip() + "\n"


def _write_publish_queue(path: Path, drafts: List[ShortsDraft], trends: List[TrendItem]) -> None:
    trend_map = {t.video_id: t for t in trends}
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "slot",
                "title",
                "hook",
                "script",
                "cta",
                "hashtags",
                "source_video_id",
                "source_title",
                "source_channel",
                "video_file",
                "video_status",
                "video_operation",
                "video_error",
                "upload_status",
            ],
        )
        writer.writeheader()
        for idx, draft in enumerate(drafts, start=1):
            trend = trend_map.get(draft.source_video_id)
            writer.writerow(
                {
                    "slot": idx,
                    "title": draft.title,
                    "hook": draft.hook,
                    "script": draft.script,
                    "cta": draft.cta,
                    "hashtags": " ".join(draft.hashtags),
                    "source_video_id": draft.source_video_id,
                    "source_title": trend.title if trend else "",
                    "source_channel": trend.channel if trend else "",
                    "video_file": draft.video_file,
                    "video_status": draft.video_status,
                    "video_operation": draft.video_operation,
                    "video_error": draft.video_error,
                    "upload_status": "ready",
                }
            )


def run_youtube_shorts(
    runner: Runner,
    *,
    execute: bool,
    channel_id: Optional[str],
    region: str,
    language: str,
    lookback_hours: int,
    drafts_per_run: int,
    min_views_per_hour_target: float,
    queries: Optional[List[str]] = None,
    gemini_video_enabled: bool = True,
    gemini_model: str = "veo-3.1-fast-generate-preview",
    gemini_aspect_ratio: str = "9:16",
    gemini_resolution: str = "720p",
    gemini_duration_seconds: int = 8,
    gemini_negative_prompt: str = "",
    gemini_max_renders_per_run: int = 3,
    gemini_poll_interval_seconds: int = 10,
    gemini_max_poll_attempts: int = 90,
) -> str:
    run_id = runner.run_id or timestamp_id()
    run_dir = DELIVERABLES_DIR / run_id
    ensure_dir(run_dir)

    cfg = WorkflowConfig(
        run_id=run_id,
        execute=execute,
        youtube_api_key=env_or_default("YOUTUBE_API_KEY", "") or "",
        channel_id=(channel_id or env_or_default("YOUTUBE_CHANNEL_ID", "") or "").strip(),
        region=(region or "US").strip() or "US",
        language=(language or "de").strip() or "de",
        lookback_hours=max(1, lookback_hours),
        drafts_per_run=max(1, drafts_per_run),
        min_views_per_hour_target=max(1.0, float(min_views_per_hour_target)),
        queries=[q.strip() for q in (queries or []) if q.strip()],
        gemini_api_key=env_or_default("GEMINI_API_KEY", "") or "",
        gemini_video_enabled=bool(gemini_video_enabled),
        gemini_model=(gemini_model or "veo-3.1-fast-generate-preview").strip() or "veo-3.1-fast-generate-preview",
        gemini_aspect_ratio=(gemini_aspect_ratio or "9:16").strip() or "9:16",
        gemini_resolution=(gemini_resolution or "720p").strip() or "720p",
        gemini_duration_seconds=max(4, min(8, int(gemini_duration_seconds))),
        gemini_negative_prompt=(gemini_negative_prompt or "").strip(),
        gemini_max_renders_per_run=max(0, int(gemini_max_renders_per_run)),
        gemini_poll_interval_seconds=max(1, int(gemini_poll_interval_seconds)),
        gemini_max_poll_attempts=max(1, int(gemini_max_poll_attempts)),
    )

    strategy_state = load_strategy_state()
    top_nuggets = load_top_nuggets(limit=8)
    strategy_context = build_strategy_prompt_context(strategy_state, top_nuggets)

    trends = fetch_trends_from_youtube(cfg)
    drafts = generate_shorts_drafts(
        runner,
        cfg,
        trends,
        strategy_context=strategy_context,
        strategy_state=strategy_state,
    )
    video_renders = render_drafts_with_gemini(cfg, drafts, trends, run_dir)
    metrics = collect_channel_shorts_metrics(cfg)
    feedback_plan = build_feedback_plan(cfg, metrics, drafts)

    trends_payload = [
        {
            "video_id": t.video_id,
            "title": t.title,
            "channel": t.channel,
            "published_at": t.published_at,
            "duration_seconds": t.duration_seconds,
            "views": t.views,
            "likes": t.likes,
            "comments": t.comments,
            "virality_score": round(t.virality_score, 2),
            "tags": t.tags,
            "source_query": t.source_query,
        }
        for t in trends
    ]

    drafts_payload = [
        {
            "title": d.title,
            "hook": d.hook,
            "script": d.script,
            "cta": d.cta,
            "hashtags": d.hashtags,
            "tone": d.tone,
            "source_video_id": d.source_video_id,
            "safety_notes": d.safety_notes,
            "slug": slugify(d.title),
            "video_file": d.video_file,
            "video_status": d.video_status,
            "video_operation": d.video_operation,
            "video_error": d.video_error,
        }
        for d in drafts
    ]

    summary_metrics = metrics.get("summary") or {}
    strategy_state, strategy_changes, winning_patterns, killed_patterns, next_test_matrix = update_strategy_from_metrics(
        strategy_state,
        run_id=run_id,
        target_vph=cfg.min_views_per_hour_target,
        avg_vph=float(summary_metrics.get("avg_views_per_hour") or 0.0),
        avg_like_rate=float(summary_metrics.get("avg_like_rate") or 0.0),
        avg_comment_rate=float(summary_metrics.get("avg_comment_rate") or 0.0),
        drafts_payload=drafts_payload,
    )
    strategy_state_path = save_strategy_state(strategy_state)

    write_json(run_dir / "trends.json", {"run_id": run_id, "count": len(trends_payload), "items": trends_payload})
    write_json(run_dir / "drafts.json", {"run_id": run_id, "count": len(drafts_payload), "items": drafts_payload})
    write_json(run_dir / "video_renders.json", video_renders)
    write_json(run_dir / "metrics.json", metrics)
    write_text(run_dir / "feedback_plan.md", feedback_plan)
    write_text(run_dir / "strategy_context.txt", strategy_context + "\n")
    write_json(run_dir / "strategy_top_nuggets.json", {"count": len(top_nuggets), "items": top_nuggets})
    _write_publish_queue(run_dir / "publish_queue.csv", drafts, trends)

    summary = {
        "run_id": run_id,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "execute": execute,
        "used_youtube_api": bool(cfg.youtube_api_key),
        "channel_id": cfg.channel_id,
        "trend_count": len(trends_payload),
        "draft_count": len(drafts_payload),
        "gemini_video_enabled": bool(cfg.gemini_video_enabled),
        "gemini_video_renders": int(video_renders.get("rendered_count") or 0),
        "strategy_state_path": str(strategy_state_path),
        "strategy_changes": strategy_changes,
        "winning_patterns": winning_patterns,
        "killed_patterns": killed_patterns,
        "next_test_matrix": next_test_matrix,
        "deliverables_dir": str(run_dir),
    }
    write_json(run_dir / "run_summary.json", summary)

    latest = DELIVERABLES_DIR / "latest.json"
    write_json(latest, summary)
    post_n8n_event(
        event_type="youtube_shorts_run",
        source="automation.workflows.youtube_shorts",
        payload={
            "run_id": run_id,
            "execute": bool(execute),
            "trend_count": len(trends_payload),
            "draft_count": len(drafts_payload),
            "strategy_changes": strategy_changes,
            "winning_patterns": winning_patterns,
            "killed_patterns": killed_patterns,
            "next_test_matrix": next_test_matrix,
            "deliverables_dir": str(run_dir),
        },
    )

    return str(run_dir)
