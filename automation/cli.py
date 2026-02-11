from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

from automation.core.config import load_router_config, load_system_config
from automation.core.router import Router
from automation.core.runner import Runner
from automation.utils.files import timestamp_id
from automation.workflows.content_factory import run_full, run_monetization, run_premium_prompts, run_threads, run_tweets


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


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Empire Automation CLI")
    parser.add_argument("command", choices=["run"], nargs="?", default="run")
    parser.add_argument("--workflow", default="full", choices=["full", "threads", "tweets", "prompts", "monetization"])
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

    args = parser.parse_args()

    system_cfg = load_system_config()
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
    else:
        run_full(runner, variables, targets)

    runner.write_log()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
