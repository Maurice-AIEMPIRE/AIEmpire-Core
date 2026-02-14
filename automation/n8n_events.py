from __future__ import annotations

import datetime as dt
import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_enabled() -> bool:
    raw = str(os.environ.get("N8N_EVENTS_ENABLED", "1")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _endpoint() -> str:
    return str(os.environ.get("N8N_EVENT_WEBHOOK_URL", "")).strip()


def post_n8n_event(
    *,
    event_type: str,
    payload: Dict[str, Any],
    source: str,
    must_succeed: bool = False,
) -> Dict[str, Any]:
    """
    Best-effort n8n webhook emitter.
    Fail-open by default: returns error payload instead of raising.
    """
    if not _is_enabled():
        return {"ok": False, "skipped": True, "reason": "n8n_disabled"}
    url = _endpoint()
    if not url:
        return {"ok": False, "skipped": True, "reason": "n8n_webhook_missing"}

    envelope = {
        "event_type": str(event_type or "").strip() or "unknown",
        "source": str(source or "").strip() or "unknown",
        "timestamp": _now_iso(),
        "payload": payload if isinstance(payload, dict) else {"value": payload},
    }
    token = str(os.environ.get("N8N_EVENT_TOKEN", "")).strip()
    timeout = int(str(os.environ.get("N8N_EVENT_TIMEOUT_SEC", "8") or "8"))
    raw = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ai-empire-n8n-events/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=raw, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=max(2, timeout)) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return {"ok": True, "status_code": int(resp.status), "body": body[:500]}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        result = {"ok": False, "error": f"http_{exc.code}", "detail": detail[:500]}
        if must_succeed:
            raise RuntimeError(f"n8n event post failed: {result}") from exc
        return result
    except Exception as exc:  # pragma: no cover
        result = {"ok": False, "error": str(exc)}
        if must_succeed:
            raise
        return result
