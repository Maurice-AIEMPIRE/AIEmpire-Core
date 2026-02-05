#!/usr/bin/env python3
"""
Claude limit watcher.

Modes:
  web: poll the Claude web UI for usage-limit text.
  countdown: wait for one or more timers and notify when they expire.
  api: poll Anthropic API and infer rate-limit state from responses.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Iterable, List, Optional, Sequence


DEFAULT_BLOCK_PHRASES = [
    r"limit\s+reached",
    r"usage\s+limit",
    r"rate\s+limit",
    r"nutzungslimit",
    r"limit\s+erreicht",
]

LANGUAGE_PHRASES = {
    "en": [
        r"limit\s+reached",
        r"usage\s+limit",
        r"rate\s+limit",
        r"you've\s+reached",
        r"usage\s+cap",
    ],
    "de": [
        r"nutzungslimit",
        r"limit\s+erreicht",
        r"limit\s+ausgesch",
        r"kontingent",
    ],
}

PERCENT_RE = re.compile(r"(\d{1,3})\s*%\s*(?:verwendet|used)", re.IGNORECASE)


def log(msg: str) -> None:
    ts = dt.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def notify(title: str, message: str, enable: bool = True) -> None:
    if not enable:
        return
    if sys.platform == "darwin":
        subprocess.run(
            [
                "osascript",
                "-e",
                f'display notification "{message}" with title "{title}"',
            ],
            check=False,
        )
    else:
        log(f"{title}: {message}")


def run_on_ready(cmd: Optional[str]) -> None:
    if not cmd:
        return
    subprocess.Popen(cmd, shell=True)


def extract_percents(text: str, percent_re: re.Pattern[str]) -> List[int]:
    values = []
    for match in percent_re.findall(text):
        try:
            values.append(int(match))
        except ValueError:
            continue
    return values


def is_blocked(text: str, threshold: int, phrases: Sequence[str], percent_re: re.Pattern[str]) -> bool:
    for phrase in phrases:
        if re.search(phrase, text, re.IGNORECASE):
            return True
    percents = extract_percents(text, percent_re)
    if percents and max(percents) >= threshold:
        return True
    return False


def parse_duration(value: str) -> int:
    raw = value.strip().lower()
    if raw.isdigit():
        return int(raw) * 60
    pattern = re.compile(r"^\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?\s*$")
    match = pattern.match(raw)
    if not match:
        raise ValueError(f"Invalid duration: {value}")
    hours = int(match.group(1) or 0)
    mins = int(match.group(2) or 0)
    secs = int(match.group(3) or 0)
    total = hours * 3600 + mins * 60 + secs
    if total <= 0:
        raise ValueError(f"Duration must be positive: {value}")
    return total


def watch_countdown(args: argparse.Namespace) -> int:
    if not args.reset_in:
        raise SystemExit("countdown mode requires --reset-in at least once")
    timers = [parse_duration(v) for v in args.reset_in]
    target = dt.datetime.now() + dt.timedelta(seconds=max(timers))
    log(f"Countdown target: {target.strftime('%Y-%m-%d %H:%M:%S')}")
    while True:
        remaining = (target - dt.datetime.now()).total_seconds()
        if remaining <= 0:
            notify("Claude Limits", "Limits sollten jetzt zurueckgesetzt sein.", args.notify)
            run_on_ready(args.on_ready)
            return 0
        if int(remaining) % 60 == 0:
            mins = int(remaining // 60)
            log(f"Noch {mins} Minuten bis zum Reset.")
        time.sleep(1)


def load_phrases(config_path: Optional[str], extra_phrases: Iterable[str], language: str) -> List[str]:
    phrases: List[str] = []
    if language == "auto":
        for items in LANGUAGE_PHRASES.values():
            phrases.extend(items)
    elif language in LANGUAGE_PHRASES:
        phrases.extend(LANGUAGE_PHRASES[language])
    else:
        phrases.extend(DEFAULT_BLOCK_PHRASES)

    if config_path:
        config_file = os.path.expanduser(config_path)
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                if isinstance(data, dict):
                    extra = data.get("phrases")
                    if isinstance(extra, list):
                        phrases.extend(str(item) for item in extra)
            except Exception as exc:
                log(f"Config konnte nicht geladen werden: {exc}")

    for phrase in extra_phrases:
        phrases.append(phrase)

    if not phrases:
        phrases = DEFAULT_BLOCK_PHRASES[:]
    return phrases


def build_percent_re(pattern: Optional[str]) -> re.Pattern[str]:
    if not pattern:
        return PERCENT_RE
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        log(f"Ungueltiger Regex '{pattern}': {exc}. Fallback auf Standard.")
        return PERCENT_RE


def watch_web(args: argparse.Namespace) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        log("Playwright fehlt. Installiere es mit:")
        log("python3 -m pip install playwright")
        log("python3 -m playwright install chromium")
        return 2

    profile_dir = os.path.expanduser(args.profile)
    os.makedirs(profile_dir, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            profile_dir,
            headless=args.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.new_page()
        page.goto(args.url, wait_until="domcontentloaded")
        if args.pause_for_login:
            log("Bitte einloggen und die Limits-Seite offen lassen, dann Enter druecken.")
            input()

        phrases = load_phrases(args.config, args.phrase or [], args.language)
        percent_re = build_percent_re(args.percent_regex)
        seen_blocked = False
        last_state: Optional[bool] = None

        while True:
            try:
                content = page.content()
            except Exception as exc:
                log(f"Fehler beim Lesen der Seite: {exc}")
                time.sleep(args.interval)
                continue

            blocked = is_blocked(content, args.threshold, phrases, percent_re)
            if blocked:
                seen_blocked = True

            if last_state is None or blocked != last_state:
                state_label = "BLOCKIERT" if blocked else "FREI"
                log(f"Statuswechsel: {state_label}")
                last_state = blocked

            if not blocked and (seen_blocked or not args.require_blocked_first):
                notify("Claude Limits", "Limits sind wieder frei. Claude kann loslegen.", args.notify)
                run_on_ready(args.on_ready)
                if not args.continue_watch:
                    return 0
                seen_blocked = False

            time.sleep(args.interval)


def api_request_blocked(
    base_url: str,
    api_key: str,
    model: str,
    max_tokens: int,
    prompt: str,
    timeout: int,
) -> Optional[bool]:
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            if status == 200:
                return False
            if status in (429, 503, 529):
                return True
            return None
    except urllib.error.HTTPError as exc:
        if exc.code in (429, 503, 529):
            return True
        if exc.code in (401, 403):
            log("API Key oder Rechteproblem. Bitte Key pruefen.")
            return None
        log(f"HTTP Fehler: {exc.code}")
        return None
    except Exception as exc:
        log(f"API Anfrage fehlgeschlagen: {exc}")
        return None


def watch_api(args: argparse.Namespace) -> int:
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    model = args.model or os.environ.get("ANTHROPIC_MODEL") or os.environ.get("CLAUDE_MODEL")
    if not api_key:
        log("Kein API Key gefunden. Setze ANTHROPIC_API_KEY oder nutze --api-key.")
        return 2
    if not model:
        log("Kein Model angegeben. Nutze --model oder setze ANTHROPIC_MODEL.")
        return 2

    seen_blocked = False
    last_state: Optional[bool] = None

    while True:
        blocked = api_request_blocked(
            base_url=args.base_url,
            api_key=api_key,
            model=model,
            max_tokens=args.max_tokens,
            prompt=args.prompt,
            timeout=args.timeout,
        )

        if blocked is None:
            time.sleep(args.interval)
            continue

        if blocked:
            seen_blocked = True

        if last_state is None or blocked != last_state:
            state_label = "BLOCKIERT" if blocked else "FREI"
            log(f"Statuswechsel: {state_label}")
            last_state = blocked

        if not blocked and (seen_blocked or not args.require_blocked_first):
            notify("Claude Limits", "API Limits sind wieder frei. Claude kann loslegen.", args.notify)
            run_on_ready(args.on_ready)
            if not args.continue_watch:
                return 0
            seen_blocked = False

        time.sleep(args.interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Claude limit watcher")
    sub = parser.add_subparsers(dest="mode", required=True)

    web = sub.add_parser("web", help="Monitor Claude web UI")
    web.add_argument("--url", default="https://claude.ai", help="Claude URL")
    web.add_argument("--profile", default="~/.claude_limit_watch_profile", help="Browser profile dir")
    web.add_argument("--interval", type=int, default=30, help="Poll interval in seconds")
    web.add_argument("--threshold", type=int, default=100, help="Percent threshold for blocked")
    web.add_argument("--percent-regex", help="Custom regex for percent detection")
    web.add_argument("--language", default="auto", help="Phrase set: auto, de, en")
    web.add_argument("--phrase", action="append", help="Extra block phrase (regex)")
    web.add_argument("--config", help="JSON config with phrases list")
    web.add_argument("--headless", action="store_true", help="Run browser headless")
    web.add_argument("--pause-for-login", action="store_true", help="Wait for manual login")
    web.add_argument("--no-require-blocked-first", dest="require_blocked_first", action="store_false", default=True)
    web.add_argument("--continue-watch", action="store_true", help="Keep watching after ready")
    web.add_argument("--no-notify", dest="notify", action="store_false", default=True)
    web.add_argument("--on-ready", help="Shell command to run when ready")

    countdown = sub.add_parser("countdown", help="Timer-based monitoring")
    countdown.add_argument("--reset-in", action="append", help="Durations like 2h32m or 90m", required=True)
    countdown.add_argument("--no-notify", dest="notify", action="store_false", default=True)
    countdown.add_argument("--on-ready", help="Shell command to run when ready")

    api = sub.add_parser("api", help="Monitor Anthropic API limits")
    api.add_argument("--base-url", default="https://api.anthropic.com/v1/messages")
    api.add_argument("--api-key", help="Anthropic API key (or env ANTHROPIC_API_KEY)")
    api.add_argument("--model", help="Model name (or env ANTHROPIC_MODEL)")
    api.add_argument("--max-tokens", type=int, default=1, help="Max tokens for probe request")
    api.add_argument("--prompt", default="ping", help="Probe prompt")
    api.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    api.add_argument("--interval", type=int, default=60, help="Poll interval in seconds")
    api.add_argument("--no-require-blocked-first", dest="require_blocked_first", action="store_false", default=True)
    api.add_argument("--continue-watch", action="store_true", help="Keep watching after ready")
    api.add_argument("--no-notify", dest="notify", action="store_false", default=True)
    api.add_argument("--on-ready", help="Shell command to run when ready")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "countdown":
        return watch_countdown(args)
    if args.mode == "web":
        return watch_web(args)
    if args.mode == "api":
        return watch_api(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
