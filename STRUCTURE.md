# AI Empire - Repository Structure

## 📁 Directory Organization

This repository follows a standardized structure for clarity and automation.

```
AIEmpire-Core/
├── .github/                    # GitHub configuration
│   ├── ISSUE_TEMPLATE/        # Issue templates (Atomic Task, Bug, Feature, Revenue)
│   ├── workflows/             # CI/CD pipelines
│   │   ├── ci.yml            # Lint, test, security scan
│   │   ├── release.yml       # Automated releases
│   │   └── nightly.yml       # Health checks
│   ├── labels.yml            # Label definitions
│   └── PULL_REQUEST_TEMPLATE.md
│
├── apps/                      # Standalone applications
│   └── (future: web apps, dashboards)
│
├── services/                  # Backend services & APIs
│   └── (future: API services, workers)
│
├── agents/                    # AI agent configurations
│   └── (future: agent prompts, policies, roles)
│
├── infra/                     # Infrastructure as code
│   ├── docker-compose.*.yaml # Docker configurations
│   └── (future: Terraform, K8s)
│
├── docs/                      # Documentation
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── CHATGPT_TASKS.md
│   └── runbooks/             # Operational guides
│       ├── infrastructure/   # Docker, services
│       ├── troubleshooting/  # Problem resolution
│       ├── monitoring/       # Health checks
│       └── security/         # Security procedures
│
├── playbooks/                 # Business process guides
│   ├── sales/                # Sales strategies
│   ├── customer-success/     # Customer engagement
│   ├── growth/               # Marketing & growth
│   └── operations/           # Business operations
│
├── templates/                 # Reusable templates
│   └── (future: email sequences, packages)
│
├── crm/                      # CRM system
│   ├── server.js
│   └── package.json
│
├── x-lead-machine/           # X/Twitter automation
│   ├── post_generator.py
│   └── viral_reply_generator.py
│
├── kimi-swarm/               # 100k agent swarm
│   ├── swarm_100k.py
│   └── github_scanner_100k.py
│
├── atomic-reactor/           # Task orchestration
│   ├── run_tasks.py
│   └── tasks/
│
├── gold-nuggets/             # Insights & discoveries
│   └── *.md
│
├── openclaw-config/          # OpenClaw configuration
│   └── (configs, agents)
│
├── systems/                  # Legacy infrastructure
│   └── docker-compose.yaml
│
├── .env.example              # Environment template
├── .gitignore               # Git ignore rules
├── CONTRIBUTING.md          # Contribution guidelines
├── SECURITY.md              # Security policy
├── README.md                # This file
└── VERSION                  # Version number
```

## 🏷️ Labels & Routing

Issues are automatically labeled for routing to appropriate systems:

### Category Labels
- `code` - Code implementation
- `docs` - Documentation
- `research` - Research tasks
- `ops` - Operations
- `security` - Security issues
- `growth` - Growth initiatives
- `revenue` - Revenue opportunities

### Priority Labels
- `P0` - Critical (blocking)
- `P1` - High (important)
- `P2` - Medium (nice-to-have)

### Model Routing
- `claude-opus` - Premium quality tasks
- `claude-sonnet` - Balanced tasks
- `claude-haiku` - Fast tasks
- `kimi` - Cost-effective tasks
- `ollama` - Local/free tasks

## 🔄 Workflow

### 1. Create Issue
Use issue templates for consistency:
- 🎯 **Atomic Task** - Development tasks
- 🐛 **Bug Report** - Bug fixes
- ✨ **Feature Request** - New features
- 💰 **Revenue Opportunity** - Revenue ideas

### 2. Work in Branch
```bash
git checkout -b feature/your-feature
# Make changes
git commit -m "feat: add new feature"
```

### 3. Create Pull Request
Use PR template, include:
- Problem description
- Solution approach
- Risk assessment
- Tests & verification
- Rollback plan

### 4. CI/CD Pipeline
Automatic checks:
- ✅ Lint code
- ✅ Run tests
- ✅ Security scan
- ✅ Build validation

### 5. Review & Merge
After approval:
- Merge to main
- Automatic release (on tags)
- Changelog generation

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/mauricepfeifer-ctrl/AIEmpire-Core.git
cd AIEmpire-Core

# Copy environment template
cp .env.example .env
# Edit .env with your values

# Start CRM
cd crm && npm install && node server.js

# Start Kimi Swarm
cd kimi-swarm
python3 -m venv venv && source venv/bin/activate
pip install aiohttp
python3 github_scanner_100k.py

# Start Docker services
cd infra
docker compose -f docker-compose.systems.yaml up -d
```

## 📊 Components

| Component | Status | Purpose |
|-----------|--------|---------|
| CRM V2 | ✅ | Lead management (BANT scoring) |
| X Lead Machine | ✅ | Twitter automation |
| Kimi Swarm | ✅ | 100k agent system |
| Atomic Reactor | ✅ | Task orchestration |
| OpenClaw | ✅ | AI agent platform |

## 🛠️ Tech Stack

- **LLMs**: Claude (Opus/Sonnet/Haiku), Kimi, Ollama
- **Backend**: Node.js, Python, FastAPI
- **Database**: SQLite, Redis, PostgreSQL
- **Automation**: n8n, Docker
- **Frontend**: Tailwind CSS

## 💰 Revenue Model

### Cost Tiers
```
Tier 1 (FREE):     Ollama local       → 95% of tasks
Tier 2 (CHEAP):    Kimi/Moonshot      → 4% of tasks
Tier 3 (QUALITY):  Claude Haiku       → 0.9% of tasks
Tier 4 (PREMIUM):  Claude Opus        → 0.1% of tasks
```

### Revenue Targets
- **Month 1**: €5k (First clients)
- **Month 3**: €20k (Recurring)
- **Month 6**: €50k (Scale)
- **Year 1**: €100k+ MRR

## 🔒 Security

- Never commit secrets (use `.env`)
- Use `.env.example` as template
- Follow security policy in `SECURITY.md`
- Automated secret scanning in CI

## 📚 Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[SECURITY.md](SECURITY.md)** - Security practices
- **[docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)** - System design
- **[playbooks/](playbooks/)** - Business playbooks
- **[docs/runbooks/](docs/runbooks/)** - Operational guides

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Workflow guidelines
- PR requirements
- Commit conventions
- Testing procedures

## 📈 Tracking Progress

- **Issues** - Individual tasks
- **Pull Requests** - Code changes
- **Projects** - Strategic initiatives
- **Releases** - Version milestones

## 👤 Author

**Maurice Pfeifer** - Elektrotechnikmeister, AI Empire Builder
- GitHub: [@mauricepfeifer-ctrl](https://github.com/mauricepfeifer-ctrl)
- Building towards 100M€ in 1-3 years
- 16+ years BMA expertise

## 📜 License

Proprietary - Maurice's AI Empire

---

**Status**: 🟢 Active Development | **Version**: 2026.02 | **Updated**: 2026-02-08
