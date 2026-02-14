from __future__ import annotations

import csv
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation.core.runner import Runner
from automation.n8n_events import post_n8n_event
from automation.tiktok import DEFAULT_VIDEO_FIELDS, list_videos
from automation.utils.files import ensure_dir, env_or_default, slugify, timestamp_id, write_json, write_text
from automation.workflows.shorts_strategy_state import (
    build_strategy_prompt_context,
    load_strategy_state,
    load_top_nuggets,
    save_strategy_state,
    update_strategy_from_metrics,
)
from automation.workflows.youtube_shorts import (
    WorkflowConfig,
    build_feedback_plan,
    collect_channel_shorts_metrics,
    fetch_trends_from_youtube,
    generate_shorts_drafts,
    render_drafts_with_gemini,
)


ROOT = Path(__file__).resolve().parents[2]
DELIVERABLES_DIR = ROOT / "content_factory" / "deliverables" / "shorts_revenue"


@dataclass
class RevenueAssumptions:
    target_eur_24h: float = 500.0
    average_order_value: float = 27.0
    profile_click_rate: float = 0.01
    landing_conversion_rate: float = 0.02


def _safe_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
        if parsed <= 0:
            return default
        return parsed
    except (TypeError, ValueError):
        return default


def _collect_tiktok_metrics() -> Dict[str, Any]:
    token = env_or_default("TIKTOK_ACCESS_TOKEN", "") or ""
    if not token:
        return {
            "available": False,
            "reason": "TIKTOK_ACCESS_TOKEN missing",
            "summary": {
                "count": 0,
                "avg_views": 0,
                "avg_like_rate": 0,
                "avg_comment_rate": 0,
            },
            "videos": [],
        }

    try:
        payload = list_videos(
            access_token=token,
            fields=DEFAULT_VIDEO_FIELDS,
            cursor=None,
            max_count=20,
        )
    except Exception as exc:  # pragma: no cover
        return {
            "available": False,
            "reason": f"TikTok API error: {exc}",
            "summary": {
                "count": 0,
                "avg_views": 0,
                "avg_like_rate": 0,
                "avg_comment_rate": 0,
            },
            "videos": [],
        }

    videos_raw = ((payload.get("data") or {}).get("videos") or []) if isinstance(payload, dict) else []

    videos: List[Dict[str, Any]] = []
    for item in videos_raw:
        if not isinstance(item, dict):
            continue
        views = int(item.get("view_count") or 0)
        likes = int(item.get("like_count") or 0)
        comments = int(item.get("comment_count") or 0)
        duration = int(item.get("duration") or 0)
        videos.append(
            {
                "id": str(item.get("id") or ""),
                "title": str(item.get("title") or ""),
                "duration": duration,
                "views": views,
                "likes": likes,
                "comments": comments,
                "share_url": str(item.get("share_url") or ""),
                "like_rate": round((likes / views) if views else 0.0, 4),
                "comment_rate": round((comments / views) if views else 0.0, 4),
            }
        )

    count = len(videos)
    if count == 0:
        return {
            "available": True,
            "reason": "No videos found",
            "summary": {
                "count": 0,
                "avg_views": 0,
                "avg_like_rate": 0,
                "avg_comment_rate": 0,
            },
            "videos": [],
        }

    avg_views = sum(v["views"] for v in videos) / count
    avg_like_rate = sum(v["like_rate"] for v in videos) / count
    avg_comment_rate = sum(v["comment_rate"] for v in videos) / count
    videos.sort(key=lambda x: x["views"], reverse=True)

    return {
        "available": True,
        "reason": "ok",
        "summary": {
            "count": count,
            "avg_views": round(avg_views, 2),
            "avg_like_rate": round(avg_like_rate, 4),
            "avg_comment_rate": round(avg_comment_rate, 4),
        },
        "winners": videos[:3],
        "laggards": videos[-3:],
        "videos": videos,
    }


def _render_offer_description(script: str, cta: str, hashtags: List[str]) -> str:
    summary = script.strip().split("\n")[0][:220]
    return f"{summary}\n\n{cta}\n\n{' '.join(hashtags[:6])}".strip()


def _sanitize_unverifiable_income_claims(text: str) -> str:
    raw = str(text or "")
    patterns = [
        r"garantiert[^.!\n]*",
        r"sicher reich[^.!\n]*",
        r"nie wieder broke[^.!\n]*",
        r"\b\d+\s*€\s*pro\s*tag\b",
        r"\b\d+\s*€\s*in\s*24h\b",
    ]
    sanitized = raw
    for pattern in patterns:
        sanitized = re.sub(pattern, "realistische Ergebnisse variieren je nach Umsetzung", sanitized, flags=re.IGNORECASE)
    return sanitized


