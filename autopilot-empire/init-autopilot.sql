-- ═══════════════════════════════════════════════════════════════
-- AUTOPILOT EMPIRE - PostgreSQL Database Schema
-- Maurice's AI Business System - Complete Database Structure
-- Erstellt: 2026-02-08
-- ═══════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════
-- AGENTS REGISTRY - Alle AI-Agenten im System
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    parent_id INT REFERENCES agents(id),
    state VARCHAR(50) DEFAULT 'idle',
    tasks_completed INT DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    revenue_generated FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agents_role ON agents(role);
CREATE INDEX idx_agents_state ON agents(state);

-- ═══════════════════════════════════════════════════════════════
-- AGENT MEMORY - Lern- und Strategie-Speicher
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE agent_memory (
    id SERIAL PRIMARY KEY,
    agent_id INT REFERENCES agents(id),
    task_type VARCHAR(100),
    strategy VARCHAR(200),
    quality_score FLOAT,
    learning_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_memory_agent ON agent_memory(agent_id);
CREATE INDEX idx_memory_task ON agent_memory(task_type);

-- ═══════════════════════════════════════════════════════════════
-- TASK EXECUTIONS - Alle Task-Ausführungen loggen
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE task_executions (
    id SERIAL PRIMARY KEY,
    agent_id INT REFERENCES agents(id),
    task_type VARCHAR(100),
    status VARCHAR(50),
    quality_score FLOAT,
    execution_time_ms INT,
    revenue_generated FLOAT DEFAULT 0.0,
    executed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_exec_agent ON task_executions(agent_id);
CREATE INDEX idx_exec_date ON task_executions(executed_at);

-- ═══════════════════════════════════════════════════════════════
-- REVENUE EVENTS - Alle Einnahmen tracken
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE revenue_events (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    platform_id VARCHAR(255),
    amount_eur FLOAT NOT NULL,
    status VARCHAR(50),
    recorded_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP
);

CREATE INDEX idx_revenue_source ON revenue_events(source);
CREATE INDEX idx_revenue_date ON revenue_events(recorded_at);

-- ═══════════════════════════════════════════════════════════════
-- DAILY REVENUE SUMMARY - Tägliche Zusammenfassung
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE daily_revenue_summary (
    date DATE PRIMARY KEY,
    tiktok_eur FLOAT DEFAULT 0.0,
    fiverr_eur FLOAT DEFAULT 0.0,
    youtube_eur FLOAT DEFAULT 0.0,
    twitter_eur FLOAT DEFAULT 0.0,
    affiliate_eur FLOAT DEFAULT 0.0,
    total_eur FLOAT,
    target_eur FLOAT DEFAULT 100.0,
    percentage_of_target FLOAT
);

-- ═══════════════════════════════════════════════════════════════
-- GENERATED CONTENT - Alle generierten Inhalte
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE generated_content (
    id SERIAL PRIMARY KEY,
    agent_id INT REFERENCES agents(id),
    content_type VARCHAR(50),
    platform VARCHAR(50),
    content TEXT,
    viral_score INT,
    status VARCHAR(50),
    posted_at TIMESTAMP,
    views INT DEFAULT 0,
    likes INT DEFAULT 0,
    shares INT DEFAULT 0,
    revenue_from_content FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_content_agent ON generated_content(agent_id);
CREATE INDEX idx_content_platform ON generated_content(platform);
CREATE INDEX idx_content_status ON generated_content(status);

-- ═══════════════════════════════════════════════════════════════
-- FIVERR GIGS - Alle Fiverr Services
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE fiverr_gigs (
    id SERIAL PRIMARY KEY,
    gig_id VARCHAR(255) UNIQUE,
    agent_id INT REFERENCES agents(id),
    title VARCHAR(255),
    description TEXT,
    price INT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    total_orders INT DEFAULT 0,
    total_revenue_eur FLOAT DEFAULT 0.0,
    avg_rating FLOAT DEFAULT 0.0
);

CREATE INDEX idx_gigs_status ON fiverr_gigs(status);

-- ═══════════════════════════════════════════════════════════════
-- FIVERR ORDERS - Alle Bestellungen
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE fiverr_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(255) UNIQUE,
    gig_id INT REFERENCES fiverr_gigs(id),
    agent_id INT REFERENCES agents(id),
    amount_eur FLOAT,
    status VARCHAR(50),
    ordered_at TIMESTAMP,
    delivered_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_orders_status ON fiverr_orders(status);
CREATE INDEX idx_orders_date ON fiverr_orders(ordered_at);

-- ═══════════════════════════════════════════════════════════════
-- HEALTH CHECKS - System Health Monitoring
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE health_checks (
    id SERIAL PRIMARY KEY,
    overall_status VARCHAR(50),
    memory_percent FLOAT,
    cpu_percent FLOAT,
    agents_online INT,
    models_available INT,
    last_recovery TIMESTAMP,
    checked_at TIMESTAMP DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- CRITICAL EVENTS - Wichtige System-Events
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE critical_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100),
    severity VARCHAR(50),
    description TEXT,
    resolution TEXT,
    resolved_at TIMESTAMP,
    event_timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_severity ON critical_events(severity);
CREATE INDEX idx_events_resolved ON critical_events(resolved_at);

-- ═══════════════════════════════════════════════════════════════
-- OPTIMIZATIONS - Performance Improvements Log
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE optimizations (
    id SERIAL PRIMARY KEY,
    optimization_type VARCHAR(100),
    before_metric FLOAT,
    after_metric FLOAT,
    improvement_percent FLOAT,
    applied_at TIMESTAMP DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- COLLECTIVE KNOWLEDGE - Geteiltes Wissen aller Agenten
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE collective_knowledge (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(100),
    best_strategy VARCHAR(200),
    avg_quality_score FLOAT,
    num_agents_using INT,
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_knowledge_task ON collective_knowledge(task_type);

-- ═══════════════════════════════════════════════════════════════
-- ANALYTICS VIEWS - Vordefinierte Abfragen für Dashboard
-- ═══════════════════════════════════════════════════════════════

-- Daily Revenue View
CREATE VIEW daily_revenue_v AS
SELECT 
    DATE(recorded_at) as date,
    SUM(CASE WHEN source = 'tiktok' THEN amount_eur ELSE 0 END) as tiktok,
    SUM(CASE WHEN source = 'fiverr' THEN amount_eur ELSE 0 END) as fiverr,
    SUM(CASE WHEN source = 'youtube' THEN amount_eur ELSE 0 END) as youtube,
    SUM(amount_eur) as total,
    COUNT(*) as num_transactions
FROM revenue_events
WHERE status = 'confirmed' OR status = 'paid'
GROUP BY DATE(recorded_at);

-- Agent Performance View
CREATE VIEW agent_performance_v AS
SELECT 
    a.agent_id, 
    a.role,
    COUNT(te.id) as tasks_completed,
    AVG(te.quality_score) as avg_quality,
    SUM(te.revenue_generated) as total_revenue,
    COUNT(CASE WHEN te.status = 'success' THEN 1 END)::FLOAT / NULLIF(COUNT(te.id), 0) as success_rate
FROM agents a
LEFT JOIN task_executions te ON a.id = te.agent_id
GROUP BY a.id, a.agent_id, a.role;

-- Content Performance View
CREATE VIEW content_performance_v AS
SELECT 
    platform,
    content_type,
    COUNT(*) as total_posts,
    AVG(viral_score) as avg_viral_score,
    SUM(views) as total_views,
    SUM(likes) as total_likes,
    SUM(shares) as total_shares,
    SUM(revenue_from_content) as total_revenue
FROM generated_content
WHERE status = 'posted'
GROUP BY platform, content_type;

-- ═══════════════════════════════════════════════════════════════
-- GRANT PERMISSIONS
-- ═══════════════════════════════════════════════════════════════
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO autopilot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO autopilot;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA public TO autopilot;

-- ═══════════════════════════════════════════════════════════════
-- INITIAL DATA - Seed Master Agents
-- ═══════════════════════════════════════════════════════════════
INSERT INTO agents (agent_id, role, model, state) VALUES
    ('content-master-001', 'Content Master', 'qwen2.5', 'active'),
    ('sales-master-001', 'Sales Master', 'llama3.3', 'active'),
    ('code-master-001', 'Code Master', 'deepseek-coder', 'active'),
    ('optimizer-001', 'Optimizer', 'mixtral-8x7b', 'active'),
    ('monitor-001', 'Monitor', 'neural-chat', 'active'),
    ('healer-001', 'Healer', 'openhermes', 'active'),
    ('scout-001', 'Scout', 'mixtral-8x7b', 'active');

-- ═══════════════════════════════════════════════════════════════
-- END OF SCHEMA
-- ═══════════════════════════════════════════════════════════════
