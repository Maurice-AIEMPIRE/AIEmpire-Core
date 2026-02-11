"""
Tenant Manager
===============
Manages tenant lifecycle: create, configure, suspend, delete.
Each tenant gets isolated resources (DB schema, Redis prefix, storage).

Usage:
    tm = TenantManager()
    tenant = await tm.create_tenant("acme-corp", owner_email="ceo@acme.com", plan="pro")
    await tm.provision_resources(tenant.tenant_id)
    status = await tm.get_tenant_status(tenant.tenant_id)
    await tm.suspend_tenant(tenant.tenant_id)
"""

import asyncio
import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional


PLATFORM_ROOT = Path(__file__).parent.parent
TENANTS_DIR = PLATFORM_ROOT / "saas-platform" / "tenants"
TENANTS_DIR.mkdir(parents=True, exist_ok=True)


class TenantStatus(str, Enum):
    PENDING = "pending"           # Created, not yet provisioned
    PROVISIONING = "provisioning" # Resources being created
    ACTIVE = "active"             # Running and accessible
    SUSPENDED = "suspended"       # Billing issue or admin action
    DELETED = "deleted"           # Marked for deletion


class TenantPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class Tenant:
    """A single tenant (customer) instance."""
    tenant_id: str
    name: str
    owner_email: str
    plan: str = TenantPlan.FREE
    status: str = TenantStatus.PENDING
    created_at: str = ""
    updated_at: str = ""
    api_key: str = ""
    api_key_hash: str = ""

    # Resource identifiers
    db_schema: str = ""
    redis_prefix: str = ""
    storage_bucket: str = ""
    cloud_run_service: str = ""

    # Usage tracking
    api_calls_this_month: int = 0
    api_calls_limit: int = 500
    storage_used_mb: float = 0.0
    active_agents: int = 0

    # Configuration
    config: dict = field(default_factory=dict)
    custom_domain: str = ""
    webhook_url: str = ""

    # Stripe
    stripe_customer_id: str = ""
    stripe_subscription_id: str = ""

    def __post_init__(self):
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        if not self.api_key:
            self.api_key = f"emp_{secrets.token_urlsafe(32)}"
            self.api_key_hash = hashlib.sha256(self.api_key.encode()).hexdigest()
        if not self.db_schema:
            self.db_schema = f"tenant_{self.tenant_id.replace('-', '_')}"
        if not self.redis_prefix:
            self.redis_prefix = f"t:{self.tenant_id}:"
        if not self.storage_bucket:
            self.storage_bucket = f"empire-tenant-{self.tenant_id}"


