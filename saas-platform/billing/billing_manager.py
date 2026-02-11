"""
Stripe Billing Integration
============================
Handles subscriptions, metering, invoices, and webhooks.

Usage:
    billing = BillingManager()
    checkout_url = await billing.create_checkout_session(tenant_id, plan="pro")
    await billing.handle_webhook(payload, signature)
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional

# Stripe SDK (optional - works without it in dev mode)
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

import sys
_platform_root = str(Path(__file__).parent.parent)
if _platform_root not in sys.path:
    sys.path.insert(0, _platform_root)

from config import config, PLAN_LIMITS, Plan


BILLING_DIR = Path(__file__).parent
BILLING_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Invoice:
    """A billing invoice."""
    invoice_id: str
    tenant_id: str
    amount_eur: float
    plan: str
    status: str = "pending"  # pending, paid, failed, refunded
    stripe_invoice_id: str = ""
    created_at: str = ""
    paid_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%S")


class BillingManager:
    """Manages Stripe billing for tenants."""

    def __init__(self):
        if STRIPE_AVAILABLE and config.stripe_secret_key:
            stripe.api_key = config.stripe_secret_key
        self.invoices_dir = BILLING_DIR / "invoices"
        self.invoices_dir.mkdir(exist_ok=True)

    async def create_customer(self, tenant_id: str, email: str, name: str) -> str:
        """Create a Stripe customer for a tenant."""
        if not STRIPE_AVAILABLE or not config.stripe_secret_key:
            # Dev mode: return mock customer ID
            return f"cus_mock_{tenant_id[:16]}"

        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"tenant_id": tenant_id},
        )
        return customer.id

    async def create_checkout_session(
        self,
        tenant_id: str,
        plan: str,
        customer_id: str = "",
        success_url: str = "",
        cancel_url: str = "",
    ) -> str:
        """Create a Stripe checkout session. Returns checkout URL."""
        plan_info = PLAN_LIMITS.get(Plan(plan))
        if not plan_info:
            return ""

        price_id = plan_info.get("stripe_price_id", "")

        if not STRIPE_AVAILABLE or not config.stripe_secret_key or not price_id:
            # Dev mode: return mock URL
            return f"https://checkout.stripe.com/mock/{tenant_id}/{plan}"

        base_url = f"https://{config.platform_domain}"
        session = stripe.checkout.Session.create(
            customer=customer_id or None,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url or f"{base_url}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url or f"{base_url}/pricing",
            metadata={"tenant_id": tenant_id, "plan": plan},
        )
        return session.url

    async def create_subscription(
        self,
        customer_id: str,
        plan: str,
        tenant_id: str,
    ) -> dict:
        """Create a subscription directly (for API-driven flows)."""
        plan_info = PLAN_LIMITS.get(Plan(plan))
        if not plan_info:
            return {"error": f"Unknown plan: {plan}"}

        price_id = plan_info.get("stripe_price_id", "")

        if not STRIPE_AVAILABLE or not config.stripe_secret_key or not price_id:
            return {
                "subscription_id": f"sub_mock_{tenant_id[:16]}",
                "status": "active",
                "plan": plan,
                "mock": True,
            }

        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            metadata={"tenant_id": tenant_id, "plan": plan},
        )
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "plan": plan,
        }

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription at period end."""
        if not STRIPE_AVAILABLE or not config.stripe_secret_key:
            return True

        if subscription_id.startswith("sub_mock"):
            return True

        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )
        return True

    async def report_usage(self, tenant_id: str, api_calls: int) -> bool:
        """Report metered usage to Stripe (for usage-based billing)."""
        # Store locally for now
        usage_file = self.invoices_dir / f"usage_{tenant_id}.json"
        usage = {}
        if usage_file.exists():
            with open(usage_file) as f:
                usage = json.load(f)

        month = time.strftime("%Y-%m")
        usage[month] = usage.get(month, 0) + api_calls

        with open(usage_file, "w") as f:
            json.dump(usage, f, indent=2)

        return True

    async def handle_webhook(self, payload: bytes, signature: str) -> dict:
        """
        Handle Stripe webhook events.

        Events we care about:
        - checkout.session.completed → Provision tenant
        - invoice.paid → Activate/renew
        - invoice.payment_failed → Warn tenant
        - customer.subscription.deleted → Suspend tenant
        """
        if not STRIPE_AVAILABLE or not config.stripe_webhook_secret:
            # Dev mode: parse as JSON directly
            event = json.loads(payload)
            return {"status": "dev_mode", "event_type": event.get("type")}

        event = stripe.Webhook.construct_event(
            payload, signature, config.stripe_webhook_secret
        )

        event_type = event["type"]
        data = event["data"]["object"]

        result = {"event_type": event_type}

        if event_type == "checkout.session.completed":
            tenant_id = data.get("metadata", {}).get("tenant_id")
            plan = data.get("metadata", {}).get("plan", "starter")
            result["action"] = "provision"
            result["tenant_id"] = tenant_id
            result["plan"] = plan
            # Actual provisioning done by caller

        elif event_type == "invoice.paid":
            customer_id = data.get("customer")
            result["action"] = "activate"
            result["customer_id"] = customer_id

        elif event_type == "invoice.payment_failed":
            customer_id = data.get("customer")
            result["action"] = "warn"
            result["customer_id"] = customer_id

        elif event_type == "customer.subscription.deleted":
            tenant_id = data.get("metadata", {}).get("tenant_id")
            result["action"] = "suspend"
            result["tenant_id"] = tenant_id

        return result

    def get_revenue_metrics(self) -> dict:
        """Calculate revenue metrics from local invoice data."""
        total_mrr = 0
        active_subs = 0

        # Read from tenant files
        tenants_dir = Path(__file__).parent / "tenants"
        plan_prices = {
            "free": 0, "starter": 49, "pro": 149, "enterprise": 499,
        }

        for path in tenants_dir.rglob("tenant.json"):
            with open(path) as f:
                data = json.load(f)
            if data.get("status") == "active":
                plan = data.get("plan", "free")
                total_mrr += plan_prices.get(plan, 0)
                if plan != "free":
                    active_subs += 1

        return {
            "mrr_eur": total_mrr,
            "arr_eur": total_mrr * 12,
            "active_subscriptions": active_subs,
            "stripe_connected": bool(config.stripe_secret_key),
        }
