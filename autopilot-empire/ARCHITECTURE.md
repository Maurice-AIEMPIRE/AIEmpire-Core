# ═══════════════════════════════════════════════════════════════
# AUTOPILOT EMPIRE - Architecture Notes
# ═══════════════════════════════════════════════════════════════

## System Architecture

Das Autopilot Empire System besteht aus mehreren Komponenten:

### Core Services (via docker-compose.yml)

1. **Ollama Master** (Port 11434)
   - Lokale AI-Modelle
   - Kostenlos, keine API Keys nötig
   - 6 Modelle: mixtral, llama3.3, qwen2.5, deepseek-coder, openhermes, neural-chat

2. **Orchestrator** (Port 8000) 
   - Master Brain des Systems
   - Verwaltet alle 7 Master-Agenten
   - Autonomer Hauptloop (alle 15 Min)
   - Collective Learning & Self-Optimization
   - Beinhaltet KEINE FastAPI/Dashboard (reines Backend)

3. **Content Service**
   - Generiert TikTok, YouTube, Twitter Content
   - Läuft 24/7 im Hintergrund
   - Nutzt qwen2.5 Model

4. **PostgreSQL** (Port 5432)
   - Long-term Memory
   - Analytics & Revenue Tracking
   - 14 Tabellen + 3 Views

5. **Redis** (Port 6379)
   - Fast Caching
   - Task Queue
   - Agent Communication

6. **Health Monitor** (Port 9090)
   - 24/7 System Monitoring
   - Dashboard unter http://localhost:9090
   - Health Checks alle 5 Minuten

7. **API Gateway** (Caddy, Port 80/443)
   - Reverse Proxy
   - Load Balancing
   - SSL Termination

### Optional: Agent Server (Standalone)

**agent_server.py** kann als separate Komponente laufen:
- FastAPI Server mit iPhone-Dashboard
- OpenRouter Integration
- 9 Agenten zur Auswahl
- 10 AI-Modelle (4 kostenlos, 6 premium)

**Start:**
```bash
python agent_server.py
# Oder mit Docker:
docker build -f Dockerfile.server -t agent-server .
docker run -p 8001:8000 agent-server
```

**Zweck:**
- Alternative zum Orchestrator für manuelle Steuerung
- Chatbot-Interface für Entwicklung/Testing
- OpenRouter/Anthropic/OpenAI Integration

## Deployment-Szenarien

### Szenario 1: Full Autopilot (Empfohlen)
```bash
docker-compose up -d
```
- Orchestrator + All Services
- 100% autonom
- Keine manuelle Interaktion nötig
- Dashboard: Monitor auf Port 9090

### Szenario 2: Autopilot + Chat Interface
```bash
# Start Autopilot
docker-compose up -d

# Start Agent Server separat
python agent_server.py  # Port 8001
```
- Autopilot läuft im Hintergrund
- Agent Server für manuelle Chats
- Beide Dashboards verfügbar

### Szenario 3: Nur Chat/Development
```bash
# Nur Ollama + DB + Redis starten
docker-compose up -d ollama-master postgres-master redis-cache

# Agent Server
python agent_server.py
```
- Kein autonomer Betrieb
- Nur für Entwicklung/Testing

## Port-Übersicht

```
11434  - Ollama API
5432   - PostgreSQL
6379   - Redis
9090   - Health Monitor Dashboard
80     - API Gateway (HTTP)
443    - API Gateway (HTTPS)
8001   - Agent Server (optional, manuell)
```

**Hinweis:** Port 8000 ist im docker-compose.yml für den Orchestrator reserviert, 
aber der Orchestrator hat aktuell kein HTTP-Interface. Für ein Dashboard nutze 
entweder Monitor (9090) oder starte agent_server.py auf Port 8001.

## Empfohlenes Setup

Für Production:
1. Starte Full Stack: `docker-compose up -d`
2. Lade Models: `bash download-models.sh`
3. Monitor Dashboard: http://localhost:9090
4. Logs: `docker-compose logs -f orchestrator`

Für Development:
1. Starte Services: `docker-compose up -d`
2. Starte Agent Server: `python agent_server.py` (Port 8000)
3. Chat Dashboard: http://localhost:8000
4. Monitor: http://localhost:9090

## Nächste Schritte (Optional)

- [ ] Orchestrator mit FastAPI ausstatten (HTTP API)
- [ ] Agent Server als Docker Service integrieren
- [ ] Unified Dashboard (Orchestrator + Monitor + Chat)
- [ ] WebSocket-Support für Live-Updates
