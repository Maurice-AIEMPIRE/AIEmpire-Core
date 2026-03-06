# LobeHub Skills Distribution

Complete LobeHub integration for AIEmpire-Core distributed skills platform.

## 📦 What's Inside

### Manifest Files
- **manifest.json** - Master skill definition and registry
- **skills-registry.json** - LobeHub-compatible skill registry
- **lobehub.config.json** - LobeHub configuration and deployment settings

### Skills Included

#### Legal Team (10 Skills)
- **Legal Timeline Builder** (L01) - Chronological case analysis
- **Legal Evidence Librarian** (L02) - Evidence organization and retrieval
- **Legal Claims/Defense Matrix** (L03) - Claims analysis
- **Legal Opponent Behavior** (L04) - Opponent behavior analysis
- **Legal Case Law Scout** (L04) - Precedent research
- **Legal Risk Officer** (L06) - Risk assessment
- **Legal Settlement/Negotiation** (L07) - Settlement strategy
- **Legal Executive Summary** (L10) - Case summaries
- **Legal Consistency Checker** (L09) - Argument validation
- **Legal Drafting Specialist** (L08) - Document generation

#### Sales Team (1 Skill)
- **Sales Lead Generation** (S01-S20) - Lead generation and qualification

#### Marketing Team (1 Skill)
- **Marketing Offers Specialist** (M01-M20) - Campaign design and optimization

#### Data Operations (1 Skill)
- **Data Ops Team Coordinator** (D01-D10) - Data pipeline orchestration

#### Research Team (1 Skill)
- **Research Team Coordinator** (R01-R10) - Research coordination and tool evaluation

#### Operations Team (2 Skills)
- **NUCLEUS Orchestrator** - Central task routing and orchestration
- **Operations Engineering Router** (O01-O30) - Ops task routing

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
python -m pip install --upgrade python-telegram-bot
```

### 2. Configure LobeHub
```bash
# Copy configuration
cp lobehub-skills/manifest.json .
cp lobehub-skills/lobehub.config.json .

# Verify installation
python3 << 'EOF'
import json
with open('manifest.json') as f:
    manifest = json.load(f)
    print(f"✅ LobeHub Manifest loaded: {manifest['name']}")
    print(f"   Skills: {len(manifest['skills'])}")
    print(f"   Teams: {len(manifest['teams'])}")
EOF
```

### 3. Start the Skills Server
```bash
# Using Docker
docker build -f Dockerfile.skills -t aiempire-skills:latest .
docker run -p 8080:8080 aiempire-skills:latest

# Or using Python directly
python empire_engine.py
```

### 4. Verify Telegram Integration
```bash
# Check Telegram bot status
curl -s http://localhost:8080/api/v1/integrations/telegram/status | jq

# Or test directly
python telegram_bot/bot.py
```

## 📡 Integration Points

### Telegram Bot Integration
```python
from telegram import Bot
from telegram.ext import Application

# Skills are automatically available in Telegram bot commands
# /skill <skill-id> <input>
# Example: /skill nucleus [STATUS]
```

### API Integration
```bash
# Invoke a skill via REST API
curl -X POST http://localhost:8080/api/v1/skills/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "aiempire/nucleus",
    "input": "Generate status report",
    "context": {}
  }'
```

### GitHub Actions CI/CD
The `.github/workflows/skills-publish.yml` workflow automatically:
- ✅ Validates all skill manifests
- ✅ Builds Docker images
- ✅ Publishes to GitHub Container Registry
- ✅ Tests Telegram integration
- ✅ Creates release packages

## 📊 Skill Directory Structure

```
.claude/skills/
├── nucleus/
│   ├── SKILL.md
│   └── (orchestrator config)
├── legal-timeline/
│   ├── SKILL.md
│   └── (legal team config)
├── legal-evidence/
│   ├── SKILL.md
│   └── (legal team config)
... (16 more skills)
└── ops-router/
    ├── SKILL.md
    └── (ops config)
```

## 🔧 Configuration Files

### manifest.json
Master skill definition with namespace, teams, and skill metadata.

```json
{
  "version": "1.0.0",
  "namespace": "aiempire",
  "teams": {
    "legal": { "skills": [...] },
    "sales": { "skills": [...] },
    ...
  }
}
```

### skills-registry.json
LobeHub-compatible registry with detailed skill specifications.

```json
{
  "skills": {
    "nucleus": {
      "id": "aiempire/nucleus",
      "type": "orchestrator",
      "triggers": ["[STATUS]", "[SPAWN]", ...]
    },
    ...
  }
}
```

### lobehub.config.json
Deployment configuration for distribution, integrations, and monitoring.

```json
{
  "distribution": {
    "channels": [
      { "name": "stable", "type": "github-releases" },
      { "name": "docker", "type": "docker-registry" }
    ]
  },
  "integrations": {
    "telegram": { "enabled": true },
    "github_actions": { "enabled": true }
  }
}
```

## 🌐 Distribution Channels

### GitHub Releases
```bash
# Published automatically on version tags
# Example: v1.0.0
```

### Docker Registry
```bash
# ghcr.io/maurice-aiempire/aiempire-skills:latest
docker pull ghcr.io/maurice-aiempire/aiempire-skills:latest
docker run -p 8080:8080 ghcr.io/maurice-aiempire/aiempire-skills:latest
```

### NPM (Future)
```bash
# @aiempire/skills package (coming soon)
npm install @aiempire/skills
```

## 🔐 Security

- ✅ Secret scanning for API keys, tokens
- ✅ API key rotation (90 days)
- ✅ Audit logging for all invocations
- ✅ RBAC-ready skill permissions
- ✅ Encrypted secret storage

## 📈 Monitoring & Metrics

Automatically tracked:
- Skill invocations per day/week/month
- Execution time distribution
- Error rates and types
- User satisfaction scores

View metrics:
```bash
curl http://localhost:8080/api/v1/metrics/skills
```

## 🤝 Contributing

To add a new skill:

1. Create directory: `.claude/skills/<skill-id>/`
2. Add `SKILL.md` with manifest
3. Update `manifest.json` and `skills-registry.json`
4. Push to branch `claude/setup-lobehub-skills-3xEMa`
5. GitHub Actions will validate and publish

## 📝 License

MIT License - See LICENSE file

## 👨‍💼 Author

Maurice Pfeifer - AIEmpire-Core
