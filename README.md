# 🏰 AI EMPIRE - Maurice's Complete System

> 100 Mio € in 1-3 Jahren - Alles automatisiert mit AI

[![CI Pipeline](https://github.com/mauricepfeifer-ctrl/AIEmpire-Core/actions/workflows/ci.yml/badge.svg)](https://github.com/mauricepfeifer-ctrl/AIEmpire-Core/actions)
[![Release](https://img.shields.io/github/v/release/mauricepfeifer-ctrl/AIEmpire-Core)](https://github.com/mauricepfeifer-ctrl/AIEmpire-Core/releases)

## 📊 Overview

| Component | Status | Purpose |
|-----------|--------|---------|
| X Lead Machine | ✅ | Automatisierte Lead-Gen auf X/Twitter |
| CRM V2 | ✅ | BANT-basiertes Lead Management |
| Kimi Swarm | ✅ | 100.000 Agents für Bulk-Tasks |
| Atomic Reactor | ✅ | Task Orchestration + Docker |
| Gold Nuggets | ✅ | Wertvolle Insights extrahiert |

**🆕 New: GitHub Workflow Optimization**
- ✅ Atomic Task Templates
- ✅ CI/CD Pipeline
- ✅ Automated Security Scanning
- ✅ Release Management

---

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- Git

### Setup

```bash
# 1. Clone & Setup Environment
git clone https://github.com/mauricepfeifer-ctrl/AIEmpire-Core.git
cd AIEmpire-Core
cp .env.example .env
# Edit .env with your API keys

# 2. Start Infrastructure
cd infra
docker compose -f docker-compose.systems.yaml up -d

# 3. Start CRM
cd ../crm && npm install && node server.js
# → http://localhost:3500

# 4. Kimi Swarm aktivieren
cd ../kimi-swarm
python3 -m venv venv && source venv/bin/activate
pip install aiohttp
python3 github_scanner_100k.py

# 5. X Content generieren
cd ../x-lead-machine
python3 post_generator.py
```

---

## 📁 Structure

```
AIEmpire-Core/
├── .github/               # 🔧 GitHub Workflows & Templates
│   ├── ISSUE_TEMPLATE/   # Atomic Task, Bug, Feature, Revenue
│   ├── workflows/        # CI/CD Pipelines
│   └── labels.yml        # Label configuration
├── apps/                  # 🖥️ Standalone Applications
├── services/              # ⚙️ Backend Services & APIs
├── agents/                # 🤖 AI Agent Configurations
├── infra/                 # 🏗️ Infrastructure (Docker, etc.)
├── docs/                  # 📚 Documentation
│   └── runbooks/         # Operational guides
├── playbooks/             # 📖 Business Playbooks
│   └── sales/            # Sales strategies
├── templates/             # 📝 Reusable Templates
├── crm/                   # 📋 CRM System
├── x-lead-machine/        # 🐦 X/Twitter Automation
├── kimi-swarm/            # 🤖 100k Agent Swarm
├── atomic-reactor/        # ⚛️ Task Orchestration
├── gold-nuggets/          # 💰 Insights & Discoveries
└── systems/               # 🔧 Legacy Infrastructure
```

**📖 Detailed Documentation:**
- [STRUCTURE.md](STRUCTURE.md) - Complete directory overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- [SECURITY.md](SECURITY.md) - Security practices

---

## 💰 Gold Nuggets (Top 5)

| Repo | Rating | Action |
|------|--------|--------|
| openai/openai-cookbook | 9/10 | Study |
| microsoft/playwright | 9/10 | Study + Monetize |
| langchain-ai/langchain | 8/10 | Study |
| langgenius/dify | 8/10 | Study |
| langflow-ai/langflow | 8/10 | Clone + Study |

---

## 🛠️ Tech Stack

- **LLMs:** Claude (Opus/Sonnet/Haiku), Kimi/Moonshot, Ollama
- **Backend:** Node.js, Python, FastAPI
- **Database:** SQLite, Redis, ChromaDB
- **Automation:** n8n, Docker
- **Frontend:** Tailwind CSS

---

## 📈 Cost Model

```
Tier 1 (FREE):     Ollama local       → 95% of tasks
Tier 2 (CHEAP):    Kimi/Moonshot      → 4% of tasks
Tier 3 (QUALITY):  Claude Haiku       → 0.9%
Tier 4 (PREMIUM):  Claude Opus        → 0.1%
```

---

## 🎯 Revenue Targets

- Month 1: €5k (First clients)
- Month 3: €20k (Recurring)
- Month 6: €50k (Scale)
- Year 1: €100k+ MRR

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

### Workflow
1. Create an Issue using our templates
2. Fork and create a branch
3. Make your changes
4. Submit a Pull Request
5. Automated CI/CD checks
6. Review and merge

### Issue Templates
- 🎯 **Atomic Task** - Small, focused tasks
- 🐛 **Bug Report** - Report issues
- ✨ **Feature Request** - Suggest features
- 💰 **Revenue Opportunity** - Revenue ideas

---

## 🔒 Security

Security is critical. Please read our [Security Policy](SECURITY.md).

- Never commit secrets
- Use `.env` for credentials
- Report vulnerabilities responsibly
- Automated security scanning in CI

---

## 👤 Author

**Maurice Pfeifer** - Elektrotechnikmeister mit 16 Jahren BMA-Expertise
- GitHub: [@mauricepfeifer-ctrl](https://github.com/mauricepfeifer-ctrl)
- Building the AI Empire towards 100M€
- Automating everything with AI

---

## 📜 License

Proprietary - Maurice's AI Empire

---

**Status**: 🟢 Active Development | **Version**: 2026.02 | **Last Updated**: 2026-02-08
