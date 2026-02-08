# 🏰 AUTOPILOT EMPIRE - Complete AI Business System

> **Maurice's 24/7 Autonomous Revenue Generation System**
> Ziel: €100/Tag in 30 Tagen, dann skalieren auf €20.000+/Monat

---

## 📊 System Overview

Autopilot Empire ist ein vollständig autonomes AI-Agenten-System, das 24/7 läuft und automatisch Einnahmen generiert durch:

- **TikTok Content** (15 Videos/Tag) → €30/Tag Ziel
- **Fiverr Services** (Automatisierte Gigs & Bidding) → €70/Tag Ziel  
- **YouTube Shorts** (5 Videos/Tag)
- **Twitter Threads** (3 Threads/Tag)

**Total Target: €100/Tag** (automatisch, hands-free)

---

## 🎯 Features

### ✅ Autonomer Betrieb
- 7 Master-Agenten (Content, Sales, Code, Optimizer, Monitor, Healer, Scout)
- Selbstständige Task-Ausführung alle 15 Minuten
- Self-Healing bei Errors
- Adaptive Agent-Spawning bei Bedarf

### ✅ Collective Learning
- Agenten teilen Wissen und Best Practices
- Kontinuierliche Performance-Verbesserung
- Top-10 Strategien pro Task-Type werden gespeichert

### ✅ Lokale AI-Modelle (KOSTENLOS via Ollama)
- `mixtral-8x7b` - Strategic Decisions
- `llama3.3` - General Tasks & Sales
- `qwen2.5` - Multilingual Content Creation
- `deepseek-coder` - Code Generation
- `openhermes` - Error Recovery
- `neural-chat` - Fast Monitoring

### ✅ iPhone-Steuerung
- SSH via Tailscale (von überall)
- Dark Theme Dashboard (Touch-optimiert)
- Monitoring Dashboard (9090)
- Tmux für persistente Sessions

### ✅ Complete Stack
- **PostgreSQL** - Long-term Memory & Analytics
- **Redis** - Fast Caching & Task Queue
- **Ollama** - Local AI Models
- **FastAPI** - Agent Server & Dashboard
- **Caddy** - Reverse Proxy
- **Health Monitor** - 24/7 System Monitoring

---

## 🚀 Quick Start

### Voraussetzungen

- Mac Mini M4 (oder kompatibel)
- Docker & Docker Compose installiert
- 16+ GB RAM (für Ollama Models)
- Internetverbindung

### Installation

```bash
# 1. Repository klonen (wenn noch nicht geschehen)
git clone https://github.com/mauricepfeifer-ctrl/AIEmpire-Core.git
cd AIEmpire-Core/autopilot-empire

# 2. iPhone Remote Setup (optional aber empfohlen)
bash iphone-remote-setup.sh

# 3. Environment konfigurieren
cp .env.template .env
# .env bearbeiten und API Keys eintragen (optional)

# 4. Docker Stack starten
docker-compose up -d

# 5. Warten bis alle Services hochgefahren sind
sleep 60

# 6. Ollama Models herunterladen (beim ersten Start)
docker exec -it autopilot-ollama ollama pull mixtral-8x7b
docker exec -it autopilot-ollama ollama pull llama3.3
docker exec -it autopilot-ollama ollama pull qwen2.5
docker exec -it autopilot-ollama ollama pull deepseek-coder
docker exec -it autopilot-ollama ollama pull openhermes
docker exec -it autopilot-ollama ollama pull neural-chat

# 7. System Status prüfen
docker-compose ps
curl http://localhost:8000/health
```

### Erste Schritte

```bash
# Dashboard öffnen
open http://localhost:8000

# Monitoring öffnen
open http://localhost:9090

# Logs anschauen
docker-compose logs -f orchestrator

# System stoppen
docker-compose down

# System neu starten
docker-compose restart
```

---

## 📁 Projektstruktur

