# LobeHub Skills - AIEmpire Core

**Version:** 1.0.0 | **Status:** ✅ Production Ready | **Skills:** 17/17

Complete LobeHub integration for AIEmpire-Core with 17 professional AI skills for legal, sales, marketing, research, and operations.

## 🚀 Quick Start

### 1. Deploy Locally
```bash
cd lobehub-skills
bash deploy.sh
```

### 2. Start Server
```bash
python -m uvicorn main:app --reload --port 8080
```

### 3. Access Skills
- API: `http://localhost:8080/api/v1/skills`
- Docs: `http://localhost:8080/docs`
- Registry: `http://localhost:8080/registry`

## 📦 Skills Catalog (17 Skills)

### Orchestration (3)
- **nucleus** - Empire Orchestrator
- **data-ops** - Data Operations Coordinator  
- **ops-router** - Operations Router

### Legal Team (10 + Warroom)
- **legal-timeline** - Timeline Builder
- **legal-evidence** - Evidence Librarian
- **legal-claims** - Claims/Defense Analyst
- **legal-opponent** - Opponent Behavior Analyst
- **legal-caselaw** - Case Law Scout
- **legal-risk** - Risk Officer
- **legal-settlement** - Settlement Strategist
- **legal-summary** - Executive Summary
- **legal-consistency** - Consistency Checker
- **legal-drafting** - Drafting Specialist
- **legal-warroom** - Warroom Coordinator

### Sales & Marketing (2)
- **sales-leadgen** - Lead Generation
- **marketing-offers** - Marketing Strategist

### Research (1)
- **research-tools** - Research Coordinator

## 📚 Files

- **deploy.sh** - Deployment script (validates all 17 skills)
- **server-integration.yaml** - Complete server configuration
- **skills-registry.json** - Centralized skill metadata
- **lobehub.config.json** - LobeHub platform config
- **DEPLOYMENT.md** - Deployment guide

## 🔗 Integration

Integrates with:
- ✅ Empire Engine (Port 8888)
- ✅ Antigravity Router (Port 9000)
- ✅ OpenClaw Agents (Port 18789)
- ✅ Claude API (Opus 4.6)

## 📊 Status

- ✅ All 17 skills validated
- ✅ Server integration configured
- ✅ Monitoring & logging enabled
- ✅ Security & RBAC setup
- ✅ Ready for LobeHub Registry

## 🚀 Deployment

```bash
# Local
bash deploy.sh

# Docker
docker pull ghcr.io/maurice-aiempire/aiempire-skills:latest

# Details
cat DEPLOYMENT.md
```

---

**Last Updated:** 2026-03-07 | **License:** MIT | **Maintained by:** AIEmpire-Core Team
