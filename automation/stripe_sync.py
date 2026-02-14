from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation.n8n_events import post_n8n_event
from automation.utils.files import ensure_dir, timestamp_id, write_json


ROOT = Path(__file__).resolve().parents[1]
STRIPE_CHARGES_URL = "https://api.stripe.com/v1/charges"
DELIVERABLES_DIR = ROOT / "content_factory" / "deliverables" / "revenue" / "stripe"


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _auth_header(secret_key: str) -> str:
    token = base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _fetch_charges(secret_key: str, *, created_gte: int, max_records: int = 200) -> List[Dict[str, Any]]:
    headers = {
        "Authorization": _auth_header(secret_key),
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "ai-empire-stripe-sync/1.0",
    }
    rows: List[Dict[str, Any]] = []
    starting_after = ""
    while len(rows) < max_records:
        page_limit = min(100, max_records - len(rows))
        params = {
            "limit": page_limit,
            "created[gte]": created_gte,
            "expand[]": "data.balance_transaction",
        }
        if starting_after:
            params["starting_after"] = starting_after
        data = urllib.parse.urlencode(params, doseq=True).encode("utf-8")
        req = urllib.request.Request(STRIPE_CHARGES_URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        page_rows = payload.get("data") if isinstance(payload, dict) else []
        if not isinstance(page_rows, list):
            break
        rows.extend([row for row in page_rows if isinstance(row, dict)])
        has_more = bool(payload.get("has_more")) if isinstance(payload, dict) else False
        if not has_more or not page_rows:
            break
        starting_after = str(page_rows[-1].get("id") or "")
        if not starting_after:
            break
    return rows


def build_revenue_snapshot(
    *,
    secret_key: str,
    lookback_hours: int = 24,
    max_records: int = 200,
) -> Dict[str, Any]:
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(hours=max(1, int(lookback_hours)))
    since_epoch = int(since.timestamp())
    charges = _fetch_charges(secret_key, created_gte=since_epoch, max_records=max_records)

    paid = [c for c in charges if bool(c.get("paid")) and str(c.get("status") or "") == "succeeded"]
    gross = 0
    refunded = 0
    fee_total = 0
    net = 0
    items: List[Dict[str, Any]] = []

    for charge in paid:
        currency = str(charge.get("currency") or "").lower()
        amount = _to_int(charge.get("amount"))
        amount_refunded = _to_int(charge.get("amount_refunded"))
        balance_tx = charge.get("balance_transaction") if isinstance(charge.get("balance_transaction"), dict) else {}
        fee = _to_int(balance_tx.get("fee"))
        net_minor = _to_int(balance_tx.get("net"))
        created_ts = _to_int(charge.get("created"))
        created_at = (
            dt.datetime.fromtimestamp(created_ts, tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")
            if created_ts > 0
            else ""
        )
        gross += amount
        refunded += amount_refunded
        fee_total += fee
        net += net_minor if net_minor else (amount - amount_refunded - fee)
        items.append(
            {
                "id": str(charge.get("id") or ""),
                "created_at": created_at,
                "currency": currency,
                "amount_minor": amount,
                "amount_refunded_minor": amount_refunded,
                "fee_minor": fee,
                "net_minor": net_minor if net_minor else (amount - amount_refunded - fee),
                "description": str(charge.get("description") or ""),
                "metadata": charge.get("metadata") if isinstance(charge.get("metadata"), dict) else {},
                "receipt_email": str(charge.get("receipt_email") or ""),
            }
        )

    items.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)

    # Convert to EUR if currency=eur; other currencies are reported separately.
    eur_items = [item for item in items if str(item.get("currency") or "") == "eur"]
    gross_eur = sum(int(item.get("amount_minor") or 0) for item in eur_items) / 100.0
    refunded_eur = sum(int(item.get("amount_refunded_minor") or 0) for item in eur_items) / 100.0
    fee_eur = sum(int(item.get("fee_minor") or 0) for item in eur_items) / 100.0
    net_eur = sum(int(item.get("net_minor") or 0) for item in eur_items) / 100.0

    return {
        "captured_at": _now_iso(),
        "lookback_hours": int(lookback_hours),
        "totals": {
            "charges_total": len(charges),
            "charges_paid": len(paid),
            "gross_minor_all": gross,
            "refunded_minor_all": refunded,
            "fee_minor_all": fee_total,
            "net_minor_all": net,
            "gross_eur": round(gross_eur, 2),
            "refunded_eur": round(refunded_eur, 2),
            "fee_eur": round(fee_eur, 2),
            "net_eur": round(net_eur, 2),
        },
        "items": items[:120],
    }


def write_snapshot(snapshot: Dict[str, Any], run_id: Optional[str] = None) -> Dict[str, str]:
    resolved_run_id = run_id or timestamp_id()
    run_dir = DELIVERABLES_DIR / resolved_run_id
    ensure_dir(run_dir)
    run_file = run_dir / "stripe_revenue.json"
    latest_file = DELIVERABLES_DIR / "latest.json"
    write_json(run_file, snapshot)
    write_json(
        latest_file,
        {
            "run_id": resolved_run_id,
            "captured_at": snapshot.get("captured_at"),
            "totals": snapshot.get("totals") or {},
            "path": str(run_file),
        },
    )
    return {"run_file": str(run_file), "latest_file": str(latest_file), "run_id": resolved_run_id}


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync real Stripe charge revenue into local deliverables")
    parser.add_argument("--lookback-hours", type=int, default=24)
    parser.add_argument("--max-records", type=int, default=200)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    secret_key = str(os.environ.get("STRIPE_SECRET_KEY", "")).strip()
    if not secret_key:
        raise SystemExit("Missing STRIPE_SECRET_KEY")

    snapshot = build_revenue_snapshot(
        secret_key=secret_key,
        lookback_hours=max(1, int(args.lookback_hours)),
        max_records=max(1, int(args.max_records)),
    )
    paths = write_snapshot(snapshot, run_id=args.run_id)
    out = {
        "status": "ok",
        "captured_at": snapshot.get("captured_at"),
        "totals": snapshot.get("totals"),
        **paths,
    }
    post_n8n_event(
        event_type="stripe_revenue_sync",
        source="automation.stripe_sync",
        payload=out,
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
