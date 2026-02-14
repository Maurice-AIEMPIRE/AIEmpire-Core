from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from automation.utils.files import ensure_dir


DEFAULT_SORA_MODEL = "sora-2"
DEFAULT_SORA_SIZE = "720x1280"


@dataclass
class SoraVideoRequest:
    prompt: str
    output_path: Path
    api_key: str
    model: str = DEFAULT_SORA_MODEL
    size: str = DEFAULT_SORA_SIZE
    seconds: int = 8
    poll_interval_seconds: int = 10
    timeout_seconds: int = 900
    cli_path: str = ""
    no_augment: bool = False


def _seconds_enum(seconds: int) -> str:
    value = int(seconds)
    if value <= 4:
        return "4"
    if value <= 8:
        return "8"
    return "12"


def _resolve_cli_path(cli_path: str) -> Path:
    explicit = (cli_path or "").strip()
    if explicit:
        return Path(explicit).expanduser()
    env_path = (os.environ.get("SORA_CLI") or "").strip()
    if env_path:
        return Path(env_path).expanduser()
    return (Path.home() / ".codex" / "skills" / "sora" / "scripts" / "sora.py").expanduser()


def _extract_video_id(bundle: Dict[str, Any]) -> str:
    create = bundle.get("create") or {}
    final = bundle.get("final") or {}
    for candidate in (final, create):
        if isinstance(candidate, dict):
            video_id = candidate.get("id") or ((candidate.get("data") or {}).get("id") if isinstance(candidate.get("data"), dict) else "")
            if isinstance(video_id, str) and video_id.strip():
                return video_id.strip()
    return ""


def render_video_with_sora(req: SoraVideoRequest) -> Dict[str, Any]:
    if not req.api_key:
        return {
            "ok": False,
            "status": "skipped",
            "error": "OPENAI_API_KEY missing",
            "output_file": str(req.output_path),
            "operation_name": "",
            "video_uri": "",
            "provider": "sora",
        }

    cli = _resolve_cli_path(req.cli_path)
    if not cli.exists():
        return {
            "ok": False,
            "status": "failed",
            "error": f"Sora CLI not found: {cli}",
            "output_file": str(req.output_path),
            "operation_name": "",
            "video_uri": "",
            "provider": "sora",
        }

    ensure_dir(req.output_path.parent)
    json_out = req.output_path.with_suffix(".sora.json")
    seconds = _seconds_enum(req.seconds)
    poll_interval = max(1, int(req.poll_interval_seconds))
    timeout = max(60, int(req.timeout_seconds))

    uv = shutil.which("uv")
    if uv:
        cmd = [
            uv,
            "run",
            "--with",
            "openai",
            "python",
            str(cli),
        ]
    else:
        cmd = [sys.executable, str(cli)]

    cmd.extend(
        [
            "create-and-poll",
            "--model",
            (req.model or DEFAULT_SORA_MODEL).strip() or DEFAULT_SORA_MODEL,
            "--prompt",
            req.prompt,
            "--size",
            (req.size or DEFAULT_SORA_SIZE).strip() or DEFAULT_SORA_SIZE,
            "--seconds",
            seconds,
            "--poll-interval",
            str(poll_interval),
            "--timeout",
            str(timeout),
            "--download",
            "--variant",
            "video",
            "--out",
            str(req.output_path),
            "--json-out",
            str(json_out),
            "--force",
        ]
    )
    if req.no_augment:
        cmd.append("--no-augment")

    env = os.environ.copy()
    env["OPENAI_API_KEY"] = req.api_key.strip()
    env.setdefault("UV_CACHE_DIR", "/tmp/uv-cache")

    completed = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        detail = stderr or stdout or f"exit_{completed.returncode}"
        return {
            "ok": False,
            "status": "failed",
            "error": detail[:900],
            "output_file": str(req.output_path),
            "operation_name": "",
            "video_uri": "",
            "provider": "sora",
        }

    if not req.output_path.exists():
        return {
            "ok": False,
            "status": "failed",
            "error": f"Sora completed but output missing: {req.output_path}",
            "output_file": str(req.output_path),
            "operation_name": "",
            "video_uri": "",
            "provider": "sora",
        }

    video_id = ""
    if json_out.exists():
        try:
            bundle = json.loads(json_out.read_text(encoding="utf-8"))
            video_id = _extract_video_id(bundle)
        except Exception:
            video_id = ""

    return {
        "ok": True,
        "status": "rendered",
        "error": "",
        "output_file": str(req.output_path),
        "operation_name": video_id,
        "video_uri": "",
        "provider": "sora",
    }