def _apply_product_first_policy(drafts: List["ShortsDraft"]) -> List["ShortsDraft"]:
    checkout_url = (
        str(env_or_default("STRIPE_PROMPT_VAULT_URL", "") or "").strip()
        or str(env_or_default("PROMPT_VAULT_URL", "") or "").strip()
    )
    if checkout_url:
        product_cta = f"Direkt zum AI Prompt Vault: {checkout_url}"
    else:
        product_cta = "Link im Profil: AI Prompt Vault. Schreib 'VAULT' fuer den direkten Zugang."
    community_cta = "Kommentiere mit EINEM Wort: JA oder NEIN?"
    if not drafts:
        return drafts
    product_slots = max(1, int(round(len(drafts) * 0.7)))
    for idx, draft in enumerate(drafts):
        draft.title = _sanitize_unverifiable_income_claims(draft.title)
        draft.hook = _sanitize_unverifiable_income_claims(draft.hook)
        draft.script = _sanitize_unverifiable_income_claims(draft.script)
        if idx < product_slots:
            draft.cta = product_cta
        else:
            draft.cta = community_cta
    return drafts


def _write_youtube_queue(path: Path, drafts: List[Dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "slot",
                "title",
                "description",
                "hashtags",
                "duration_target_sec",
                "offer_cta",
                "video_file",
                "video_status",
                "video_operation",
                "video_error",
                "status",
            ],
        )
        writer.writeheader()
        for idx, draft in enumerate(drafts, start=1):
            writer.writerow(
                {
                    "slot": idx,
                    "title": draft["title"],
                    "description": draft["description"],
                    "hashtags": " ".join(draft["hashtags"]),
                    "duration_target_sec": 35,
                    "offer_cta": draft["cta"],
                    "video_file": draft.get("video_file", ""),
                    "video_status": draft.get("video_status", ""),
                    "video_operation": draft.get("video_operation", ""),
                    "video_error": draft.get("video_error", ""),
                    "status": "ready",
                }
            )


def _write_tiktok_queue(path: Path, drafts: List[Dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "slot",
                "caption",
                "script",
                "hashtags",
                "duration_target_sec",
                "creator_rewards_eligible",
                "offer_cta",
                "video_file",
                "video_status",
                "video_operation",
                "video_error",
                "status",
            ],
        )
        writer.writeheader()
        for idx, draft in enumerate(drafts, start=1):
            short_caption = draft["title"][:120]
            # Add one >=60s variant because TikTok rewards require >=1 minute.
            writer.writerow(
                {
                    "slot": f"{idx}a",
                    "caption": short_caption,
                    "script": draft["script"],
                    "hashtags": " ".join(draft["hashtags"]),
                    "duration_target_sec": 35,
                    "creator_rewards_eligible": "no",
                    "offer_cta": draft["cta"],
                    "video_file": draft.get("video_file", ""),
                    "video_status": draft.get("video_status", ""),
                    "video_operation": draft.get("video_operation", ""),
                    "video_error": draft.get("video_error", ""),
                    "status": "ready",
                }
            )
            writer.writerow(
                {
                    "slot": f"{idx}b",
                    "caption": short_caption,
                    "script": draft["script"] + "\n\nErweitere das Beispiel mit 2 Zusatzpunkten und einem Mini-Case.",
                    "hashtags": " ".join(draft["hashtags"]),
                    "duration_target_sec": 65,
                    "creator_rewards_eligible": "yes",
                    "offer_cta": draft["cta"],
                    "video_file": draft.get("video_file", ""),
                    "video_status": draft.get("video_status", ""),
                    "video_operation": draft.get("video_operation", ""),
                    "video_error": draft.get("video_error", ""),
                    "status": "ready",
                }
            )


def _money_model(
    assumptions: RevenueAssumptions,
    youtube_metrics: Dict[str, Any],
    tiktok_metrics: Dict[str, Any],
    drafts_count: int,
) -> Dict[str, Any]:
    avg_yt_views = float((youtube_metrics.get("summary") or {}).get("avg_views") or 0.0)
    avg_tt_views = float((tiktok_metrics.get("summary") or {}).get("avg_views") or 0.0)

    projected_views_24h = max(1000.0, (avg_yt_views + avg_tt_views) * max(drafts_count, 1))
    projected_clicks = projected_views_24h * assumptions.profile_click_rate
    projected_sales = projected_clicks * assumptions.landing_conversion_rate
    projected_revenue = projected_sales * assumptions.average_order_value

    needed_sales = assumptions.target_eur_24h / assumptions.average_order_value
    needed_clicks = needed_sales / assumptions.landing_conversion_rate
    needed_views = needed_clicks / assumptions.profile_click_rate

    return {
        "assumptions": {
            "target_eur_24h": assumptions.target_eur_24h,
            "average_order_value": assumptions.average_order_value,
            "profile_click_rate": assumptions.profile_click_rate,
            "landing_conversion_rate": assumptions.landing_conversion_rate,
        },
        "projection": {
            "projected_views_24h": round(projected_views_24h, 2),
            "projected_clicks": round(projected_clicks, 2),
            "projected_sales": round(projected_sales, 2),
            "projected_revenue_eur": round(projected_revenue, 2),
        },
        "required_for_target": {
            "needed_sales": round(needed_sales, 2),
            "needed_clicks": round(needed_clicks, 2),
            "needed_views": round(needed_views, 2),
        },
    }


