"""
SaaS Platform Configuration
"""

import os
from dataclasses import dataclass, field
from enum import Enum


class Plan(str, Enum):
    """Subscription plans."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


PLAN_LIMITS = {
    Plan.FREE: {
        "name": "Free Trial",
        "price_eur": 0,
        "agent_teams": 1,
        "api_calls_monthly": 500,
        "storage_gb": 1,
        "gemini_mirror": False,
        "custom_agents": False,
        "support": "community",
        "trial_days": 14,
    },
    Plan.STARTER: {
        "name": "Starter",
        "price_eur": 49,
        "agent_teams": 1,
        "api_calls_monthly": 5_000,
        "storage_gb": 5,
        "gemini_mirror": False,
        "custom_agents": False,
        "support": "email",
        "stripe_price_id": os.getenv("STRIPE_PRICE_STARTER", ""),
    },
    Plan.PRO: {
        "name": "Pro",
        "price_eur": 149,
        "agent_teams": 5,
        "api_calls_monthly": 50_000,
        "storage_gb": 25,
        "gemini_mirror": True,
        "custom_agents": True,
        "support": "priority",
        "stripe_price_id": os.getenv("STRIPE_PRICE_PRO", ""),
    },
    Plan.ENTERPRISE: {
        "name": "Enterprise",
        "price_eur": 499,
        "agent_teams": -1,  # unlimited
        "api_calls_monthly": -1,  # unlimited
        "storage_gb": 100,
        "gemini_mirror": True,
        "custom_agents": True,
        "support": "dedicated",
        "stripe_price_id": os.getenv("STRIPE_PRICE_ENTERPRISE", ""),
    },
}


@dataclass
class PlatformConfig:
    """Central SaaS platform configuration."""

    # Platform
    platform_name: str = "AIEmpire Cloud"
    platform_domain: str = os.getenv("PLATFORM_DOMAIN", "app.aiempire.cloud")
    platform_port: int = int(os.getenv("PLATFORM_PORT", "8000"))
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Database (control plane)
    db_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://empire_admin:empire@localhost:5432/empire_saas"
    )

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Auth
    jwt_secret: str = os.getenv("JWT_SECRET", "CHANGE-ME-IN-PRODUCTION")
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Stripe
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_publishable_key: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

    # Tenant provisioning
    tenant_namespace_prefix: str = "empire-tenant"
    tenant_db_prefix: str = "tenant_"
    max_tenants: int = 1000

    # Cloud
    gcp_project: str = os.getenv("GCP_PROJECT_ID", "aiempire-core")
    gcp_region: str = os.getenv("GCP_REGION", "europe-west1")

    # Limits
    max_request_size_mb: int = 10
    rate_limit_per_minute: int = 60

    # AI Model defaults
    default_ollama_model: str = "phi:q4"
    default_gemini_model: str = "gemini-2.0-flash"


config = PlatformConfig()
