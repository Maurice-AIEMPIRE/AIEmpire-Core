from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation.utils.files import ensure_dir


def _clean_text(text: str, limit: int = 500) -> str:
    raw = " ".join(str(text or "").split())
    if len(raw) <= limit:
        return raw
    return raw[: limit - 3].rstrip() + "..."


def _require_module(name: str) -> Optional[str]:
    try:
        __import__(name)
        return None
    except Exception as exc:
        return f"missing_python_dependency:{name}:{exc}"


def _edge_tts_generate(audio_path: Path, text: str, voice: str) -> Dict[str, Any]:
    edge_tts_bin = shutil.which("edge-tts")
    if not edge_tts_bin:
        return {
            "ok": False,
            "error": "missing_binary:edge-tts",
        }

    cmd = [
        edge_tts_bin,
        "--voice",
        voice,
        "--text",
        text,
        "--write-media",
        str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not audio_path.exists():
        detail = (result.stderr or result.stdout or "edge_tts_failed").strip()[:900]
        return {"ok": False, "error": detail}
    return {"ok": True, "error": ""}


def _fetch_pexels_video_link(api_key: str, query: str) -> Dict[str, Any]:
    dep_err = _require_module("requests")
    if dep_err:
        return {"ok": False, "error": dep_err, "link": ""}

    import requests  # type: ignore

    if not api_key:
        return {"ok": False, "error": "missing_env:PEXELS_API_KEY", "link": ""}

    url = "https://api.pexels.com/videos/search"
    params = {
        "query": query or "ai technology abstract",
        "orientation": "portrait",
        "size": "medium",
        "per_page": 15,
    }
    headers = {"Authorization": api_key}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
    except Exception as exc:
        return {"ok": False, "error": f"pexels_request_failed:{exc}", "link": ""}

    if resp.status_code != 200:
        return {"ok": False, "error": f"pexels_http_{resp.status_code}:{resp.text[:300]}", "link": ""}

    payload = resp.json() if resp.content else {}
    videos = payload.get("videos") if isinstance(payload, dict) else []
    if not isinstance(videos, list) or not videos:
        return {"ok": False, "error": "pexels_no_videos", "link": ""}

    candidates: List[Dict[str, Any]] = []
    for v in videos:
        if not isinstance(v, dict):
            continue
        files = v.get("video_files")
        if not isinstance(files, list):
            continue
        for f in files:
            if not isinstance(f, dict):
                continue
            width = int(f.get("width") or 0)
            height = int(f.get("height") or 0)
            link = str(f.get("link") or "").strip()
            if not link:
                continue
            portrait = height > width
            score = 0
            if portrait:
                score += 100
            score += min(height, 1920) / 100.0
            candidates.append(
                {
                    "link": link,
                    "width": width,
                    "height": height,
                    "score": score,
                }
            )

    if not candidates:
        return {"ok": False, "error": "pexels_no_files", "link": ""}

    candidates.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
    best = candidates[0]
    return {"ok": True, "error": "", "link": str(best.get("link") or "")}


def _download_file(url: str, output_path: Path) -> Dict[str, Any]:
    dep_err = _require_module("requests")
    if dep_err:
        return {"ok": False, "error": dep_err}

    import requests  # type: ignore

    try:
        with requests.get(url, stream=True, timeout=60) as resp:
            if resp.status_code != 200:
                return {"ok": False, "error": f"download_http_{resp.status_code}"}
            with output_path.open("wb") as fh:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        fh.write(chunk)
    except Exception as exc:
        return {"ok": False, "error": f"download_failed:{exc}"}

    if not output_path.exists() or output_path.stat().st_size <= 0:
        return {"ok": False, "error": "download_empty_file"}
    return {"ok": True, "error": ""}


def _compose_video_moviepy(
    *,
    bg_video_path: Path,
    audio_path: Path,
    output_path: Path,
    subtitle_text: str,
) -> Dict[str, Any]:
    dep_err = _require_module("moviepy")
    if dep_err:
        return {"ok": False, "error": dep_err}

    from moviepy.editor import (  # type: ignore
        AudioFileClip,
        CompositeVideoClip,
        TextClip,
        VideoFileClip,
        concatenate_videoclips,
    )

    video: Any = None
    audio: Any = None
    final_clip: Any = None
    subtitle_clip: Any = None
    try:
        audio = AudioFileClip(str(audio_path))
        audio_duration = max(1.0, float(audio.duration or 1.0))

        video = VideoFileClip(str(bg_video_path)).without_audio()
        if video.w <= 0 or video.h <= 0:
            return {"ok": False, "error": "invalid_bg_video_dimensions"}

        # Force 9:16 center-crop + resize.
        target_w, target_h = 720, 1280
        src_ratio = video.w / video.h
        target_ratio = target_w / target_h
        if src_ratio > target_ratio:
            new_w = int(video.h * target_ratio)
            x1 = max(0, int((video.w - new_w) / 2))
            video = video.crop(x1=x1, y1=0, x2=x1 + new_w, y2=video.h)
        else:
            new_h = int(video.w / target_ratio)
            y1 = max(0, int((video.h - new_h) / 2))
            video = video.crop(x1=0, y1=y1, x2=video.w, y2=y1 + new_h)
        video = video.resize((target_w, target_h))

        if video.duration < audio_duration:
            loops = max(1, int(math.ceil(audio_duration / max(video.duration, 0.1))))
            video = concatenate_videoclips([video] * loops)
        video = video.subclip(0, audio_duration)

        clean_subtitle = _clean_text(subtitle_text, 180)
        subtitle_clip = TextClip(
            clean_subtitle,
            fontsize=52,
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(660, None),
            align="center",
        ).set_duration(audio_duration)
        subtitle_clip = subtitle_clip.set_position(("center", "bottom"))

        final_clip = CompositeVideoClip([video, subtitle_clip]).set_audio(audio)
        final_clip.write_videofile(
            str(output_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            threads=2,
            verbose=False,
            logger=None,
        )

        if not output_path.exists() or output_path.stat().st_size <= 0:
            return {"ok": False, "error": "moviepy_output_missing"}

        return {"ok": True, "error": "", "duration": round(audio_duration, 2)}
    except Exception as exc:
        return {"ok": False, "error": f"moviepy_failed:{exc}"}
    finally:
        for clip in [subtitle_clip, final_clip, video, audio]:
            try:
                if clip is not None:
                    clip.close()
            except Exception:
                pass


def render_faceless_video_local(
    *,
    title: str,
    narration_text: str,
    subtitle_text: str,
    output_path: Path,
    duration_seconds: int,
    pexels_query: str,
    pexels_api_key: str,
    edge_tts_voice: str,
) -> Dict[str, Any]:
    ensure_dir(output_path.parent)

    install_hint = (
        "pip install edge-tts moviepy==1.0.3 requests "
        "google-auth-oauthlib google-api-python-client"
    )

    narration = _clean_text(narration_text, 1800)
    if not narration:
        narration = _clean_text(title, 300)

    with tempfile.TemporaryDirectory(prefix="faceless_render_") as tmp:
        tmp_dir = Path(tmp)
        audio_path = tmp_dir / "voice.mp3"
        bg_path = tmp_dir / "bg.mp4"

        tts = _edge_tts_generate(audio_path, narration, edge_tts_voice or "de-DE-KillianNeural")
        if not bool(tts.get("ok")):
            return {
                "ok": False,
                "status": "failed",
                "provider": "local_faceless",
                "output_file": "",
                "operation_name": "edge_tts+pexels+moviepy",
                "error": f"{tts.get('error')} | install_hint:{install_hint}",
            }

        pick = _fetch_pexels_video_link(pexels_api_key, pexels_query or title)
        if not bool(pick.get("ok")):
            return {
                "ok": False,
                "status": "failed",
                "provider": "local_faceless",
                "output_file": "",
                "operation_name": "edge_tts+pexels+moviepy",
                "error": f"{pick.get('error')} | ensure_valid_PEXELS_API_KEY",
            }

        download = _download_file(str(pick.get("link") or ""), bg_path)
        if not bool(download.get("ok")):
            return {
                "ok": False,
                "status": "failed",
                "provider": "local_faceless",
                "output_file": "",
                "operation_name": "edge_tts+pexels+moviepy",
                "error": str(download.get("error") or "pexels_download_failed"),
            }

        compose = _compose_video_moviepy(
            bg_video_path=bg_path,
            audio_path=audio_path,
            output_path=output_path,
            subtitle_text=subtitle_text or title,
        )
        if not bool(compose.get("ok")):
            return {
                "ok": False,
                "status": "failed",
                "provider": "local_faceless",
                "output_file": "",
                "operation_name": "edge_tts+pexels+moviepy",
                "error": f"{compose.get('error')} | install_hint:{install_hint}",
            }

    return {
        "ok": True,
        "status": "rendered",
        "provider": "local_faceless",
        "output_file": str(output_path),
        "operation_name": "edge_tts+pexels+moviepy",
        "error": "",
    }