def _load_real_revenue_snapshot() -> Dict[str, Any]:
    latest = ROOT / "content_factory" / "deliverables" / "revenue" / "stripe" / "latest.json"
    if not latest.exists():
        return {"available": False}
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"available": False}
    run_path = Path(str(payload.get("path") or ""))
    if run_path.exists():
        try:
            snapshot = json.loads(run_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"available": False}
        totals = snapshot.get("totals") if isinstance(snapshot, dict) else {}
        return {
            "available": True,
            "captured_at": snapshot.get("captured_at"),
            "totals": totals if isinstance(totals, dict) else {},
        }
    return {
        "available": True,
        "captured_at": payload.get("captured_at"),
        "totals": payload.get("totals") if isinstance(payload.get("totals"), dict) else {},
    }


def _write_execution_brief(
    path: Path,
    *,
    money_model: Dict[str, Any],
    real_revenue: Dict[str, Any],
    youtube_feedback: str,
    tiktok_metrics: Dict[str, Any],
) -> None:
    proj = money_model.get("projection") or {}
    req = money_model.get("required_for_target") or {}
    real_totals = (real_revenue.get("totals") if isinstance(real_revenue, dict) else {}) or {}

    lines = [
        "# Shorts Revenue Execution Brief",
        "",
        "## 24h Revenue Reality",
        f"- REAL Stripe net (lookback): EUR {real_totals.get('net_eur', 0)}",
        f"- REAL Stripe gross (lookback): EUR {real_totals.get('gross_eur', 0)}",
        f"- REAL Stripe successful payments: {real_totals.get('charges_paid', 0)}",
        f"- Projected revenue (current metrics): EUR {proj.get('projected_revenue_eur', 0)}",
        f"- Required views for target: {req.get('needed_views', 0)}",
        "- Priority: direct product conversion over ad revenue in first 24h.",
        "",
        "## Highest-value lanes",
        "- AI Automation Templates (high intent, direct purchase path)",
        "- Business Prompt Bundles (quick AOV, immediate fulfillment)",
        "- Technical Fix/How-to mini-lessons leading to paid guides",
        "",
        "## YouTube feedback loop",
        youtube_feedback,
        "",
        "## TikTok feedback summary",
        f"- API available: {tiktok_metrics.get('available')}",
        f"- Reason: {tiktok_metrics.get('reason')}",
        f"- Avg views: {(tiktok_metrics.get('summary') or {}).get('avg_views', 0)}",
        f"- Avg like rate: {(tiktok_metrics.get('summary') or {}).get('avg_like_rate', 0)}",
        f"- Avg comment rate: {(tiktok_metrics.get('summary') or {}).get('avg_comment_rate', 0)}",
        "",
        "## Immediate optimization rules",
        "- Keep 2-sec hook change every edit beat.",
        "- One clear offer CTA per post (single product, no mixed CTA).",
        "- Kill formats after 3 poor posts in a row, duplicate top 20% formats.",
        "- Post short + >=60s variant on TikTok for growth + rewards eligibility.",
    ]

    write_text(path, "\n".join(lines).strip() + "\n")


