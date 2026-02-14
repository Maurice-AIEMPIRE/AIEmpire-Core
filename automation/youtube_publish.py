from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from automation.n8n_events import post_n8n_event
from automation.utils.files import env_or_default


ROOT = Path(__file__).resolve().parents[1]
YT_TOKEN_URL = "https://oauth2.googleapis.com/token"
YT_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
YT_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


class PublishError(RuntimeError):
    pass


@dataclass
class PublisherConfig:
    client_id: str
    client_secret: str
    refresh_token: str
    access_token: str
    youtube_api_key: str
    category_id: str = "27"
    made_for_kids: bool = False
    notify_subscribers: bool = True


def _has_youtube_publish_auth(cfg: PublisherConfig) -> bool:
    has_access = bool(str(cfg.access_token or "").strip())
    has_refresh_flow = bool(
        str(cfg.client_id or "").strip()
        and str(cfg.client_secret or "").strip()
        and str(cfg.refresh_token or "").strip()
    )
    return has_access or has_refresh_flow


def _is_transient_publish_auth_error(message: str) -> bool:
    text = str(message or "").strip().lower()
    if not text:
        return False
    markers = (
        "missing youtube_access_token",
        "token refresh failed",
        "token refresh connection error",
        "upload failed after token refresh",
        "youtube upload connection error",
        "youtube upload http 401",
    )
    return any(marker in text for marker in markers)


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> Optional[dt.datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except ValueError:
        return None


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _truthy(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _refresh_access_token(cfg: PublisherConfig) -> str:
    if not cfg.client_id or not cfg.client_secret or not cfg.refresh_token:
        raise PublishError("Missing YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET / YOUTUBE_REFRESH_TOKEN for token refresh")

    payload = urllib.parse.urlencode(
        {
            "client_id": cfg.client_id,
            "client_secret": cfg.client_secret,
            "refresh_token": cfg.refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        YT_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else str(exc)
        raise PublishError(f"Token refresh failed: {detail}") from exc
    except urllib.error.URLError as exc:
        raise PublishError(f"Token refresh connection error: {exc}") from exc

    token = str(data.get("access_token") or "").strip()
    if not token:
        raise PublishError("Token refresh returned no access_token")
    return token


def _guess_content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def _multipart_related(metadata: Dict[str, Any], file_path: Path, boundary: str) -> bytes:
    meta_json = json.dumps(metadata, ensure_ascii=False).encode("utf-8")
    file_bytes = file_path.read_bytes()
    content_type = _guess_content_type(file_path)

    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b"Content-Type: application/json; charset=UTF-8\r\n\r\n")
    body.extend(meta_json)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f"Content-Type: {content_type}\r\n".encode("utf-8"))
    body.extend(b"Content-Transfer-Encoding: binary\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body)


def _upload_once(
    cfg: PublisherConfig,
    *,
    access_token: str,
    file_path: Path,
    title: str,
    description: str,
    tags: List[str],
    mode: str,
) -> Dict[str, Any]:
    boundary = f"===============codex_{uuid.uuid4().hex}"
    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:15],
            "categoryId": cfg.category_id,
        },
        "status": {
            "privacyStatus": mode,
            "selfDeclaredMadeForKids": cfg.made_for_kids,
        },
    }
    params = urllib.parse.urlencode(
        {
            "part": "snippet,status",
            "uploadType": "multipart",
            "notifySubscribers": "true" if cfg.notify_subscribers else "false",
        }
    )
    url = f"{YT_UPLOAD_URL}?{params}"
    data = _multipart_related(metadata, file_path, boundary)
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
            "Content-Length": str(len(data)),
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upload_video(
    cfg: PublisherConfig,
    *,
    file_path: Path,
    title: str,
    description: str,
    tags: List[str],
    mode: str,
) -> Dict[str, Any]:
    token = cfg.access_token.strip()
    if not token and cfg.refresh_token:
        token = _refresh_access_token(cfg)
    if not token:
        raise PublishError("Missing YOUTUBE_ACCESS_TOKEN and no refresh fallback available")

    try:
        return _upload_once(
            cfg,
            access_token=token,
            file_path=file_path,
            title=title,
            description=description,
            tags=tags,
            mode=mode,
        )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else str(exc)
        if exc.code == 401 and cfg.refresh_token:
            token = _refresh_access_token(cfg)
            try:
                return _upload_once(
                    cfg,
                    access_token=token,
                    file_path=file_path,
                    title=title,
                    description=description,
                    tags=tags,
                    mode=mode,
                )
            except Exception as exc2:
                raise PublishError(f"YouTube upload failed after token refresh: {exc2}") from exc2
        raise PublishError(f"YouTube upload HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise PublishError(f"YouTube upload connection error: {exc}") from exc


def _queue_path(workflow: str, run_id: str) -> Path:
    if workflow == "shorts_revenue":
        return ROOT / "content_factory" / "deliverables" / workflow / run_id / "youtube_publish_queue.csv"
    if workflow == "youtube_shorts":
        return ROOT / "content_factory" / "deliverables" / workflow / run_id / "publish_queue.csv"
    raise PublishError(f"Unsupported workflow for YouTube publish: {workflow}")


def _latest_run_id(workflow: str) -> str:
    latest = ROOT / "content_factory" / "deliverables" / workflow / "latest.json"
    payload = _load_json(latest)
    run_id = str(payload.get("run_id") or "").strip()
    if not run_id:
        raise PublishError(f"No latest run_id found for workflow={workflow}")
    return run_id


def _normalize_tags(raw: str) -> List[str]:
    tokens = [t.strip() for t in str(raw or "").replace(",", " ").split() if t.strip()]
    out: List[str] = []
    for tok in tokens:
        if not tok.startswith("#"):
            tok = "#" + tok
        out.append(tok)
    # unique keep order
    seen = set()
    uniq = []
    for t in out:
        low = t.lower()
        if low in seen:
            continue
        seen.add(low)
        uniq.append(t)
    return uniq


def _build_description(row: Dict[str, Any]) -> str:
    if row.get("description"):
        return str(row.get("description") or "")
    hook = str(row.get("hook") or "").strip()
    script = str(row.get("script") or "").strip()
    cta = str(row.get("cta") or row.get("offer_cta") or "").strip()
    tags = str(row.get("hashtags") or "").strip()
    parts = [p for p in [hook, script, cta, tags] if p]
    return "\n\n".join(parts).strip()[:5000]


def _state_key(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "status"
    if "upload_status" in rows[0]:
        return "upload_status"
    return "status"


def _ensure_columns(fieldnames: List[str], needed: List[str]) -> List[str]:
    out = list(fieldnames)
    for col in needed:
        if col not in out:
            out.append(col)
    return out


def _queue_filename_for_workflow(workflow: str) -> str:
    if workflow == "shorts_revenue":
        return "youtube_publish_queue.csv"
    return "publish_queue.csv"


def _iter_queue_files(workflow: str) -> List[Path]:
    base = ROOT / "content_factory" / "deliverables" / workflow
    if not base.exists():
        return []
    qname = _queue_filename_for_workflow(workflow)
    files = [p for p in base.glob(f"*/{qname}") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def _collect_publish_history(workflow: str) -> List[Dict[str, Any]]:
    history: List[Dict[str, Any]] = []
    for queue in _iter_queue_files(workflow):
        try:
            with queue.open("r", encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
        except OSError:
            continue
        state_col = _state_key(rows)
        for row in rows:
            state = str(row.get(state_col) or "").strip().lower()
            if state != "published":
                continue
            published_at = str(row.get("published_at") or "").strip()
            if not published_at:
                continue
            history.append(
                {
                    "published_at": published_at,
                    "published_mode": str(row.get("published_mode") or "").strip().lower() or "unknown",
                    "published_video_id": str(row.get("published_video_id") or "").strip(),
                    "queue_file": str(queue),
                }
            )
    history.sort(key=lambda x: str(x.get("published_at") or ""), reverse=True)
    return history


def _fetch_video_kpis(api_key: str, video_ids: List[str]) -> Dict[str, Any]:
    valid_ids = [vid for vid in video_ids if vid]
    if not api_key or not valid_ids:
        return {"available": False, "avg_vph": 0.0, "avg_like_rate": 0.0, "count": 0, "videos": []}
    params = urllib.parse.urlencode(
        {
            "part": "snippet,statistics",
            "id": ",".join(valid_ids[:50]),
            "maxResults": 50,
            "key": api_key,
        }
    )
    req = urllib.request.Request(f"{YT_VIDEOS_URL}?{params}", headers={"User-Agent": "ai-empire-youtube-publish/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    videos: List[Dict[str, Any]] = []
    now = dt.datetime.now(dt.timezone.utc)
    for item in payload.get("items", []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict):
            continue
        stats = item.get("statistics") or {}
        snippet = item.get("snippet") or {}
        views = int(str(stats.get("viewCount") or "0"))
        likes = int(str(stats.get("likeCount") or "0"))
        published_at_raw = str(snippet.get("publishedAt") or "")
        published_at = _parse_iso(published_at_raw)
        if not published_at:
            continue
        age_hours = max((now - published_at).total_seconds() / 3600.0, 1.0)
        videos.append(
            {
                "video_id": str(item.get("id") or ""),
                "views": views,
                "likes": likes,
                "vph": round(views / age_hours, 2),
                "like_rate": round((likes / views) if views else 0.0, 4),
            }
        )
    if not videos:
        return {"available": False, "avg_vph": 0.0, "avg_like_rate": 0.0, "count": 0, "videos": []}
    avg_vph = sum(v["vph"] for v in videos) / len(videos)
    avg_like_rate = sum(v["like_rate"] for v in videos) / len(videos)
    return {
        "available": True,
        "avg_vph": round(avg_vph, 2),
        "avg_like_rate": round(avg_like_rate, 4),
        "count": len(videos),
        "videos": videos,
    }


def _guard_state_path(workflow: str) -> Path:
    return ROOT / "content_factory" / "deliverables" / workflow / "publish_guard_state.json"


def _evaluate_publish_mode(
    *,
    workflow: str,
    requested_mode: str,
    cfg: PublisherConfig,
    history: List[Dict[str, Any]],
    now: dt.datetime,
) -> Tuple[str, Dict[str, Any]]:
    guard_path = _guard_state_path(workflow)
    guard = _load_json(guard_path)
    active_until = _parse_iso(str(guard.get("active_until") or ""))
    details: Dict[str, Any] = {
        "requested_mode": requested_mode,
        "effective_mode": requested_mode,
        "guard_active": False,
        "guard_reason": "",
        "guard_active_until": str(guard.get("active_until") or ""),
        "kpi_snapshot": {},
    }

    if active_until and active_until > now:
        details["guard_active"] = True
        details["guard_reason"] = str(guard.get("reason") or "killswitch_active")
        details["effective_mode"] = "unlisted"
        return "unlisted", details

    if requested_mode != "public":
        return requested_mode, details

    public_published = [item for item in history if str(item.get("published_mode") or "") == "public"]
    latest_public = public_published[:6]
    if len(latest_public) < 6:
        return requested_mode, details

    video_ids = [str(item.get("published_video_id") or "") for item in latest_public]
    try:
        kpis = _fetch_video_kpis(cfg.youtube_api_key, video_ids)
    except Exception as exc:
        details["kpi_snapshot"] = {"available": False, "error": str(exc)}
        return requested_mode, details

    details["kpi_snapshot"] = kpis
    if not bool(kpis.get("available")):
        return requested_mode, details

    avg_vph = float(kpis.get("avg_vph") or 0.0)
    avg_like_rate = float(kpis.get("avg_like_rate") or 0.0)
    if avg_vph < 50.0 or avg_like_rate < 0.02:
        active_until_new = now + dt.timedelta(hours=12)
        reason = (
            f"kpi_killswitch avg_vph={avg_vph:.2f} avg_like_rate={avg_like_rate:.4f} "
            f"thresholds(vph<50 or like_rate<0.02)"
        )
        payload = {
            "updated_at": _now_iso(),
            "active_until": active_until_new.isoformat().replace("+00:00", "Z"),
            "reason": reason,
            "avg_vph": avg_vph,
            "avg_like_rate": avg_like_rate,
        }
        guard_path.parent.mkdir(parents=True, exist_ok=True)
        guard_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        details["guard_active"] = True
        details["guard_reason"] = reason
        details["guard_active_until"] = payload["active_until"]
        details["effective_mode"] = "unlisted"
        return "unlisted", details

    if guard_path.exists():
        guard_path.unlink()
    return requested_mode, details


def process_queue(
    *,
    workflow: str,
    run_id: Optional[str],
    mode: str,
    max_posts: int,
    max_posts_per_day: int,
    min_spacing_min: int,
    dry_run: bool,
    cfg: PublisherConfig,
) -> Dict[str, Any]:
    resolved_run_id = run_id or _latest_run_id(workflow)
    queue = _queue_path(workflow, resolved_run_id)
    if not queue.exists():
        raise PublishError(f"Queue not found: {queue}")

    with queue.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    state_col = _state_key(rows)
    fieldnames = _ensure_columns(
        fieldnames,
        ["published_video_id", "published_url", "published_at", "published_mode", "publish_error"],
    )

    now = dt.datetime.now(dt.timezone.utc)
    auth_ready = _has_youtube_publish_auth(cfg)
    recovered_rows = 0
    for row in rows:
        state = str(row.get(state_col) or "").strip().lower()
        if state != "error":
            continue
        if _is_transient_publish_auth_error(str(row.get("publish_error") or "")):
            row[state_col] = "ready"
            row["publish_error"] = ""
            recovered_rows += 1

    history = _collect_publish_history(workflow)
    effective_mode, guard_details = _evaluate_publish_mode(
        workflow=workflow,
        requested_mode=mode,
        cfg=cfg,
        history=history,
        now=now,
    )

    blocked_reason = ""
    if not dry_run and not auth_ready:
        blocked_reason = "missing_youtube_auth:need_access_token_or_refresh_credentials"
    day_limit = max(1, int(max_posts_per_day))
    spacing_minutes = max(0, int(min_spacing_min))
    history_24h = []
    for entry in history:
        published_at = _parse_iso(str(entry.get("published_at") or ""))
        if not published_at:
            continue
        if (now - published_at) <= dt.timedelta(hours=24):
            history_24h.append(entry)
    if len(history_24h) >= day_limit:
        blocked_reason = f"daily_cap_reached:{len(history_24h)}/{day_limit}"

    if not blocked_reason and spacing_minutes > 0 and history:
        latest_published = _parse_iso(str(history[0].get("published_at") or ""))
        if latest_published:
            since_min = (now - latest_published).total_seconds() / 60.0
            if since_min < spacing_minutes:
                blocked_reason = f"spacing_guard_active:{since_min:.1f}<{spacing_minutes}min"

    published = 0
    errors = 0

    for row in rows:
        if blocked_reason:
            break
        state = str(row.get(state_col) or "").strip().lower()
        if state not in {"ready", "planned", "queued"}:
            continue
        if published >= max_posts:
            break

        video_file = Path(str(row.get("video_file") or "").strip())
        if not video_file.is_absolute():
            video_file = ROOT / str(video_file)
        if not video_file.exists():
            row[state_col] = "error"
            row["publish_error"] = f"video file not found: {video_file}"
            errors += 1
            continue

        title = str(row.get("title") or row.get("caption") or "").strip()[:100]
        if not title:
            row[state_col] = "error"
            row["publish_error"] = "missing title/caption"
            errors += 1
            continue
        description = _build_description(row)
        tags = _normalize_tags(str(row.get("hashtags") or ""))

        if dry_run:
            row[state_col] = "dry_run_ready"
            row["publish_error"] = ""
            continue

        try:
            payload = upload_video(
                cfg,
                file_path=video_file,
                title=title,
                description=description,
                tags=tags,
                mode=effective_mode,
            )
            video_id = str(payload.get("id") or "").strip()
            if not video_id:
                raise PublishError("upload response missing video id")
            row[state_col] = "published"
            row["published_video_id"] = video_id
            row["published_url"] = f"https://www.youtube.com/watch?v={video_id}"
            row["published_at"] = _now_iso()
            row["published_mode"] = effective_mode
            row["publish_error"] = ""
            published += 1
        except Exception as exc:  # pragma: no cover
            row[state_col] = "error"
            row["publish_error"] = str(exc)
            errors += 1

    with queue.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    summary = {
        "workflow": workflow,
        "run_id": resolved_run_id,
        "queue_file": str(queue),
        "mode": mode,
        "effective_mode": effective_mode,
        "auth_ready": auth_ready,
        "recovered_rows": recovered_rows,
        "max_posts_per_day": day_limit,
        "min_spacing_min": spacing_minutes,
        "blocked_reason": blocked_reason,
        "guard": guard_details,
        "dry_run": dry_run,
        "published_count": published,
        "error_count": errors,
        "timestamp": _now_iso(),
    }
    summary_path = queue.parent / "publish_run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    post_n8n_event(
        event_type="youtube_publish_result",
        source="automation.youtube_publish",
        payload=summary,
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-publish YouTube queue rows using YouTube Data API uploads")
    parser.add_argument("--workflow", choices=["youtube_shorts", "shorts_revenue"], required=True)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--mode", choices=["public", "unlisted", "private"], default=None)
    parser.add_argument("--max-posts", type=int, default=1)
    parser.add_argument("--max-posts-per-day", type=int, default=6)
    parser.add_argument("--min-spacing-min", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = PublisherConfig(
        client_id=str(env_or_default("YOUTUBE_CLIENT_ID", "") or ""),
        client_secret=str(env_or_default("YOUTUBE_CLIENT_SECRET", "") or ""),
        refresh_token=str(env_or_default("YOUTUBE_REFRESH_TOKEN", "") or ""),
        access_token=str(env_or_default("YOUTUBE_ACCESS_TOKEN", "") or ""),
        youtube_api_key=str(env_or_default("YOUTUBE_API_KEY", "") or ""),
        category_id=str(env_or_default("YOUTUBE_CATEGORY_ID", "27") or "27"),
        made_for_kids=_truthy(str(env_or_default("YOUTUBE_MADE_FOR_KIDS", "0") or "0")),
        notify_subscribers=_truthy(str(env_or_default("YOUTUBE_NOTIFY_SUBSCRIBERS", "1") or "1")),
    )
    mode = args.mode or str(env_or_default("AUTO_PUBLISH_MODE", "public") or "public")
    summary = process_queue(
        workflow=args.workflow,
        run_id=args.run_id,
        mode=mode,
        max_posts=max(1, int(args.max_posts)),
        max_posts_per_day=max(1, int(args.max_posts_per_day)),
        min_spacing_min=max(0, int(args.min_spacing_min)),
        dry_run=bool(args.dry_run),
        cfg=cfg,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
