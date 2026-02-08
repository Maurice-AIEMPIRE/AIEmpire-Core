CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE,
    role VARCHAR(50),
    tasks_completed INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE revenue_events (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    amount_eur FLOAT,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE task_executions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100),
    task_type VARCHAR(100),
    status VARCHAR(50),
    executed_at TIMESTAMP DEFAULT NOW()
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO autopilot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO autopilot;
