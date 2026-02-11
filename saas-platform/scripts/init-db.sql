-- AIEmpire Cloud — Database Initialization
-- Creates all required databases and extensions

-- Create databases
CREATE DATABASE empire;
CREATE DATABASE n8n;

-- Connect to empire_saas and set up
\c empire_saas;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Tenants table
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    owner_email VARCHAR(256) NOT NULL,
    plan VARCHAR(32) DEFAULT 'free',
    status VARCHAR(32) DEFAULT 'pending',
    api_key_hash VARCHAR(128),
    stripe_customer_id VARCHAR(128),
    stripe_subscription_id VARCHAR(128),
    config JSONB DEFAULT '{}',
    api_calls_this_month INTEGER DEFAULT 0,
    api_calls_limit INTEGER DEFAULT 500,
    storage_used_mb FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tenants_email ON tenants(owner_email);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_plan ON tenants(plan);
CREATE INDEX idx_tenants_api_key ON tenants(api_key_hash);

-- API usage log
CREATE TABLE IF NOT EXISTS api_usage (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) REFERENCES tenants(tenant_id),
    endpoint VARCHAR(256),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms FLOAT,
    tokens_used INTEGER DEFAULT 0,
    model_used VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_tenant ON api_usage(tenant_id);
CREATE INDEX idx_usage_created ON api_usage(created_at);

-- Billing events
CREATE TABLE IF NOT EXISTS billing_events (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) REFERENCES tenants(tenant_id),
    event_type VARCHAR(64),
    amount_eur NUMERIC(10,2),
    stripe_event_id VARCHAR(128),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow state (per-tenant)
CREATE TABLE IF NOT EXISTS workflow_state (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) REFERENCES tenants(tenant_id),
    step VARCHAR(32),
    status VARCHAR(32),
    result JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_workflow_tenant ON workflow_state(tenant_id);

-- Knowledge items (per-tenant)
CREATE TABLE IF NOT EXISTS knowledge_items (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) REFERENCES tenants(tenant_id),
    name VARCHAR(256),
    summary TEXT,
    tags TEXT[],
    confidence FLOAT DEFAULT 0.8,
    status VARCHAR(32) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ki_tenant ON knowledge_items(tenant_id);
CREATE INDEX idx_ki_tags ON knowledge_items USING gin(tags);

-- Agent conversations (per-tenant)
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) REFERENCES tenants(tenant_id),
    conv_id VARCHAR(128),
    title VARCHAR(256),
    agent VARCHAR(64),
    status VARCHAR(32) DEFAULT 'active',
    summary TEXT,
    message_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE INDEX idx_conv_tenant ON conversations(tenant_id);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) REFERENCES tenants(tenant_id),
    source VARCHAR(64),
    message TEXT,
    priority VARCHAR(16) DEFAULT 'normal',
    category VARCHAR(32) DEFAULT 'info',
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notif_tenant ON notifications(tenant_id);
CREATE INDEX idx_notif_unread ON notifications(tenant_id, read) WHERE read = FALSE;

-- Grant empire_admin full access
GRANT ALL ON ALL TABLES IN SCHEMA public TO empire_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO empire_admin;

-- Connect to empire DB
\c empire;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