```
autopilot-empire/
├── docker-compose.yml              # Alle Docker Services
├── init-autopilot.sql              # Datenbank Schema
├── orchestrator.py                 # Master Brain (Swarm Manager)
├── agent_server.py                 # FastAPI Dashboard & API
├── Dockerfile.orchestrator         # Orchestrator Container
├── Caddyfile                       # Reverse Proxy Config
├── .env.template                   # Environment Template
├── iphone-remote-setup.sh          # iPhone Setup Script
├── requirements-orchestrator.txt   # Python Dependencies
│
├── config/
│   ├── agents.yaml                 # Agent Configuration
│   └── models.yaml                 # Model Configuration
│
├── agents/
│   ├── content_squad.py            # Content Generation Service
│   └── Dockerfile.content          # Content Service Container
│
├── monitoring/
│   ├── health_monitor.py           # 24/7 Health Monitoring
│   └── Dockerfile.monitor          # Monitor Container
│
└── data/                           # Persistent Data (wird erstellt)
    ├── logs/                       # Application Logs
    ├── postgres/                   # Database Files
    ├── models/                     # Ollama Models
    ├── redis/                      # Cache
    └── caddy/                      # Gateway Data
```

---

## 🔧 Konfiguration

### Environment Variables (.env)

Kopiere `.env.template` nach `.env` und konfiguriere:

```bash
# Obligatorisch
REVENUE_TARGET=100.0               # Tägliches Revenue-Ziel (EUR)
EXECUTION_MODE=aggressive          # aggressive | balanced | conservative
AUTO_SPAWN_AGENTS=true             # Automatisches Agent-Spawning

# Optional: Premium AI APIs (für bessere Qualität)
OPENROUTER_API_KEY=sk-or-v1-...    # Ein Key für alle Modelle
ANTHROPIC_API_KEY=sk-ant-...       # Claude Direct
OPENAI_API_KEY=sk-...              # OpenAI Direct

# Optional: Platform APIs (für Auto-Posting)
TIKTOK_API_KEY=                    # TikTok Auto-Posting
FIVERR_API_KEY=                    # Fiverr Automation
```

### Agent Configuration (config/agents.yaml)

Definiert alle 7 Master-Agenten und ihre Fähigkeiten:

- Content Master (qwen2.5)
- Sales Master (llama3.3)
- Code Master (deepseek-coder)
- Optimizer (mixtral-8x7b)
- Monitor (neural-chat)
- Healer (openhermes)
- Scout (mixtral-8x7b)

### Model Configuration (config/models.yaml)

Definiert alle verfügbaren AI-Modelle und Selection Strategy.

---

## 📱 iPhone Remote Access

### Setup

```bash
# 1. Setup-Script auf Mac ausführen
bash iphone-remote-setup.sh

# 2. iPhone Apps installieren
# - Tailscale (App Store)
# - Termius (App Store)

# 3. Tailscale verbinden (gleicher Account wie Mac)
# 4. Termius Host konfigurieren mit Tailscale IP
# 5. Vom iPhone aus verbinden und System starten
```

### iPhone Dashboard

```
Agent Dashboard:  http://[TAILSCALE-IP]:8000
Monitoring:       http://[TAILSCALE-IP]:9090
```

### Tmux für persistente Sessions

```bash
# Neue Session erstellen
tmux new -s autopilot

# Session verlassen (läuft weiter)
Ctrl+B, dann D

# Wieder verbinden
tmux attach -t autopilot

# Alle Sessions anzeigen
tmux ls
```

---

## 📊 API Endpoints

### Agent Server (Port 8000)

```
GET  /                    # iPhone Dashboard
POST /chat                # Chat mit Agent
GET  /agents              # Liste aller Agenten
GET  /models              # Liste aller Modelle
GET  /stats               # System Statistics
GET  /health              # Health Check
GET  /revenue/daily       # Tägliche Einnahmen
GET  /revenue/breakdown   # Revenue nach Source
```

### Monitoring (Port 9090)

```
GET  /                    # Monitoring Dashboard
GET  /status              # System Status (JSON)
GET  /health              # Health Check
```

---

## 🎯 System Workflow

### Hauptloop (alle 15 Min)

1. **REVENUE PHASE**
   - 3 TikTok Scripts generieren
   - 2 Fiverr Gigs erstellen
   - 1 YouTube Short
   - 1 Twitter Thread

2. **HEALTH CHECK**
   - Alle Agenten prüfen
   - System Resources monitoren
   - Database Performance
   - Ollama Models verfügbar

3. **COLLECTIVE LEARNING**
   - Best Strategies identifizieren
   - Wissen zwischen Agenten teilen
   - Top-10 Strategien speichern

4. **OPTIMIZATION** (jede Stunde)
   - Performance analysieren
   - Underperformer identifizieren
   - Bei Bedarf Helper-Agents spawnen

