"""
SaaS Platform API
==================
FastAPI application serving the control plane:
- Auth (JWT)
- Tenant CRUD
- Billing webhooks
- Admin dashboard API
- Health monitoring

Run:
    uvicorn saas-platform.api.main:app --host 0.0.0.0 --port 8000
"""

import asyncio
import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr

# JWT
try:
    import jwt as pyjwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

import sys
_platform_root = str(Path(__file__).parent.parent)
if _platform_root not in sys.path:
    sys.path.insert(0, _platform_root)

from config import config, PLAN_LIMITS, Plan
from tenants import TenantManager
from billing import BillingManager


# ═══════════════════════════════════════════════════════════════
# App Setup
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="AIEmpire Cloud",
    description="AI Business Automation Platform as a Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Managers
tenant_mgr = TenantManager()
billing_mgr = BillingManager()


# ═══════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════

class SignupRequest(BaseModel):
    name: str
    email: str
    company: str = ""
    plan: str = "free"

class LoginRequest(BaseModel):
    email: str
    api_key: str

class UpgradePlanRequest(BaseModel):
    plan: str

class WebhookEvent(BaseModel):
    type: str
    data: dict = {}


# ═══════════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════════

def create_jwt(tenant_id: str, email: str) -> str:
    """Create a JWT token."""
    payload = {
        "tenant_id": tenant_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=config.jwt_expiry_hours),
        "iat": datetime.utcnow(),
    }
    if JWT_AVAILABLE:
        return pyjwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)
    # Fallback: simple token
    return f"tok_{tenant_id}_{secrets.token_hex(16)}"


def verify_jwt(token: str) -> dict:
    """Verify and decode a JWT token."""
    if JWT_AVAILABLE:
        return pyjwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
    # Fallback: extract tenant_id from simple token
    parts = token.split("_")
    if len(parts) >= 2:
        return {"tenant_id": parts[1], "email": "dev@local"}
    raise HTTPException(401, "Invalid token")


async def get_current_tenant(authorization: Optional[str] = Header(None)):
    """Extract tenant from Authorization header."""
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.replace("Bearer ", "")

    # Check if it's an API key
    if token.startswith("emp_"):
        tenant = tenant_mgr.get_tenant_by_api_key(token)
        if not tenant:
            raise HTTPException(401, "Invalid API key")
        if tenant.status != "active":
            raise HTTPException(403, f"Tenant is {tenant.status}")
        return tenant

    # Otherwise it's a JWT
    try:
        payload = verify_jwt(token)
        tenant = tenant_mgr.get_tenant(payload["tenant_id"])
        if not tenant:
            raise HTTPException(401, "Tenant not found")
        return tenant
    except Exception:
        raise HTTPException(401, "Invalid token")


# ═══════════════════════════════════════════════════════════════
# Public Endpoints
# ═══════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "ok",
        "service": "aiempire-cloud",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/pricing")
async def pricing():
    """Get pricing plans."""
    plans = {}
    for plan_enum, limits in PLAN_LIMITS.items():
        plans[plan_enum.value] = {
            "name": limits["name"],
            "price_eur": limits["price_eur"],
            "agent_teams": limits["agent_teams"],
            "api_calls_monthly": limits["api_calls_monthly"],
            "storage_gb": limits["storage_gb"],
            "gemini_mirror": limits["gemini_mirror"],
            "custom_agents": limits["custom_agents"],
            "support": limits["support"],
        }
    return {"plans": plans}


@app.post("/signup")
async def signup(req: SignupRequest):
    """Create a new tenant account."""
    # Create tenant
    tenant = await tenant_mgr.create_tenant(
        name=req.company or req.name,
        owner_email=req.email,
        plan=req.plan,
    )

    # Provision resources
    provision_result = await tenant_mgr.provision_resources(tenant.tenant_id)

    # Create JWT
    token = create_jwt(tenant.tenant_id, req.email)

    return {
        "success": True,
        "tenant_id": tenant.tenant_id,
        "api_key": tenant.api_key,
        "token": token,
        "plan": tenant.plan,
        "message": f"Welcome to AIEmpire Cloud! Your API key: {tenant.api_key}",
        "dashboard_url": f"https://{config.platform_domain}/dashboard",
    }


@app.post("/login")
async def login(req: LoginRequest):
    """Login with email + API key."""
    tenant = tenant_mgr.get_tenant_by_api_key(req.api_key)
    if not tenant or tenant.owner_email != req.email:
        raise HTTPException(401, "Invalid credentials")

    token = create_jwt(tenant.tenant_id, req.email)

    return {
        "success": True,
        "tenant_id": tenant.tenant_id,
        "token": token,
        "plan": tenant.plan,
    }


# ═══════════════════════════════════════════════════════════════
# Tenant API (Authenticated)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/tenant")
async def get_tenant_info(tenant=Depends(get_current_tenant)):
    """Get current tenant info."""
    return {
        "tenant_id": tenant.tenant_id,
        "name": tenant.name,
        "plan": tenant.plan,
        "status": tenant.status,
        "api_calls_used": tenant.api_calls_this_month,
        "api_calls_limit": tenant.api_calls_limit,
        "config": tenant.config,
    }


