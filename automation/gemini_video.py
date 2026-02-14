from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from automation.utils.files import ensure_dir


DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "veo-3.1-fast-generate-preview"


class GeminiVideoError(RuntimeError):
    pass


@dataclass
class GeminiVideoRequest:
    prompt: str
    output_path: Path
    api_key: str
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    aspect_ratio: str = "9:16"
    resolution: str = "720p"
    duration_seconds: int = 8
    negative_prompt: str = ""
    poll_interval_seconds: int = 10
    max_poll_attempts: int = 90
    request_timeout_seconds: int = 60


def _headers(api_key: str) -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
        "User-Agent": "ai-empire-gemini-video/1.0",
    }


def _http_json(
    method: str,
    url: str,
    *,
    api_key: str,
    payload: Dict[str, Any] | None = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers=_headers(api_key),
        method=method.upper(),
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else str(exc)
        raise GeminiVideoError(f"Gemini API HTTP error: {detail}") from exc
    except urllib.error.URLError as exc:
        raise GeminiVideoError(f"Gemini API connection error: {exc}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GeminiVideoError("Gemini API returned invalid JSON payload") from exc


def _download_to_file(url: str, api_key: str, output_path: Path, timeout: int = 120) -> None:
    ensure_dir(output_path.parent)
    req = urllib.request.Request(url, headers={"x-goog-api-key": api_key, "User-Agent": "ai-empire-gemini-video/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else str(exc)
        raise GeminiVideoError(f"Gemini download HTTP error: {detail}") from exc
    except urllib.error.URLError as exc:
        raise GeminiVideoError(f"Gemini download connection error: {exc}") from exc
    output_path.write_bytes(content)


def _extract_video_uri(payload: Dict[str, Any]) -> str:
    response = payload.get("response") or {}
    generated = (response.get("generateVideoResponse") or {}).get("generatedSamples") or []
    if not isinstance(generated, list) or not generated:
        return ""
    first = generated[0] or {}
    video = first.get("video") or {}
    uri = str(video.get("uri") or "").strip()
    return uri


def render_video_with_gemini(req: GeminiVideoRequest) -> Dict[str, Any]:
    if not req.api_key:
        return {
            "ok": False,
            "status": "skipped",
            "error": "GEMINI_API_KEY missing",
            "output_file": str(req.output_path),
            "operation_name": "",
            "video_uri": "",
        }

    parameters: Dict[str, Any] = {
        "aspectRatio": req.aspect_ratio,
        "resolution": req.resolution,
        "durationSeconds": int(max(4, min(8, int(req.duration_seconds)))),
    }
    negative = req.negative_prompt.strip()
    if negative:
        parameters["negativePrompt"] = negative

    start_url = req.base_url.rstrip("/") + f"/models/{urllib.parse.quote(req.model, safe='')}:predictLongRunning"
    start_payload = {
        "instances": [{"prompt": req.prompt}],
        "parameters": parameters,
    }

    try:
        started = _http_json(
            "POST",
            start_url,
            api_key=req.api_key,
            payload=start_payload,
            timeout=req.request_timeout_seconds,
        )
    except GeminiVideoError as exc:
        return {
            "ok": False,
            "status": "failed",
            "error": str(exc),
            "output_file": str(req.output_path),
            "operation_name": "",
            "video_uri": "",
        }
    operation_name = str(started.get("name") or "").strip()
    if not operation_name:
        return {
            "ok": False,
            "status": "failed",
            "error": "Missing operation name in start response",
            "output_file": str(req.output_path),
            "operation_name": "",
            "video_uri": "",
            "raw": started,
        }

    operation_url = req.base_url.rstrip("/") + "/" + operation_name
    final_payload: Dict[str, Any] = {}
    for _ in range(max(1, req.max_poll_attempts)):
        try:
            polled = _http_json(
                "GET",
                operation_url,
                api_key=req.api_key,
                timeout=req.request_timeout_seconds,
            )
        except GeminiVideoError as exc:
            return {
                "ok": False,
                "status": "failed",
                "error": str(exc),
                "output_file": str(req.output_path),
                "operation_name": operation_name,
                "video_uri": "",
                "raw": final_payload,
            }
        final_payload = polled
        if bool(polled.get("done")):
            break
        time.sleep(max(1, req.poll_interval_seconds))

    if not final_payload or not bool(final_payload.get("done")):
        return {
            "ok": False,
            "status": "timeout",
            "error": "Operation polling timed out",
            "output_file": str(req.output_path),
            "operation_name": operation_name,
            "video_uri": "",
            "raw": final_payload,
        }

    if final_payload.get("error"):
        return {
            "ok": False,
            "status": "failed",
            "error": json.dumps(final_payload.get("error"), ensure_ascii=False),
            "output_file": str(req.output_path),
            "operation_name": operation_name,
            "video_uri": "",
            "raw": final_payload,
        }

    video_uri = _extract_video_uri(final_payload)
    if not video_uri:
        return {
            "ok": False,
            "status": "failed",
            "error": "Missing video uri in operation response",
            "output_file": str(req.output_path),
            "operation_name": operation_name,
            "video_uri": "",
            "raw": final_payload,
        }

    try:
        _download_to_file(video_uri, req.api_key, req.output_path)
    except GeminiVideoError as exc:
        return {
            "ok": False,
            "status": "failed",
            "error": str(exc),
            "output_file": str(req.output_path),
            "operation_name": operation_name,
            "video_uri": video_uri,
            "raw": final_payload,
        }

    return {
        "ok": True,
        "status": "rendered",
        "error": "",
        "output_file": str(req.output_path),
        "operation_name": operation_name,
        "video_uri": video_uri,
        "raw": final_payload,
    }
