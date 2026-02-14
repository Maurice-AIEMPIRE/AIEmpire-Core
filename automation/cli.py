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
    parser.add_argument("--video-provider", default=None, help="sora|local")
    parser.add_argument("--video-duration-seconds", type=int, default=None)
    parser.add_argument("--video-max-renders", type=int, default=None)
    parser.add_argument("--sora-video-enabled", default=None, help="true|false")
    parser.add_argument("--sora-model", default=None)
    parser.add_argument("--sora-size", default=None)
    parser.add_argument("--sora-poll-interval-seconds", type=int, default=None)
    parser.add_argument("--sora-timeout-seconds", type=int, default=None)
    parser.add_argument("--sora-cli-path", default=None)

    args = parser.parse_args()

    system_cfg = load_system_config()
    youtube_cfg = system_cfg.get("youtube", {})
    revenue_cfg = system_cfg.get("revenue", {})
    sora_cfg = system_cfg.get("sora_video", {})
    video_cfg = system_cfg.get("video_renderer", {})
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
        sora_enabled_raw = args.sora_video_enabled
        if sora_enabled_raw is None:
            sora_enabled = bool(sora_cfg.get("enabled", True))
        else:
            sora_enabled = str(sora_enabled_raw).strip().lower() in {"1", "true", "yes", "on"}
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
            video_provider=args.video_provider or video_cfg.get("provider", "sora"),
            video_duration_seconds=int(args.video_duration_seconds or video_cfg.get("duration_seconds", 8)),
            max_renders_per_run=int(args.video_max_renders or video_cfg.get("max_renders_per_run", 3)),
            sora_video_enabled=sora_enabled,
            sora_model=args.sora_model or sora_cfg.get("model", "sora-2"),
            sora_size=args.sora_size or sora_cfg.get("size", "720x1280"),
            sora_poll_interval_seconds=int(
                args.sora_poll_interval_seconds or sora_cfg.get("poll_interval_seconds", 10)
            ),
            sora_timeout_seconds=int(args.sora_timeout_seconds or sora_cfg.get("timeout_seconds", 900)),
            sora_cli_path=args.sora_cli_path or sora_cfg.get("cli_path", ""),
        )
    elif args.workflow == "shorts_revenue":
        sora_enabled_raw = args.sora_video_enabled
        if sora_enabled_raw is None:
            sora_enabled = bool(sora_cfg.get("enabled", True))
        else:
            sora_enabled = str(sora_enabled_raw).strip().lower() in {"1", "true", "yes", "on"}
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
            video_provider=args.video_provider or video_cfg.get("provider", "sora"),
            video_duration_seconds=int(args.video_duration_seconds or video_cfg.get("duration_seconds", 8)),
            max_renders_per_run=int(args.video_max_renders or video_cfg.get("max_renders_per_run", 3)),
            sora_video_enabled=sora_enabled,
            sora_model=args.sora_model or sora_cfg.get("model", "sora-2"),
            sora_size=args.sora_size or sora_cfg.get("size", "720x1280"),
            sora_poll_interval_seconds=int(
                args.sora_poll_interval_seconds or sora_cfg.get("poll_interval_seconds", 10)
            ),
            sora_timeout_seconds=int(args.sora_timeout_seconds or sora_cfg.get("timeout_seconds", 900)),
            sora_cli_path=args.sora_cli_path or sora_cfg.get("cli_path", ""),
        )
    else:
        run_full(runner, variables, targets)

    runner.write_log()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
