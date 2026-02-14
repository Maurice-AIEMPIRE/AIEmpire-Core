from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict

from automation.n8n_events import post_n8n_event
from automation.utils.files import ensure_dir, write_json


ROOT = Path(__file__).resolve().parents[1]
EVENT_DIR = ROOT / "content_factory" / "deliverables" / "revenue" / "stripe" / "events"


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _verify_signature(payload: bytes, sig_header: str, webhook_secret: str, tolerance_sec: int = 300) -> bool:
    if not sig_header or not webhook_secret:
        return False
    parts = {}
    for chunk in sig_header.split(","):
        if "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        parts[k.strip()] = v.strip()
    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        return False
    try:
        ts = int(timestamp)
    except ValueError:
        return False
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    if abs(now - ts) > max(60, int(tolerance_sec)):
        return False
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


class StripeWebhookHandler(BaseHTTPRequestHandler):
    webhook_secret: str = ""

    def _write(self, code: int, payload: Dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        sig_header = str(self.headers.get("Stripe-Signature", ""))

        if not _verify_signature(raw, sig_header, self.webhook_secret):
            self._write(401, {"ok": False, "error": "invalid_signature"})
            return

        try:
            event = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._write(400, {"ok": False, "error": "invalid_json"})
            return

        event_id = str(event.get("id") or f"evt_{int(dt.datetime.now().timestamp())}")
        ensure_dir(EVENT_DIR)
        write_json(
            EVENT_DIR / f"{event_id}.json",
            {
                "received_at": _now_iso(),
                "headers": dict(self.headers),
                "event": event,
            },
        )
        latest = EVENT_DIR.parent / "latest_event.json"
        write_json(latest, {"received_at": _now_iso(), "event_id": event_id, "event_type": event.get("type")})
        post_n8n_event(
            event_type="stripe_webhook_received",
            source="automation.stripe_webhook_server",
            payload={
                "event_id": event_id,
                "event_type": str(event.get("type") or ""),
                "livemode": bool(event.get("livemode")),
            },
        )
        self._write(200, {"ok": True, "event_id": event_id})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Local Stripe webhook receiver with signature verification")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--secret", default=None, help="Webhook secret (or env STRIPE_WEBHOOK_SECRET)")
    args = parser.parse_args()

    webhook_secret = str(args.secret or os.environ.get("STRIPE_WEBHOOK_SECRET", "")).strip()
    if not webhook_secret:
        raise SystemExit("Missing STRIPE_WEBHOOK_SECRET")

    StripeWebhookHandler.webhook_secret = webhook_secret
    server = HTTPServer((args.host, int(args.port)), StripeWebhookHandler)
    print(f"Stripe webhook server listening on http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