class TenantManager:
    """Manages the full tenant lifecycle."""

    PLAN_LIMITS = {
        TenantPlan.FREE:       {"api_calls": 500,    "agents": 1,  "storage_gb": 1,   "gemini": False},
        TenantPlan.STARTER:    {"api_calls": 5000,   "agents": 1,  "storage_gb": 5,   "gemini": False},
        TenantPlan.PRO:        {"api_calls": 50000,  "agents": 5,  "storage_gb": 25,  "gemini": True},
        TenantPlan.ENTERPRISE: {"api_calls": -1,     "agents": -1, "storage_gb": 100, "gemini": True},
    }

    def __init__(self, tenants_dir: Optional[Path] = None):
        self.tenants_dir = tenants_dir or TENANTS_DIR
        self.tenants_dir.mkdir(parents=True, exist_ok=True)

    async def create_tenant(
        self,
        name: str,
        owner_email: str,
        plan: str = TenantPlan.FREE,
    ) -> Tenant:
        """Create a new tenant."""
        # Generate unique ID
        slug = name.lower().replace(" ", "-").replace("_", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")[:30]
        tenant_id = f"{slug}-{secrets.token_hex(4)}"

        # Get plan limits
        limits = self.PLAN_LIMITS.get(plan, self.PLAN_LIMITS[TenantPlan.FREE])

        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            owner_email=owner_email,
            plan=plan,
            api_calls_limit=limits["api_calls"],
            config={
                "max_agents": limits["agents"],
                "storage_gb": limits["storage_gb"],
                "gemini_enabled": limits["gemini"],
                "ollama_model": "phi:q4",
                "workflow_interval_hours": 6,
                "cowork_interval_minutes": 30,
            },
        )

        self._save_tenant(tenant)
        return tenant

    async def provision_resources(self, tenant_id: str) -> dict:
        """
        Provision cloud resources for a tenant.
        In production, this creates:
        - Database schema
        - Redis namespace
        - Storage bucket
        - Cloud Run service
        - Agent configuration
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}

        tenant.status = TenantStatus.PROVISIONING
        self._save_tenant(tenant)

        results = {}

        # 1. Create tenant directory structure
        tenant_dir = self.tenants_dir / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        for subdir in ["state", "output", "memory", "config", "logs"]:
            (tenant_dir / subdir).mkdir(exist_ok=True)

        results["directories"] = "created"

        # 2. Create tenant-specific workflow config
        workflow_config = {
            "tenant_id": tenant_id,
            "plan": tenant.plan,
            "agents": {
                "workflow": {"enabled": True, "interval_hours": 6},
                "cowork": {"enabled": True, "interval_minutes": 30},
                "gemini_mirror": {"enabled": tenant.config.get("gemini_enabled", False)},
            },
            "model_routing": {
                "primary": "ollama",
                "fallback": "gemini" if tenant.config.get("gemini_enabled") else "ollama",
                "ollama_model": tenant.config.get("ollama_model", "phi:q4"),
            },
            "limits": {
                "api_calls_monthly": tenant.api_calls_limit,
                "max_agents": tenant.config.get("max_agents", 1),
                "storage_gb": tenant.config.get("storage_gb", 1),
            },
        }

        config_path = tenant_dir / "config" / "empire_config.json"
        with open(config_path, "w") as f:
            json.dump(workflow_config, f, indent=2)

        results["config"] = "created"

        # 3. Initialize tenant state
        initial_state = {
            "tenant_id": tenant_id,
            "status": "initialized",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "current_step": None,
            "cycle_count": 0,
            "synergy_score": 0,
            "last_workflow_run": None,
            "last_cowork_run": None,
        }

        state_path = tenant_dir / "state" / "current_state.json"
        with open(state_path, "w") as f:
            json.dump(initial_state, f, indent=2)

        results["state"] = "initialized"

        # 4. Generate docker-compose override for this tenant
        compose = self._generate_tenant_compose(tenant)
        compose_path = tenant_dir / "docker-compose.tenant.yml"
        with open(compose_path, "w") as f:
            f.write(compose)

        results["compose"] = "generated"

        # Mark as active
        tenant.status = TenantStatus.ACTIVE
        tenant.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_tenant(tenant)

        results["status"] = "active"
        return results

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get a tenant by ID."""
        meta_path = self.tenants_dir / tenant_id / "tenant.json"
        if not meta_path.exists():
            # Also check flat file
            meta_path = self.tenants_dir / f"{tenant_id}.json"
            if not meta_path.exists():
                return None

        with open(meta_path) as f:
            data = json.load(f)
        return Tenant(**data)

    def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Find tenant by API key hash."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        for path in self.tenants_dir.rglob("tenant.json"):
            with open(path) as f:
                data = json.load(f)
            if data.get("api_key_hash") == key_hash:
                return Tenant(**data)

        return None

    async def suspend_tenant(self, tenant_id: str, reason: str = "") -> bool:
        """Suspend a tenant (billing failure, abuse, etc.)."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.SUSPENDED
        tenant.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        tenant.config["suspend_reason"] = reason
        self._save_tenant(tenant)
        return True

    async def reactivate_tenant(self, tenant_id: str) -> bool:
        """Reactivate a suspended tenant."""
        tenant = self.get_tenant(tenant_id)
        if not tenant or tenant.status != TenantStatus.SUSPENDED:
            return False

        tenant.status = TenantStatus.ACTIVE
        tenant.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        tenant.config.pop("suspend_reason", None)
        self._save_tenant(tenant)
        return True

    async def delete_tenant(self, tenant_id: str) -> bool:
        """Mark tenant for deletion (soft delete)."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.DELETED
        tenant.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_tenant(tenant)
        return True

    async def upgrade_plan(self, tenant_id: str, new_plan: str) -> Optional[Tenant]:
        """Upgrade tenant to a new plan."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        limits = self.PLAN_LIMITS.get(new_plan)
        if not limits:
            return None

        tenant.plan = new_plan
        tenant.api_calls_limit = limits["api_calls"]
        tenant.config["max_agents"] = limits["agents"]
        tenant.config["storage_gb"] = limits["storage_gb"]
        tenant.config["gemini_enabled"] = limits["gemini"]
        tenant.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save_tenant(tenant)

        return tenant

    def increment_api_calls(self, tenant_id: str) -> bool:
        """Track API usage. Returns False if limit exceeded."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        if tenant.api_calls_limit != -1 and tenant.api_calls_this_month >= tenant.api_calls_limit:
            return False

        tenant.api_calls_this_month += 1
        self._save_tenant(tenant)
        return True

    def reset_monthly_usage(self) -> int:
        """Reset all tenant monthly counters. Run via cron on 1st of month."""
        count = 0
        for path in self.tenants_dir.rglob("tenant.json"):
            with open(path) as f:
                data = json.load(f)
            data["api_calls_this_month"] = 0
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            count += 1
        return count

    def list_tenants(
        self,
        status: Optional[str] = None,
        plan: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """List all tenants with filtering."""
        tenants = []

        for path in sorted(self.tenants_dir.rglob("tenant.json")):
            with open(path) as f:
                data = json.load(f)

            if status and data.get("status") != status:
                continue
            if plan and data.get("plan") != plan:
                continue

            tenants.append({
                "tenant_id": data["tenant_id"],
                "name": data["name"],
                "owner_email": data["owner_email"],
                "plan": data.get("plan", "free"),
                "status": data.get("status", "unknown"),
                "api_calls": data.get("api_calls_this_month", 0),
                "api_limit": data.get("api_calls_limit", 0),
                "created_at": data.get("created_at", ""),
            })

            if len(tenants) >= limit:
                break

        return tenants

    def get_metrics(self) -> dict:
        """Get platform-wide metrics."""
        tenants = self.list_tenants(limit=10000)

        total = len(tenants)
        active = sum(1 for t in tenants if t["status"] == "active")
        by_plan = {}
        total_api_calls = 0

        for t in tenants:
            plan = t["plan"]
            by_plan[plan] = by_plan.get(plan, 0) + 1
            total_api_calls += t["api_calls"]

        return {
            "total_tenants": total,
            "active_tenants": active,
            "tenants_by_plan": by_plan,
            "total_api_calls_this_month": total_api_calls,
            "mrr_eur": (
                by_plan.get("starter", 0) * 49 +
                by_plan.get("pro", 0) * 149 +
                by_plan.get("enterprise", 0) * 499
            ),
        }

    def status_report(self) -> str:
        """Formatted status report."""
        metrics = self.get_metrics()
        tenants = self.list_tenants(limit=10)

        lines = [
            "=" * 60,
            "AIEMPIRE CLOUD — PLATFORM STATUS",
            "=" * 60,
            f"  Total Tenants:  {metrics['total_tenants']}",
            f"  Active:         {metrics['active_tenants']}",
            f"  MRR:            {metrics['mrr_eur']} EUR",
            f"  API Calls:      {metrics['total_api_calls_this_month']}",
            "",
            "  By Plan:",
        ]

        for plan, count in metrics.get("tenants_by_plan", {}).items():
            lines.append(f"    {plan:15s}: {count}")

        if tenants:
            lines.extend(["", "  Recent Tenants:"])
            for t in tenants[:5]:
                status_icon = {"active": "🟢", "suspended": "🔴", "pending": "🟡"}.get(t["status"], "⚪")
                lines.append(
                    f"    {status_icon} {t['tenant_id']:30s} | {t['plan']:10s} | "
                    f"{t['api_calls']}/{t['api_limit']} calls"
                )

        lines.append("=" * 60)
        return "\n".join(lines)

    def _save_tenant(self, tenant: Tenant) -> None:
        """Save tenant metadata."""
        tenant_dir = self.tenants_dir / tenant.tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        meta_path = tenant_dir / "tenant.json"

        data = asdict(tenant)
        # Never persist the raw API key after initial creation
        # Only store the hash
        if "api_key" in data and tenant.status != TenantStatus.PENDING:
            data.pop("api_key", None)

        with open(meta_path, "w") as f:
            json.dump(data, f, indent=2)

    def _generate_tenant_compose(self, tenant: Tenant) -> str:
        """Generate docker-compose for a tenant instance."""
        gemini_svc = ""
        if tenant.config.get("gemini_enabled"):
            gemini_svc = f"""
  gemini-mirror-{tenant.tenant_id}:
    image: aiempire/gemini-mirror:latest
    environment:
      - TENANT_ID={tenant.tenant_id}
      - REDIS_PREFIX={tenant.redis_prefix}
    restart: unless-stopped
    networks:
      - empire-net"""

        return f"""# Auto-generated for tenant: {tenant.tenant_id}
# Plan: {tenant.plan} | Created: {tenant.created_at}
version: "3.8"

services:
  empire-api-{tenant.tenant_id}:
    image: aiempire/empire-api:latest
    environment:
      - TENANT_ID={tenant.tenant_id}
      - DB_SCHEMA={tenant.db_schema}
      - REDIS_PREFIX={tenant.redis_prefix}
      - API_CALLS_LIMIT={tenant.api_calls_limit}
      - PLAN={tenant.plan}
    ports:
      - "0:3333"
    restart: unless-stopped
    networks:
      - empire-net

  workflow-{tenant.tenant_id}:
    image: aiempire/workflow:latest
    environment:
      - TENANT_ID={tenant.tenant_id}
      - REDIS_PREFIX={tenant.redis_prefix}
    restart: unless-stopped
    networks:
      - empire-net

  cowork-{tenant.tenant_id}:
    image: aiempire/cowork:latest
    environment:
      - TENANT_ID={tenant.tenant_id}
      - REDIS_PREFIX={tenant.redis_prefix}
      - INTERVAL=1800
    restart: unless-stopped
    networks:
      - empire-net
{gemini_svc}
networks:
  empire-net:
    external: true
"""