def run_shorts_revenue(
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
    revenue_target_eur: float = 500.0,
    average_order_value: float = 27.0,
    profile_click_rate: float = 0.01,
    landing_conversion_rate: float = 0.02,
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
    shorts_drafts = generate_shorts_drafts(
        runner,
        cfg,
        trends,
        strategy_context=strategy_context,
        strategy_state=strategy_state,
    )
    shorts_drafts = _apply_product_first_policy(shorts_drafts)
    video_renders = render_drafts_with_gemini(cfg, shorts_drafts, trends, run_dir)
    yt_metrics = collect_channel_shorts_metrics(cfg)
    tiktok_metrics = _collect_tiktok_metrics()

    drafts_payload: List[Dict[str, Any]] = []
    for d in shorts_drafts:
        drafts_payload.append(
            {
                "title": d.title,
                "hook": d.hook,
                "script": d.script,
                "cta": d.cta,
                "hashtags": d.hashtags,
                "tone": d.tone,
                "source_video_id": d.source_video_id,
                "slug": slugify(d.title),
                "description": _render_offer_description(d.script, d.cta, d.hashtags),
                "video_file": d.video_file,
                "video_status": d.video_status,
                "video_operation": d.video_operation,
                "video_error": d.video_error,
            }
        )

    yt_summary = yt_metrics.get("summary") or {}
    strategy_state, strategy_changes, winning_patterns, killed_patterns, next_test_matrix = update_strategy_from_metrics(
        strategy_state,
        run_id=run_id,
        target_vph=cfg.min_views_per_hour_target,
        avg_vph=float(yt_summary.get("avg_views_per_hour") or 0.0),
        avg_like_rate=float(yt_summary.get("avg_like_rate") or 0.0),
        avg_comment_rate=float(yt_summary.get("avg_comment_rate") or 0.0),
        drafts_payload=drafts_payload,
    )
    strategy_state_path = save_strategy_state(strategy_state)

    youtube_feedback = build_feedback_plan(cfg, yt_metrics, shorts_drafts)

    assumptions = RevenueAssumptions(
        target_eur_24h=_safe_float(revenue_target_eur, 500.0),
        average_order_value=_safe_float(average_order_value, 27.0),
        profile_click_rate=_safe_float(profile_click_rate, 0.01),
        landing_conversion_rate=_safe_float(landing_conversion_rate, 0.02),
    )
    money_model = _money_model(assumptions, yt_metrics, tiktok_metrics, len(drafts_payload))
    real_revenue = _load_real_revenue_snapshot()

    _write_youtube_queue(run_dir / "youtube_publish_queue.csv", drafts_payload)
    _write_tiktok_queue(run_dir / "tiktok_publish_queue.csv", drafts_payload)

    write_json(
        run_dir / "trends.json",
        {
            "count": len(trends),
            "items": [
                {
                    "video_id": t.video_id,
                    "title": t.title,
                    "channel": t.channel,
                    "views": t.views,
                    "likes": t.likes,
                    "comments": t.comments,
                    "virality_score": round(t.virality_score, 2),
                }
                for t in trends
            ],
        },
    )
    write_json(run_dir / "drafts.json", {"count": len(drafts_payload), "items": drafts_payload})
    write_json(run_dir / "video_renders.json", video_renders)
    write_json(run_dir / "youtube_metrics.json", yt_metrics)
    write_json(run_dir / "tiktok_metrics.json", tiktok_metrics)
    write_json(run_dir / "money_model.json", money_model)
    write_json(run_dir / "real_revenue_snapshot.json", real_revenue)
    write_text(run_dir / "youtube_feedback_plan.md", youtube_feedback)
    write_text(run_dir / "strategy_context.txt", strategy_context + "\n")
    write_json(run_dir / "strategy_top_nuggets.json", {"count": len(top_nuggets), "items": top_nuggets})

    _write_execution_brief(
        run_dir / "execution_brief.md",
        money_model=money_model,
        real_revenue=real_revenue,
        youtube_feedback=youtube_feedback,
        tiktok_metrics=tiktok_metrics,
    )

    summary = {
        "run_id": run_id,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "execute": execute,
        "deliverables_dir": str(run_dir),
        "draft_count": len(drafts_payload),
        "used_youtube_api": bool(cfg.youtube_api_key),
        "used_tiktok_api": bool(tiktok_metrics.get("available")),
        "gemini_video_enabled": bool(cfg.gemini_video_enabled),
        "gemini_video_renders": int(video_renders.get("rendered_count") or 0),
        "money_projection_eur_24h": (money_model.get("projection") or {}).get("projected_revenue_eur", 0),
        "real_revenue_eur": ((real_revenue.get("totals") or {}).get("net_eur") if isinstance(real_revenue, dict) else 0),
        "strategy_state_path": str(strategy_state_path),
        "strategy_changes": strategy_changes,
        "winning_patterns": winning_patterns,
        "killed_patterns": killed_patterns,
        "next_test_matrix": next_test_matrix,
    }
    write_json(run_dir / "run_summary.json", summary)
    write_json(DELIVERABLES_DIR / "latest.json", summary)
    post_n8n_event(
        event_type="shorts_revenue_run",
        source="automation.workflows.shorts_revenue",
        payload={
            "run_id": run_id,
            "execute": bool(execute),
            "draft_count": len(drafts_payload),
            "money_projection_eur_24h": summary.get("money_projection_eur_24h"),
            "real_revenue_eur": summary.get("real_revenue_eur"),
            "strategy_changes": strategy_changes,
            "winning_patterns": winning_patterns,
            "killed_patterns": killed_patterns,
            "next_test_matrix": next_test_matrix,
            "deliverables_dir": str(run_dir),
        },
    )
    return str(run_dir)
