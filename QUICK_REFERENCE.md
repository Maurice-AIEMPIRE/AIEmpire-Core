# 🚀 AIEmpire-Core - Quick Reference Guide

> Schnellzugriff auf alle wichtigen Commands & Informationen

---

## ⚡ Wichtigste Commands

### CRM starten
\`\`\`bash
cd ~/AIEmpire-Core/crm && npm install && node server.js
# → http://localhost:3500
\`\`\`

### X Posts generieren
\`\`\`bash
cd ~/AIEmpire-Core/x-lead-machine && python3 post_generator.py
\`\`\`

### Kimi Swarm aktivieren
\`\`\`bash
cd ~/AIEmpire-Core/kimi-swarm
python3 -m venv venv && source venv/bin/activate
pip install aiohttp && python3 github_scanner_100k.py
\`\`\`

### Atomic Reactor Tasks
\`\`\`bash
cd ~/AIEmpire-Core/atomic-reactor && python3 run_tasks.py
\`\`\`

---

## 📁 Wichtigste Dateien

| Datei | Zweck | Size |
|-------|-------|------|
| `COMPLETE_STRUCTURE.md` | Vollständige Struktur-Doku | 16KB |
| `COPILOT_BRIEFING.md` | System Briefing | 6KB |
| `README.md` | Projekt Overview | 2.7KB |
| `crm/server.js` | CRM Server | 7KB |
| `x-lead-machine/READY_TO_POST.md` | 7 fertige Posts | - |
| `gold-nuggets/GOLD_OPENCLAW_MASTERPLAN_2026-02-08.md` | ⭐ Strategy | - |

---

## 🎯 Schnell-Navigation

### Komponenten
- **CRM:** `/crm/` - Lead Management
- **X Machine:** `/x-lead-machine/` - Twitter Automation
- **Swarm:** `/kimi-swarm/` - 100K Agent System
- **Reactor:** `/atomic-reactor/` - Task Orchestration
- **Gold:** `/gold-nuggets/` - Strategien & Insights
- **Config:** `/openclaw-config/` - AI Agent Setup
- **Docs:** `/docs/` - Dokumentation

### Strategische Docs
- **Monetization:** `gold-nuggets/MONETIZATION_REPORT_2026-02-08.md`
- **OpenClaw Plan:** `gold-nuggets/GOLD_OPENCLAW_MASTERPLAN_2026-02-08.md`
- **Business Plan:** `docs/BUSINESSPLAN_IST_2026-02-08.md`

---

## 🔑 Environment Variables

\`\`\`bash
# In ~/.zshrc:
export MOONSHOT_API_KEY="sk-..."
export X_API_KEY="..."
export X_API_SECRET="..."
\`\`\`

Nach Änderungen: `source ~/.zshrc`

---

## 📊 Ports & Services

| Service | Port | Command |
|---------|------|---------|
| CRM | 3500 | `cd crm && node server.js` |
| Ollama | 11434 | `ollama serve` |
| OpenClaw | 18789 | (LaunchAgent) |
| Redis | 6379 | `brew services start redis` |
| PostgreSQL | 5432 | `brew services start postgresql@16` |

---

## 💰 Revenue Targets

| Timeline | Target | Focus |
|----------|--------|-------|
| Diese Woche | 2-3K EUR | Gumroad + Fiverr |
| Monat 1 | 25K EUR | Content + Services |
| Monat 3 | 90K EUR | Full Automation |
| Jahr 1 | 500K+ EUR | Scale |

---

## 🛠️ Common Tasks

### Git
\`\`\`bash
git status
git add .
git commit -m "Update"
git push origin main
\`\`\`

### Python Venv
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

### NPM
\`\`\`bash
npm install
npm start
npm run dev
\`\`\`

### Docker
\`\`\`bash
docker-compose up -d
docker-compose down
docker-compose logs -f
\`\`\`

---

## 📞 Links

- **GitHub:** https://github.com/mauricepfeifer-ctrl/AIEmpire-Core
- **OpenClaw:** https://openclaw.com
- **Kimi API:** https://platform.moonshot.cn

---

*Updated: 2026-02-08*