5. **ADAPTIVE SPAWNING**
   - Bei Revenue <70%: neue Agenten spawnen
   - Bei High Load: Worker spawnen
   - Bei Quality Drop: Optimizer aktivieren

---

## 💰 Revenue Tracking

### Database Views

```sql
-- Tägliche Einnahmen
SELECT * FROM daily_revenue_v ORDER BY date DESC LIMIT 30;

-- Agent Performance
SELECT * FROM agent_performance_v;

-- Content Performance
SELECT * FROM content_performance_v;
```

### Revenue Targets

```
TikTok:     €30/Tag
Fiverr:     €70/Tag
YouTube:    €0/Tag (später)
Twitter:    €0/Tag (später)
───────────────────────
TOTAL:      €100/Tag
```

---

## 🔍 Monitoring & Logs

### Docker Logs

```bash
# Alle Services
docker-compose logs -f

# Nur Orchestrator
docker-compose logs -f orchestrator

# Nur Content Service
docker-compose logs -f content-service

# Letzte 100 Zeilen
docker-compose logs --tail=100 orchestrator
```

### Log Files

```
data/logs/orchestrator.log    # Orchestrator Logs
data/logs/content.log          # Content Generation Logs
data/logs/monitor.log          # Monitoring Logs
```

### Health Checks

```bash
# Orchestrator
curl http://localhost:8000/health

# Monitor
curl http://localhost:9090/health

# Ollama
curl http://localhost:11434/api/tags

# Database
docker exec -it autopilot-db psql -U autopilot -c "SELECT 1"

# Redis
docker exec -it autopilot-redis redis-cli PING
```

---

## 🛠 Troubleshooting

### Problem: Ollama Models nicht verfügbar

```bash
# Models manuell herunterladen
docker exec -it autopilot-ollama ollama pull mixtral-8x7b
docker exec -it autopilot-ollama ollama pull llama3.3
docker exec -it autopilot-ollama ollama pull qwen2.5
```

### Problem: Database Connection Error

```bash
# Database Status prüfen
docker-compose ps postgres-master

# Database neu starten
docker-compose restart postgres-master

# Logs prüfen
docker-compose logs postgres-master
```

### Problem: Orchestrator startet nicht

```bash
# Logs prüfen
docker-compose logs orchestrator

# Manuell starten für Debug
docker-compose run --rm orchestrator python orchestrator.py
```

### Problem: Port bereits belegt

```bash
# Ports anpassen in docker-compose.yml
# z.B. "8001:8000" statt "8000:8000"
```

---

## 🔐 Security Best Practices

1. **API Keys nicht committen** - Immer `.env` verwenden
2. **Starke Passwörter** - In Production DB-Passwort ändern
3. **Firewall** - Nur nötige Ports öffnen
4. **Tailscale** - Für sicheren Remote-Zugriff
5. **Backups** - Regelmäßig `data/` Ordner sichern

---

## 📈 Scaling

### Horizontal Scaling

```yaml
# In docker-compose.yml
orchestrator:
  deploy:
    replicas: 3  # Mehrere Orchestrator Instances

content-service:
  deploy:
    replicas: 5  # Mehr Content Workers
```

### Vertical Scaling

```yaml
# Mehr Resources pro Container
orchestrator:
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: '2'
```

---

## 👤 Author

**Maurice** - Elektrotechnikmeister & AI Empire Builder
- 16 Jahre BMA-Expertise
- Ziel: Finanzielle Freiheit durch AI-Automation
- GitHub: @mauricepfeifer-ctrl

---

## 📜 License

Proprietary - Maurice's AI Empire

---

## 🆘 Support

Bei Fragen oder Problemen:

1. Logs prüfen: `docker-compose logs -f`
2. Health Check: `curl http://localhost:8000/health`
3. Database Check: `docker exec -it autopilot-db psql -U autopilot`
4. GitHub Issues erstellen

---

## 🎉 Nächste Schritte

1. ✅ System starten
2. ⏳ Ollama Models herunterladen (~20 Min)
3. 📊 Dashboard öffnen und überwachen
4. 📱 iPhone Remote Setup
5. 💰 Erste €100/Tag abwarten
6. 📈 Skalieren auf €20k+/Monat

**Let's build that empire! 🚀**
