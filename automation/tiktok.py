from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from automation.utils.files import env_or_default


AUTH_ENDPOINT = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_ENDPOINT = "https://open.tiktokapis.com/v2/oauth/token/"
REVOKE_ENDPOINT = "https://open.tiktokapis.com/v2/oauth/revoke/"
USER_INFO_ENDPOINT = "https://open.tiktokapis.com/v2/user/info/"
VIDEO_LIST_ENDPOINT = "https://open.tiktokapis.com/v2/video/list/"
VIDEO_QUERY_ENDPOINT = "https://open.tiktokapis.com/v2/video/query/"
CREATOR_INFO_ENDPOINT = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
INBOX_VIDEO_INIT_ENDPOINT = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
DIRECT_VIDEO_INIT_ENDPOINT = "https://open.tiktokapis.com/v2/post/publish/video/init/"
POST_STATUS_ENDPOINT = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

DEFAULT_VIDEO_FIELDS = (
    "id,title,create_time,duration,cover_image_url,share_url,view_count,like_count,comment_count"
)
DEFAULT_USER_FIELDS = "open_id,union_id,avatar_url,display_name"
DEFAULT_PRIVACY_LEVEL = "PUBLIC_TO_EVERYONE"

MIN_UPLOAD_CHUNK_BYTES = 5 * 1024 * 1024
MAX_UPLOAD_CHUNK_BYTES = 64 * 1024 * 1024


def _require_value(name: str, value: Optional[str]) -> str:
    if value and value.strip():
        return value.strip()
    raise ValueError(f"Missing required value: {name}")


def _format_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def _env_bool(name: str, default: bool = False) -> bool:
    value = env_or_default(name)
    if value is None:
        return default
    value = value.strip().lower()
    return value in {"1", "true", "yes", "on", "y"}


def _split_csv(raw: str) -> List[str]:
    return [x.strip() for x in raw.split(",") if x.strip()]


def _normalize_upload_chunk_size(video_size: int, chunk_size: Optional[int]) -> int:
    if video_size <= 0:
        raise ValueError("Video file is empty")
    if chunk_size is None or chunk_size <= 0:
        if video_size <= MAX_UPLOAD_CHUNK_BYTES:
            return video_size
        return 10 * 1024 * 1024

    if chunk_size > MAX_UPLOAD_CHUNK_BYTES and video_size > chunk_size:
        raise ValueError("chunk_size must be <= 64MB for multi-chunk uploads")
    if video_size > MIN_UPLOAD_CHUNK_BYTES and chunk_size < MIN_UPLOAD_CHUNK_BYTES and video_size > chunk_size:
        raise ValueError("chunk_size must be >= 5MB when using multiple chunks")
    return chunk_size


def _validate_tiktok_response(payload: Dict[str, Any], strict: bool = True) -> None:
    if not strict:
        return
    error = payload.get("error")
    if isinstance(error, dict):
        code = str(error.get("code", "")).strip().lower()
        if code and code != "ok":
            message = str(error.get("message", "")).strip()
            log_id = str(error.get("log_id", "")).strip()
            suffix = f" (log_id={log_id})" if log_id else ""
            raise RuntimeError(f"TikTok error {code}: {message}{suffix}")


