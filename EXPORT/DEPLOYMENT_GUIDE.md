# AIEmpire-Core 2.0 — Deployment Guide

## Quick Start

### Voraussetzungen
- Python 3.9+
- Docker (optional)
- 20 GB freier Speicherplatz
- macOS/Linux (getestet auf Darwin 25.2.0)

### Installation

1. **Klone das Repository**
   ```bash
   git clone <repo>
   cd AIEmpire-Core__codex
   ```

2. **Starte Auto-Setup**
   ```bash
   python3 AUTOPILOT.py full_autopilot
   ```

3. **Starte Infrastructure**
   ```bash
   # Terminal 1: Ollama
   ollama serve

   # Terminal 2: Redis
   redis-server

   # Terminal 3: PostgreSQL (falls nicht systemwide)
   pg_ctl -D /usr/local/var/postgres start
   ```

4. **Starte Main Application**
   ```bash
   python3 empire_engine.py auto
   ```

## System Overview

### Backend Architecture
- **Empire Engine** (Hauptorchestrator)
- **Antigravity** (26 Module für Code-Qualität)
- **Workflow System** (n8n Integration)
- **Brain System** (7 AI-Brains)
- **CRM** (Lead-Management)

### Revenue Streams
1. Gumroad (Digital Products)
2. Fiverr/Upwork (AI Services)
3. BMA + AI Consulting
4. Twitter/TikTok Lead Generation
5. Community (Discord/Telegram)

### Monitoring
- 5 LaunchAgents aktiv
- Auto-Repair bei Fehlern
- Crash Recovery systemweit
- Daily Health Checks

## API Endpoints

| Endpunkt | Port | Funktion |
|----------|------|----------|
| empire_engine.py | - | Main orchestrator |
| n8n | 5678 | Workflow automation |
| CRM | 3500 | Lead management |
| Ollama | 11434 | LLM inference |
| Redis | 6379 | Cache layer |
| PostgreSQL | 5432 | Data storage |

## Troubleshooting

### Disk Space voll
```bash
python3 AUTOPILOT.py fix_all
```

### n8n API Key fehlt
1. Gehe zu http://localhost:5678
2. Settings → API → Create Key
3. Speichere in ~/.zshrc

### Ollama Models werden nicht geladen
```bash
ollama pull qwen2.5-coder:7b
ollama pull codellama:7b
ollama pull mistral:7b
```

## Support
- Issues: GitHub Issues
- Docs: /docs/
- Knowledge Store: ~/.openclaw/workspace/ai-empire/

---
Generated: 2026-02-11T18:35:19.534967
