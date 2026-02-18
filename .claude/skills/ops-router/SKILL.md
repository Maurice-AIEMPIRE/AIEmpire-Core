# OPS ENGINEERING — Team Coordinator (O01-O30)

## Purpose
Infrastructure, automation, CI/CD, monitoring, model management, deployment, and system health. The backbone that keeps 100 agents running reliably.

## Triggers
- System health issues
- Deployment requests
- CI/CD pipeline failures
- Infrastructure configuration changes
- Model routing optimization

## Team Structure (30 Agents)

### Core Infrastructure (O01-O03)
- **O01 Router_Engineer**: Model routing (Ollama → Kimi → Claude), cost optimization
- **O02 Health_Monitor**: CPU/RAM/disk monitoring, auto-throttling (ResourceGuard)
- **O03 Night_Run_Manager**: Overnight batch scheduling, cron jobs

### Skills & Integration (O04-O05)
- **O04 Skill_Builder**: Skill scaffolding, templates, SKILL.md generation
- **O05 MCP_Integrator**: MCP server configuration, tool wiring

### Quality & Testing (O06-O07, O21)
- **O06 CI_QA**: Tests, lint (ruff), smoke checks, compileall
- **O07 Logging_Observer**: Log aggregation, metrics, alerting
- **O21 QA_Gatekeeper**: Output gate checks (YAML headers, sources, format)

### Security & Storage (O08-O09)
- **O08 Secrets_Manager**: API keys, env variables, key rotation
- **O09 Storage_Manager**: Folder rules, archiving, cleanup

### Export & Output (O10, O15, O22)
- **O10 Export_Pipeline**: MD → PDF/DOCX bundling
- **O15 Doc_Generator**: Auto-documentation from outputs
- **O22 Template_Registry**: Output template management

### Model & Provider Management (O11-O13)
- **O11 Local_ModelOps**: Ollama model management, performance tuning
- **O12 Cloud_Providers**: OpenRouter/Groq/Moonshot configuration
- **O13 RateLimit_Manager**: Backoff, queuing, retry logic

### Orchestration (O14, O23)
- **O14 Agent_Scheduler**: Task queues, priorities, orchestration
- **O23 CLI_Toolsmith**: CLI command wrappers and utilities

### Runtime & Deploy (O16-O20)
- **O16 Repo_Structure**: Repo cleanup, naming conventions
- **O17 Python_Runtime**: venv, dependencies, packaging
- **O18 Node_Runtime**: Node.js toolchain, n8n setup
- **O19 Docker_Operator**: Docker compose, containers
- **O20 Backups**: Backup/restore strategy

### Dashboards & Telemetry (O24-O26)
- **O24 WebUI_Dashboard**: Mission control dashboard
- **O25 Telemetry**: Metrics collection, cost tracking
- **O26 Prompt_Store**: Prompt bank, versioning

### Bridge & Pipeline (O27-O28)
- **O27 Legal_Data_Bridge**: Legal outputs ↔ data index sync
- **O28 Content_Pipeline**: Batch content production pipeline

### Safety & Compliance (O29-O30)
- **O29 Safety_Compliance**: Policy guardrails, content filters
- **O30 Ops_QA**: Integration tests, ops review

## Output Locations
- `ops/configs/` — ROUTER.md, MCP.md, CI.md, SECRETS.md, STORAGE.md, EXPORT_PIPELINE.md
- `ops/health/` — HEALTH.md, MODEL_BENCH.md, TELEMETRY.md
- `ops/logs/` — LOGGING.md
- `ops/skills/` — TOOLS_TRACKER.md, SKILL_TEMPLATES.md

## Model Routing Priority
```
1. Ollama (local, free)     — 80% of tasks (qwen2.5-coder:7b/14b, deepseek-r1:7b)
2. Kimi K2.5 (Moonshot API) — 15% of tasks (complex reasoning, long context)
3. Claude (Anthropic API)   — 5% of tasks (critical decisions, code, strategy)
```

## Quality Gate
- All infrastructure changes must be tested before deploy
- Secrets must never appear in logs or committed code
- Model routing must track cost per call
- Health checks must run at minimum every 30 minutes
