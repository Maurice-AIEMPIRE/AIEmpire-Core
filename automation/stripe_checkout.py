from __future__ import annotations

import argparse
import base64
import json
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List


STRIPE_CHECKOUT_SESSION_URL = "https://api.stripe.com/v1/checkout/sessions"


def _auth_header(secret_key: str) -> str:
    token = base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def _create_session(
    *,
    secret_key: str,
    success_url: str,
    cancel_url: str,
    price_id: str,
    mode: str = "payment",
    metadata: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    params: List[tuple[str, str]] = [
        ("mode", mode),
        ("success_url", success_url),
        ("cancel_url", cancel_url),
        ("line_items[0][price]", price_id),
        ("line_items[0][quantity]", "1"),
    ]
    for key, value in (metadata or {}).items():
        params.append((f"metadata[{key}]", value))

    data = urllib.parse.urlencode(params).encode("utf-8")
    headers = {
        "Authorization": _auth_header(secret_key),
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "ai-empire-stripe-checkout/1.0",
    }
    req = urllib.request.Request(STRIPE_CHECKOUT_SESSION_URL, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Stripe Checkout session URL")
    parser.add_argument("--price-id", required=True, help="Stripe price_id (e.g. price_123)")
    parser.add_argument("--success-url", required=True)
    parser.add_argument("--cancel-url", required=True)
    parser.add_argument("--mode", default="payment", choices=["payment", "subscription"])
    parser.add_argument("--metadata", default="", help="Comma separated key=value pairs")
    args = parser.parse_args()

    secret_key = str(os.environ.get("STRIPE_SECRET_KEY", "")).strip()
    if not secret_key:
        raise SystemExit("Missing STRIPE_SECRET_KEY")

    metadata: Dict[str, str] = {}
    if args.metadata:
        for part in str(args.metadata).split(","):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            k = key.strip()
            v = value.strip()
            if k:
                metadata[k] = v

    payload = _create_session(
        secret_key=secret_key,
        success_url=args.success_url,
        cancel_url=args.cancel_url,
        price_id=args.price_id,
        mode=args.mode,
        metadata=metadata,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(str(payload.get("url") or ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
