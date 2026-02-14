from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

from automation.core.config import load_router_config, load_system_config
from automation.core.router import Router
from automation.core.runner import Runner
from automation.utils.files import timestamp_id
from automation.workflows.content_factory import run_full, run_monetization, run_premium_prompts, run_threads, run_tweets
from automation.workflows.shorts_revenue import run_shorts_revenue
from automation.workflows.youtube_shorts import run_youtube_shorts


def parse_targets(raw: str) -> Dict[str, int]:
    targets: Dict[str, int] = {}
    if not raw:
        return targets
    for part in raw.split(","):
        if not part.strip():
            continue
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        try:
            targets[key] = int(value.strip())
        except ValueError:
            continue
    return targets


def scale_targets(base: Dict[str, int], scale: float) -> Dict[str, int]:
    if scale == 1.0:
        return base
    scaled = {}
    for key, value in base.items():
        scaled[key] = max(1, int(round(value * scale)))
    return scaled


def parse_list(raw: str) -> List[str]:
    if not raw:
        return []
    out: List[str] = []
    for part in raw.split(","):
        value = part.strip()
        if value:
            out.append(value)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Empire Automation CLI")
    parser.add_argument("command", choices=["run"], nargs="?", default="run")
    parser.add_argument(
        "--workflow",
        default="full",
        choices=["full", "threads", "tweets", "prompts", "monetization", "youtube_shorts", "shorts_revenue"],
    )
    parser.add_argument("--execute", action="store_true", help="Execute LLM calls (otherwise dry-run)")
    parser.add_argument("--niche", default=None)
    parser.add_argument("--style", default=None)
    parser.add_argument(
        "--creative-mode",
        default=None,
        help="Creative direction for X posts (e.g. comedy_ai_cartoons_dark_humor_comic)",
    )
    parser.add_argument("--targets", default=None, help="Override targets: threads=50,tweets=300,premium_prompts=400")
    parser.add_argument("--scale", type=float, default=1.0, help="Scale target counts (e.g. 0.2)")
    parser.add_argument("--router-config", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--youtube-channel-id", default=None)
    parser.add_argument("--youtube-region", default=None)
    parser.add_argument("--youtube-language", default=None)
    parser.add_argument("--youtube-lookback-hours", type=int, default=None)
    parser.add_argument("--youtube-drafts", type=int, default=None)
    parser.add_argument("--youtube-min-vph", type=float, default=None, help="Target views-per-hour floor")
    parser.add_argument(
        "--youtube-queries",
        default=None,
        help='Comma-separated queries, e.g. "ai news shorts,motivation shorts,funny shorts"',
    )
    parser.add_argument("--revenue-target-eur", type=float, default=None)
    parser.add_argument("--average-order-value", type=float, default=None)
    parser.add_argument("--profile-click-rate", type=float, default=None)
    parser.add_argument("--landing-conversion-rate", type=float, default=None)
    parser.add_argument("--gemini-video-enabled", default=None, help="true|false")
    parser.add_argument("--gemini-model", default=None)
    parser.add_argument("--gemini-aspect-ratio", default=None)
    parser.add_argument("--gemini-resolution", default=None)
    parser.add_argument("--gemini-duration-seconds", type=int, default=None)
    parser.add_argument("--gemini-negative-prompt", default=None)
    parser.add_argument("--gemini-max-renders", type=int, default=None)
    parser.add_argument("--gemini-poll-interval-seconds", type=int, default=None)
    parser.add_argument("--gemini-max-poll-attempts", type=int, default=None)

    args = parser.parse_args()

    system_cfg = load_system_config()
    youtube_cfg = system_cfg.get("youtube", {})
    revenue_cfg = system_cfg.get("revenue", {})
    gemini_cfg = system_cfg.get("gemini_video", {})
    targets = system_cfg.get("targets", {})
    override_targets = parse_targets(args.targets or "")
    targets.update(override_targets)
    targets = scale_targets(targets, args.scale)

    niche = args.niche or system_cfg.get("niche", "AI agents for content creation")
    style = args.style or system_cfg.get("style", "direct, clear, no emojis")
    creative_mode = args.creative_mode or system_cfg.get(
        "creative_mode",
        "comedy_ai_cartoons_dark_humor_comic",
    )
    outputs = system_cfg.get("outputs", ["threads_50.md", "tweets_300.md", "premium_prompts_400.md"])

    variables = {
        "NISCHE": niche,
        "STIL": style,
        "KREATIV_MODUS": creative_mode,
        "OUTPUTS": ", ".join(outputs),
    }

    router_cfg_path = Path(args.router_config) if args.router_config else None
    if router_cfg_path is None and args.workflow in {"youtube_shorts", "shorts_revenue"}:
        # Default youtube workflow to local-only router to avoid extra costs.
        router_cfg_path = Path("automation") / "config" / "router_local.json"
    router_cfg = load_router_config(router_cfg_path)
    router = Router(router_cfg)

    run_id = args.run_id or timestamp_id()
    log_path = Path("automation") / "runs" / f"run_{run_id}.json"
    runner = Runner(router, execute=args.execute, run_id=run_id, log_path=log_path)

    if args.workflow == "threads":
        run_threads(runner, variables, targets.get("threads", 50))
    elif args.workflow == "tweets":
        run_tweets(runner, variables, targets.get("tweets", 300))
    elif args.workflow == "prompts":
        run_premium_prompts(runner, variables, targets.get("premium_prompts", 400))
    elif args.workflow == "monetization":
        run_monetization(runner, variables)
    elif args.workflow == "youtube_shorts":
        gemini_enabled_raw = args.gemini_video_enabled
        if gemini_enabled_raw is None:
            gemini_enabled = bool(gemini_cfg.get("enabled", True))
        else:
            gemini_enabled = str(gemini_enabled_raw).strip().lower() in {"1", "true", "yes", "on"}
        run_youtube_shorts(
            runner,
            execute=args.execute,
            channel_id=args.youtube_channel_id or youtube_cfg.get("channel_id"),
            region=(args.youtube_region or youtube_cfg.get("region") or "US"),
            language=(args.youtube_language or youtube_cfg.get("language") or "de"),
            lookback_hours=int(args.youtube_lookback_hours or youtube_cfg.get("lookback_hours", 24)),
            drafts_per_run=int(args.youtube_drafts or youtube_cfg.get("drafts_per_run", 6)),
            min_views_per_hour_target=float(args.youtube_min_vph or youtube_cfg.get("min_views_per_hour_target", 300)),
            queries=parse_list(args.youtube_queries or "") or list(youtube_cfg.get("queries", [])),
            gemini_video_enabled=gemini_enabled,
            gemini_model=args.gemini_model or gemini_cfg.get("model", "veo-3.1-fast-generate-preview"),
            gemini_aspect_ratio=args.gemini_aspect_ratio or gemini_cfg.get("aspect_ratio", "9:16"),
            gemini_resolution=args.gemini_resolution or gemini_cfg.get("resolution", "720p"),
            gemini_duration_seconds=int(args.gemini_duration_seconds or gemini_cfg.get("duration_seconds", 8)),
            gemini_negative_prompt=args.gemini_negative_prompt or gemini_cfg.get("negative_prompt", ""),
            gemini_max_renders_per_run=int(args.gemini_max_renders or gemini_cfg.get("max_renders_per_run", 3)),
            gemini_poll_interval_seconds=int(
                args.gemini_poll_interval_seconds or gemini_cfg.get("poll_interval_seconds", 10)
            ),
            gemini_max_poll_attempts=int(args.gemini_max_poll_attempts or gemini_cfg.get("max_poll_attempts", 90)),
        )
    elif args.workflow == "shorts_revenue":
        gemini_enabled_raw = args.gemini_video_enabled
        if gemini_enabled_raw is None:
            gemini_enabled = bool(gemini_cfg.get("enabled", True))
        else:
            gemini_enabled = str(gemini_enabled_raw).strip().lower() in {"1", "true", "yes", "on"}
        run_shorts_revenue(
            runner,
            execute=args.execute,
            channel_id=args.youtube_channel_id or youtube_cfg.get("channel_id"),
            region=(args.youtube_region or youtube_cfg.get("region") or "US"),
            language=(args.youtube_language or youtube_cfg.get("language") or "de"),
            lookback_hours=int(args.youtube_lookback_hours or youtube_cfg.get("lookback_hours", 24)),
            drafts_per_run=int(args.youtube_drafts or youtube_cfg.get("drafts_per_run", 6)),
            min_views_per_hour_target=float(args.youtube_min_vph or youtube_cfg.get("min_views_per_hour_target", 300)),
            queries=parse_list(args.youtube_queries or "") or list(youtube_cfg.get("queries", [])),
            revenue_target_eur=float(args.revenue_target_eur or revenue_cfg.get("target_eur_24h", 500)),
            average_order_value=float(args.average_order_value or revenue_cfg.get("average_order_value", 27)),
            profile_click_rate=float(args.profile_click_rate or revenue_cfg.get("profile_click_rate", 0.01)),
            landing_conversion_rate=float(args.landing_conversion_rate or revenue_cfg.get("landing_conversion_rate", 0.02)),
            gemini_video_enabled=gemini_enabled,
            gemini_model=args.gemini_model or gemini_cfg.get("model", "veo-3.1-fast-generate-preview"),
            gemini_aspect_ratio=args.gemini_aspect_ratio or gemini_cfg.get("aspect_ratio", "9:16"),
            gemini_resolution=args.gemini_resolution or gemini_cfg.get("resolution", "720p"),
            gemini_duration_seconds=int(args.gemini_duration_seconds or gemini_cfg.get("duration_seconds", 8)),
            gemini_negative_prompt=args.gemini_negative_prompt or gemini_cfg.get("negative_prompt", ""),
            gemini_max_renders_per_run=int(args.gemini_max_renders or gemini_cfg.get("max_renders_per_run", 3)),
            gemini_poll_interval_seconds=int(
                args.gemini_poll_interval_seconds or gemini_cfg.get("poll_interval_seconds", 10)
            ),
            gemini_max_poll_attempts=int(args.gemini_max_poll_attempts or gemini_cfg.get("max_poll_attempts", 90)),
        )
    else:
        run_full(runner, variables, targets)

    runner.write_log()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