@app.post("/api/tenant/upgrade")
async def upgrade_plan(req: UpgradePlanRequest, tenant=Depends(get_current_tenant)):
    """Upgrade tenant plan."""
    # Create checkout session for paid plans
    if req.plan != "free":
        checkout_url = await billing_mgr.create_checkout_session(
            tenant_id=tenant.tenant_id,
            plan=req.plan,
        )
        return {"checkout_url": checkout_url, "plan": req.plan}

    # Downgrade to free
    updated = await tenant_mgr.upgrade_plan(tenant.tenant_id, req.plan)
    return {"success": True, "plan": req.plan}


@app.get("/api/tenant/usage")
async def get_usage(tenant=Depends(get_current_tenant)):
    """Get tenant usage metrics."""
    return {
        "tenant_id": tenant.tenant_id,
        "period": time.strftime("%Y-%m"),
        "api_calls": {
            "used": tenant.api_calls_this_month,
            "limit": tenant.api_calls_limit,
            "remaining": max(0, tenant.api_calls_limit - tenant.api_calls_this_month)
            if tenant.api_calls_limit > 0 else -1,
        },
        "storage": {
            "used_mb": tenant.storage_used_mb,
            "limit_gb": tenant.config.get("storage_gb", 1),
        },
        "agents": {
            "active": tenant.active_agents,
            "limit": tenant.config.get("max_agents", 1),
        },
    }


# ═══════════════════════════════════════════════════════════════
# Workflow API (Tenant-Scoped)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/workflow/run")
async def run_workflow(tenant=Depends(get_current_tenant)):
    """Trigger the 5-step workflow for this tenant."""
    if not tenant_mgr.increment_api_calls(tenant.tenant_id):
        raise HTTPException(429, "API call limit exceeded. Upgrade your plan.")

    return {
        "status": "triggered",
        "tenant_id": tenant.tenant_id,
        "workflow": "5-step-compound-loop",
        "steps": ["audit", "architect", "analyst", "refinery", "compounder"],
    }


@app.post("/api/cowork/cycle")
async def run_cowork(tenant=Depends(get_current_tenant)):
    """Trigger a Cowork cycle for this tenant."""
    if not tenant_mgr.increment_api_calls(tenant.tenant_id):
        raise HTTPException(429, "API call limit exceeded. Upgrade your plan.")

    return {
        "status": "triggered",
        "tenant_id": tenant.tenant_id,
        "cycle": "observe-plan-act-reflect",
    }


@app.get("/api/status")
async def get_system_status(tenant=Depends(get_current_tenant)):
    """Get system status for this tenant."""
    tenant_dir = Path(__file__).parent.parent / "tenants" / tenant.tenant_id
    state_file = tenant_dir / "state" / "current_state.json"

    state = {}
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)

    return {
        "tenant_id": tenant.tenant_id,
        "plan": tenant.plan,
        "state": state,
        "health": "ok",
    }


# ═══════════════════════════════════════════════════════════════
# Billing Webhooks
# ═══════════════════════════════════════════════════════════════

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    result = await billing_mgr.handle_webhook(payload, signature)

    # Process actions
    action = result.get("action")
    tenant_id = result.get("tenant_id")

    if action == "provision" and tenant_id:
        await tenant_mgr.provision_resources(tenant_id)
        plan = result.get("plan", "starter")
        await tenant_mgr.upgrade_plan(tenant_id, plan)

    elif action == "suspend" and tenant_id:
        await tenant_mgr.suspend_tenant(tenant_id, "subscription_cancelled")

    return {"received": True}


# ═══════════════════════════════════════════════════════════════
# Admin API
# ═══════════════════════════════════════════════════════════════

@app.get("/admin/metrics")
async def admin_metrics(x_admin_key: Optional[str] = Header(None)):
    """Get platform metrics (admin only)."""
    admin_key = os.getenv("ADMIN_API_KEY", "admin-dev-key")
    if x_admin_key != admin_key:
        raise HTTPException(403, "Admin access required")

    platform_metrics = tenant_mgr.get_metrics()
    revenue_metrics = billing_mgr.get_revenue_metrics()

    return {
        **platform_metrics,
        **revenue_metrics,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/admin/tenants")
async def admin_list_tenants(
    status: Optional[str] = None,
    plan: Optional[str] = None,
    x_admin_key: Optional[str] = Header(None),
):
    """List all tenants (admin only)."""
    admin_key = os.getenv("ADMIN_API_KEY", "admin-dev-key")
    if x_admin_key != admin_key:
        raise HTTPException(403, "Admin access required")

    tenants = tenant_mgr.list_tenants(status=status, plan=plan)
    return {"tenants": tenants, "count": len(tenants)}