def _http_post_form(
    url: str,
    form: Dict[str, str],
    timeout: int = 30,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    body = urllib.parse.urlencode(form).encode("utf-8")
    req_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(
        url,
        data=body,
        headers=req_headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else str(exc)
        raise RuntimeError(f"HTTP {exc.code} on {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Connection error on {url}: {exc}") from exc


def _http_json(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    query: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    encoded_query = urllib.parse.urlencode(
        {k: str(v) for k, v in (query or {}).items() if v is not None and str(v) != ""}
    )
    request_url = f"{url}?{encoded_query}" if encoded_query else url
    req_headers = headers.copy() if headers else {}
    body: Optional[bytes] = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json; charset=UTF-8")
    req = urllib.request.Request(request_url, headers=req_headers, data=body, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else str(exc)
        raise RuntimeError(f"HTTP {exc.code} on {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Connection error on {url}: {exc}") from exc


def _upload_bytes(
    upload_url: str,
    data: bytes,
    *,
    start: int,
    end: int,
    total_size: int,
    mime_type: str,
    timeout: int = 120,
) -> Tuple[int, str]:
    headers = {
        "Content-Type": mime_type,
        "Content-Length": str(len(data)),
        "Content-Range": f"bytes {start}-{end}/{total_size}",
    }
    req = urllib.request.Request(upload_url, data=data, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = int(resp.status)
            range_header = str(resp.headers.get("Content-Range", ""))
            return status, range_header
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else str(exc)
        raise RuntimeError(f"Upload HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Upload connection error: {exc}") from exc


def upload_file_chunks(
    upload_url: str,
    file_path: Path,
    *,
    chunk_size: Optional[int],
    mime_type: str,
    timeout: int = 120,
) -> Dict[str, Any]:
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")
    total_size = file_path.stat().st_size
    actual_chunk_size = _normalize_upload_chunk_size(total_size, chunk_size)
    total_chunks = int(math.ceil(total_size / actual_chunk_size))

    uploads: List[Dict[str, Any]] = []
    with file_path.open("rb") as handle:
        start = 0
        while start < total_size:
            end = min(start + actual_chunk_size, total_size) - 1
            chunk = handle.read(end - start + 1)
            if not chunk:
                break
            status, uploaded_range = _upload_bytes(
                upload_url=upload_url,
                data=chunk,
                start=start,
                end=end,
                total_size=total_size,
                mime_type=mime_type,
                timeout=timeout,
            )
            uploads.append(
                {
                    "chunk_index": len(uploads),
                    "start": start,
                    "end": end,
                    "bytes": len(chunk),
                    "status": status,
                    "uploaded_range": uploaded_range,
                }
            )
            start = end + 1

    return {
        "file_path": str(file_path),
        "video_size": total_size,
        "chunk_size": actual_chunk_size,
        "total_chunks": total_chunks,
        "uploaded_chunks": len(uploads),
        "chunks": uploads,
    }


def build_auth_url(
    client_key: str,
    redirect_uri: str,
    scopes: str,
    state: Optional[str],
    code_challenge: Optional[str],
    code_challenge_method: str,
) -> str:
    params = {
        "client_key": client_key,
        "response_type": "code",
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "state": state or secrets.token_hex(12),
    }
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = code_challenge_method
    query = urllib.parse.urlencode(params)
    return f"{AUTH_ENDPOINT}?{query}"


def generate_pkce_pair() -> Dict[str, str]:
    verifier = secrets.token_urlsafe(64)
    verifier = verifier[:128]
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return {
        "code_verifier": verifier,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }


def exchange_code(
    *,
    client_key: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    code_verifier: Optional[str],
) -> Dict[str, Any]:
    form = {
        "client_key": client_key,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    if code_verifier:
        form["code_verifier"] = code_verifier
    return _http_post_form(TOKEN_ENDPOINT, form)


def refresh_access_token(*, client_key: str, client_secret: str, refresh_token: str) -> Dict[str, Any]:
    form = {
        "client_key": client_key,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    return _http_post_form(TOKEN_ENDPOINT, form)


def get_client_token(*, client_key: str, client_secret: str) -> Dict[str, Any]:
    form = {
        "client_key": client_key,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    return _http_post_form(TOKEN_ENDPOINT, form)


def revoke_token(*, client_key: str, client_secret: str, token: str) -> Dict[str, Any]:
    form = {
        "client_key": client_key,
        "client_secret": client_secret,
        "token": token,
    }
    return _http_post_form(REVOKE_ENDPOINT, form)


def get_user_info(access_token: str, fields: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {access_token}"}
    return _http_json("GET", USER_INFO_ENDPOINT, headers=headers, query={"fields": fields})


def list_videos(access_token: str, fields: str, cursor: Optional[int], max_count: Optional[int]) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    payload: Dict[str, Any] = {}
    if cursor is not None:
        payload["cursor"] = int(cursor)
    if max_count is not None:
        payload["max_count"] = int(max_count)
    return _http_json("POST", VIDEO_LIST_ENDPOINT, headers=headers, query={"fields": fields}, payload=payload)


def query_videos(access_token: str, fields: str, video_ids: List[str]) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    payload = {"filters": {"video_ids": video_ids}}
    return _http_json("POST", VIDEO_QUERY_ENDPOINT, headers=headers, query={"fields": fields}, payload=payload)


def query_creator_info(access_token: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    return _http_json("POST", CREATOR_INFO_ENDPOINT, headers=headers, payload={})


def init_inbox_video(access_token: str, source_info: Dict[str, Any]) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    return _http_json("POST", INBOX_VIDEO_INIT_ENDPOINT, headers=headers, payload={"source_info": source_info})


def init_direct_video(access_token: str, post_info: Dict[str, Any], source_info: Dict[str, Any]) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    payload = {"post_info": post_info, "source_info": source_info}
    return _http_json("POST", DIRECT_VIDEO_INIT_ENDPOINT, headers=headers, payload=payload)


def fetch_post_status(access_token: str, publish_id: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    return _http_json("POST", POST_STATUS_ENDPOINT, headers=headers, payload={"publish_id": publish_id})


def _source_info_from_file(file_path: Path, chunk_size: Optional[int]) -> Dict[str, Any]:
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")
    video_size = file_path.stat().st_size
    normalized_chunk_size = _normalize_upload_chunk_size(video_size, chunk_size)
    total_chunk_count = int(math.ceil(video_size / normalized_chunk_size))
    return {
        "source": "FILE_UPLOAD",
        "video_size": video_size,
        "chunk_size": normalized_chunk_size,
        "total_chunk_count": total_chunk_count,
    }


def _post_info_from_args(args: argparse.Namespace) -> Dict[str, Any]:
    title = _require_value("title", args.title)
    privacy_level = args.privacy_level or env_or_default("TIKTOK_PRIVACY_LEVEL", DEFAULT_PRIVACY_LEVEL)
    return {
        "title": title,
        "privacy_level": privacy_level,
        "disable_comment": bool(args.disable_comment),
        "disable_duet": bool(args.disable_duet),
        "disable_stitch": bool(args.disable_stitch),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="TikTok API helper for automation project")
    parser.add_argument(
        "--strict-error",
        action="store_true",
        default=_env_bool("TIKTOK_API_STRICT", True),
        help="Fail when TikTok response contains error.code != ok",
    )
    parser.add_argument(
        "--no-strict-error",
        dest="strict_error",
        action="store_false",
        help="Do not fail on TikTok error object",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_pkce = sub.add_parser("pkce", help="Generate PKCE verifier/challenge pair")

    p_auth = sub.add_parser("auth-url", help="Generate TikTok OAuth authorization URL")
    p_auth.add_argument("--client-key", default=env_or_default("TIKTOK_CLIENT_KEY"))
    p_auth.add_argument("--redirect-uri", default=env_or_default("TIKTOK_REDIRECT_URI"))
    p_auth.add_argument(
        "--scopes",
        default=env_or_default("TIKTOK_SCOPES", "user.info.basic,video.list"),
        help="Comma-separated scopes",
    )
    p_auth.add_argument("--state", default=env_or_default("TIKTOK_STATE"))
    p_auth.add_argument("--code-challenge", default=env_or_default("TIKTOK_CODE_CHALLENGE"))
    p_auth.add_argument("--code-challenge-method", default=env_or_default("TIKTOK_CODE_CHALLENGE_METHOD", "S256"))

    p_exchange = sub.add_parser("exchange-code", help="Exchange OAuth code for access token")
    p_exchange.add_argument("--client-key", default=env_or_default("TIKTOK_CLIENT_KEY"))
    p_exchange.add_argument("--client-secret", default=env_or_default("TIKTOK_CLIENT_SECRET"))
    p_exchange.add_argument("--code", required=True)
    p_exchange.add_argument("--redirect-uri", default=env_or_default("TIKTOK_REDIRECT_URI"))
    p_exchange.add_argument("--code-verifier", default=env_or_default("TIKTOK_CODE_VERIFIER"))

    p_refresh = sub.add_parser("refresh-token", help="Refresh TikTok access token")
    p_refresh.add_argument("--client-key", default=env_or_default("TIKTOK_CLIENT_KEY"))
    p_refresh.add_argument("--client-secret", default=env_or_default("TIKTOK_CLIENT_SECRET"))
    p_refresh.add_argument("--refresh-token", default=env_or_default("TIKTOK_REFRESH_TOKEN"))

    p_client = sub.add_parser("client-token", help="Request app-level client token")
    p_client.add_argument("--client-key", default=env_or_default("TIKTOK_CLIENT_KEY"))
    p_client.add_argument("--client-secret", default=env_or_default("TIKTOK_CLIENT_SECRET"))

    p_revoke = sub.add_parser("revoke-token", help="Revoke a TikTok access or refresh token")
    p_revoke.add_argument("--client-key", default=env_or_default("TIKTOK_CLIENT_KEY"))
    p_revoke.add_argument("--client-secret", default=env_or_default("TIKTOK_CLIENT_SECRET"))
    p_revoke.add_argument("--token", default=env_or_default("TIKTOK_REVOKE_TOKEN"))

    p_user = sub.add_parser("user-info", help="Fetch TikTok user profile data")
    p_user.add_argument("--access-token", default=env_or_default("TIKTOK_ACCESS_TOKEN"))
    p_user.add_argument(
        "--fields",
        default=env_or_default("TIKTOK_USER_FIELDS", DEFAULT_USER_FIELDS),
    )

    p_list = sub.add_parser("video-list", help="List user's public videos")
    p_list.add_argument("--access-token", default=env_or_default("TIKTOK_ACCESS_TOKEN"))
    p_list.add_argument("--fields", default=env_or_default("TIKTOK_VIDEO_FIELDS", DEFAULT_VIDEO_FIELDS))
    p_list.add_argument("--cursor", type=int, default=None)
    p_list.add_argument("--max-count", type=int, default=10)

    p_query = sub.add_parser("video-query", help="Query selected videos by id")
    p_query.add_argument("--access-token", default=env_or_default("TIKTOK_ACCESS_TOKEN"))
    p_query.add_argument("--fields", default=env_or_default("TIKTOK_VIDEO_FIELDS", DEFAULT_VIDEO_FIELDS))
    p_query.add_argument(
        "--video-ids",
        default=env_or_default("TIKTOK_VIDEO_IDS"),
        help="Comma-separated list of video ids",
    )

    p_creator = sub.add_parser("creator-info", help="Query creator info required for direct post UX")
    p_creator.add_argument("--access-token", default=env_or_default("TIKTOK_ACCESS_TOKEN"))

    p_inbox_file = sub.add_parser("inbox-init-file", help="Init inbox upload with local file (video.upload)")
    p_inbox_file.add_argument("--access-token", default=env_or_default("TIKTOK_ACCESS_TOKEN"))
    p_inbox_file.add_argument("--file", required=True)
    p_inbox_file.add_argument("--chunk-size", type=int, default=None, help="Bytes")
    p_inbox_file.add_argument("--upload", action="store_true", help="Upload binary immediately using returned upload_url")
    p_inbox_file.add_argument("--mime-type", default="video/mp4")

    p_inbox_url = sub.add_parser("inbox-init-url", help="Init inbox upload with pull-from-url")
    p_inbox_url.add_argument("--access-token", default=env_or_default("TIKTOK_ACCESS_TOKEN"))
    p_inbox_url.add_argument("--video-url", default=env_or_default("TIKTOK_VIDEO_URL"))

    p_direct_file = sub.add_parser("direct-init-file", help="Init direct post with local file (video.publish)")
    p_direct_file.add_argument("--access-token", default=env_or_default("TIKTOK_ACCESS_TOKEN"))
    p_direct_file.add_argument("--file", required=True)
    p_direct_file.add_argument("--title", default=env_or_default("TIKTOK_TITLE"))
    p_direct_file.add_argument("--privacy-level", default=env_or_default("TIKTOK_PRIVACY_LEVEL", DEFAULT_PRIVACY_LEVEL))
    p_direct_file.add_argument("--disable-comment", action="store_true", default=_env_bool("TIKTOK_DISABLE_COMMENT", False))
    p_direct_file.add_argument("--disable-duet", action="store_true", default=_env_bool("TIKTOK_DISABLE_DUET", False))
    p_direct_file.add_argument("--disable-stitch", action="store_true", default=_env_bool("TIKTOK_DISABLE_STITCH", False))
    p_direct_file.add_argument("--chunk-size", type=int, default=None, help="Bytes")
    p_direct_file.add_argument("--upload", action="store_true", help="Upload binary immediately using returned upload_url")
    p_direct_file.add_argument("--mime-type", default="video/mp4")

    p_direct_url = sub.add_parser("direct-init-url", help="Init direct post with pull-from-url")
    p_direct_url.add_argument("--access-token", default=env_or_default("TIKTOK_ACCESS_TOKEN"))
    p_direct_url.add_argument("--title", default=env_or_default("TIKTOK_TITLE"))
    p_direct_url.add_argument("--privacy-level", default=env_or_default("TIKTOK_PRIVACY_LEVEL", DEFAULT_PRIVACY_LEVEL))
    p_direct_url.add_argument("--disable-comment", action="store_true", default=_env_bool("TIKTOK_DISABLE_COMMENT", False))
    p_direct_url.add_argument("--disable-duet", action="store_true", default=_env_bool("TIKTOK_DISABLE_DUET", False))
    p_direct_url.add_argument("--disable-stitch", action="store_true", default=_env_bool("TIKTOK_DISABLE_STITCH", False))
    p_direct_url.add_argument("--video-url", default=env_or_default("TIKTOK_VIDEO_URL"))

    p_status = sub.add_parser("post-status", help="Fetch post/upload status by publish_id")
    p_status.add_argument("--access-token", default=env_or_default("TIKTOK_ACCESS_TOKEN"))
    p_status.add_argument("--publish-id", required=True)

    p_upload = sub.add_parser("upload-file", help="Upload local file to a TikTok upload_url")
    p_upload.add_argument("--upload-url", required=True)
    p_upload.add_argument("--file", required=True)
    p_upload.add_argument("--chunk-size", type=int, default=None, help="Bytes")
    p_upload.add_argument("--mime-type", default="video/mp4")

    args = parser.parse_args()

    try:
        if args.command == "pkce":
            print(_format_json(generate_pkce_pair()))
            return 0

        if args.command == "auth-url":
            client_key = _require_value("TIKTOK_CLIENT_KEY", args.client_key)
            redirect_uri = _require_value("TIKTOK_REDIRECT_URI", args.redirect_uri)
            scopes = _require_value("TIKTOK_SCOPES", args.scopes)
            url = build_auth_url(
                client_key=client_key,
                redirect_uri=redirect_uri,
                scopes=scopes,
                state=args.state,
                code_challenge=args.code_challenge,
                code_challenge_method=args.code_challenge_method,
            )
            print(url)
            return 0

        if args.command == "exchange-code":
            payload = exchange_code(
                client_key=_require_value("TIKTOK_CLIENT_KEY", args.client_key),
                client_secret=_require_value("TIKTOK_CLIENT_SECRET", args.client_secret),
                code=_require_value("code", args.code),
                redirect_uri=_require_value("TIKTOK_REDIRECT_URI", args.redirect_uri),
                code_verifier=args.code_verifier,
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "refresh-token":
            payload = refresh_access_token(
                client_key=_require_value("TIKTOK_CLIENT_KEY", args.client_key),
                client_secret=_require_value("TIKTOK_CLIENT_SECRET", args.client_secret),
                refresh_token=_require_value("TIKTOK_REFRESH_TOKEN", args.refresh_token),
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "client-token":
            payload = get_client_token(
                client_key=_require_value("TIKTOK_CLIENT_KEY", args.client_key),
                client_secret=_require_value("TIKTOK_CLIENT_SECRET", args.client_secret),
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "revoke-token":
            payload = revoke_token(
                client_key=_require_value("TIKTOK_CLIENT_KEY", args.client_key),
                client_secret=_require_value("TIKTOK_CLIENT_SECRET", args.client_secret),
                token=_require_value("TIKTOK_REVOKE_TOKEN", args.token),
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "user-info":
            payload = get_user_info(
                access_token=_require_value("TIKTOK_ACCESS_TOKEN", args.access_token),
                fields=_require_value("TIKTOK_USER_FIELDS", args.fields),
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "video-list":
            payload = list_videos(
                access_token=_require_value("TIKTOK_ACCESS_TOKEN", args.access_token),
                fields=_require_value("TIKTOK_VIDEO_FIELDS", args.fields),
                cursor=args.cursor,
                max_count=args.max_count,
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "video-query":
            video_ids = _split_csv(_require_value("TIKTOK_VIDEO_IDS", args.video_ids))
            payload = query_videos(
                access_token=_require_value("TIKTOK_ACCESS_TOKEN", args.access_token),
                fields=_require_value("TIKTOK_VIDEO_FIELDS", args.fields),
                video_ids=video_ids,
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "creator-info":
            payload = query_creator_info(access_token=_require_value("TIKTOK_ACCESS_TOKEN", args.access_token))
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "inbox-init-file":
            file_path = Path(args.file).expanduser().resolve()
            source_info = _source_info_from_file(file_path, args.chunk_size)
            payload = init_inbox_video(
                access_token=_require_value("TIKTOK_ACCESS_TOKEN", args.access_token),
                source_info=source_info,
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            if args.upload:
                upload_url = (
                    (payload.get("data") or {}).get("upload_url")
                    if isinstance(payload.get("data"), dict)
                    else None
                )
                upload_url = _require_value("upload_url", str(upload_url) if upload_url else None)
                upload_result = upload_file_chunks(
                    upload_url=upload_url,
                    file_path=file_path,
                    chunk_size=source_info.get("chunk_size"),
                    mime_type=args.mime_type,
                )
                payload = {"init": payload, "upload": upload_result}
            print(_format_json(payload))
            return 0

        if args.command == "inbox-init-url":
            payload = init_inbox_video(
                access_token=_require_value("TIKTOK_ACCESS_TOKEN", args.access_token),
                source_info={"source": "PULL_FROM_URL", "video_url": _require_value("video_url", args.video_url)},
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "direct-init-file":
            file_path = Path(args.file).expanduser().resolve()
            post_info = _post_info_from_args(args)
            source_info = _source_info_from_file(file_path, args.chunk_size)
            payload = init_direct_video(
                access_token=_require_value("TIKTOK_ACCESS_TOKEN", args.access_token),
                post_info=post_info,
                source_info=source_info,
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            if args.upload:
                upload_url = (
                    (payload.get("data") or {}).get("upload_url")
                    if isinstance(payload.get("data"), dict)
                    else None
                )
                upload_url = _require_value("upload_url", str(upload_url) if upload_url else None)
                upload_result = upload_file_chunks(
                    upload_url=upload_url,
                    file_path=file_path,
                    chunk_size=source_info.get("chunk_size"),
                    mime_type=args.mime_type,
                )
                payload = {"init": payload, "upload": upload_result}
            print(_format_json(payload))
            return 0

        if args.command == "direct-init-url":
            payload = init_direct_video(
                access_token=_require_value("TIKTOK_ACCESS_TOKEN", args.access_token),
                post_info=_post_info_from_args(args),
                source_info={"source": "PULL_FROM_URL", "video_url": _require_value("video_url", args.video_url)},
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "post-status":
            payload = fetch_post_status(
                access_token=_require_value("TIKTOK_ACCESS_TOKEN", args.access_token),
                publish_id=_require_value("publish_id", args.publish_id),
            )
            _validate_tiktok_response(payload, strict=args.strict_error)
            print(_format_json(payload))
            return 0

        if args.command == "upload-file":
            payload = upload_file_chunks(
                upload_url=_require_value("upload_url", args.upload_url),
                file_path=Path(args.file).expanduser().resolve(),
                chunk_size=args.chunk_size,
                mime_type=args.mime_type,
            )
            print(_format_json(payload))
            return 0

        raise ValueError(f"Unsupported command: {args.command}")
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
